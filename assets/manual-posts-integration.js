(() => {
  const DATA_URL = 'manual_posts.json';
  const WIDGETS_URL = 'https://platform.twitter.com/widgets.js';

  const normalizeName = (value) => String(value || '').replace(/[\s　]/g, '');
  const typeMap = {
    'シングル': 'x_post_single',
    'BOX': 'x_post_box',
    '定額': 'x_post_fixed',
    'PSA・鑑定品': 'x_post_psa',
    '未分類': 'x_post_other'
  };

  const ensureStyles = () => {
    if (document.getElementById('manual-posts-integration-style')) return;
    const style = document.createElement('style');
    style.id = 'manual-posts-integration-style';
    style.textContent = `
      .manual-post-card {
        min-width: min(86vw, 430px);
        height: auto !important;
        min-height: 0 !important;
        align-self: flex-start;
        padding: 12px;
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(31,39,52,.98), rgba(17,22,31,.98));
        scroll-snap-align: start;
      }
      .manual-post-card .manual-post-badge {
        display: inline-flex;
        margin: 2px 2px 10px;
        padding: 4px 9px;
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
      }
      .manual-post-card .manual-post-embed {
        width: 100%;
        min-height: 120px;
      }
      .manual-post-card .twitter-tweet {
        margin: 0 auto !important;
      }
      .manual-post-card .manual-post-fallback {
        display: grid;
        gap: 10px;
        padding: 14px;
        color: #d8dee8;
        font-size: 13px;
        line-height: 1.65;
      }
      .manual-post-card .manual-post-fallback a {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 46px;
        border-radius: 12px;
        background: #eef3fa;
        color: #10141c;
        text-decoration: none;
        font-weight: 800;
      }
    `;
    document.head.appendChild(style);
  };

  const loadWidgets = () => new Promise((resolve, reject) => {
    if (window.twttr?.widgets) {
      resolve(window.twttr);
      return;
    }

    const existing = document.querySelector(`script[src="${WIDGETS_URL}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.twttr), { once: true });
      existing.addEventListener('error', reject, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = WIDGETS_URL;
    script.async = true;
    script.charset = 'utf-8';
    script.addEventListener('load', () => resolve(window.twttr), { once: true });
    script.addEventListener('error', reject, { once: true });
    document.head.appendChild(script);
  });

  const findStoreGroup = (storeName) => {
    const target = normalizeName(storeName);
    return [...document.querySelectorAll('.store-group')].find(group => {
      const name = group.querySelector('.store-group-name')?.textContent || '';
      return normalizeName(name) === target;
    });
  };

  const makeFallback = (item) => {
    const fallback = document.createElement('div');
    fallback.className = 'manual-post-fallback';
    fallback.innerHTML = '<div>埋め込みを読み込めませんでした。Xで投稿を確認してください。</div>';
    const link = document.createElement('a');
    link.href = item.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Xで投稿を開く';
    fallback.appendChild(link);
    return fallback;
  };

  const makeCard = (item) => {
    const article = document.createElement('article');
    article.className = 'manual-post-card store-post-card';
    article.dataset.status = item.statusId || '';
    article.dataset.store = item.store || '';
    article.dataset.types = typeMap[item.category] || 'x_post_other';
    article.dataset.manualPost = 'true';

    const badge = document.createElement('div');
    badge.className = 'manual-post-badge';
    badge.textContent = `手動登録・${item.category || '未分類'}`;

    const embed = document.createElement('div');
    embed.className = 'manual-post-embed';
    const quote = document.createElement('blockquote');
    quote.className = 'twitter-tweet';
    quote.dataset.theme = 'dark';
    quote.dataset.dnt = 'true';
    quote.dataset.conversation = 'none';
    const link = document.createElement('a');
    link.href = item.url;
    link.textContent = 'Xの投稿を表示';
    quote.appendChild(link);
    embed.appendChild(quote);

    article.append(badge, embed);
    article._manualItem = item;
    return article;
  };

  const renderEmbeds = async (cards) => {
    if (!cards.length) return;
    try {
      const twttr = await loadWidgets();
      await Promise.all(cards.map(async card => {
        try {
          await twttr.widgets.load(card);
          if (!card.querySelector('iframe')) {
            const embed = card.querySelector('.manual-post-embed');
            embed.replaceChildren(makeFallback(card._manualItem));
          }
        } catch {
          const embed = card.querySelector('.manual-post-embed');
          embed.replaceChildren(makeFallback(card._manualItem));
        }
      }));
    } catch {
      cards.forEach(card => {
        const embed = card.querySelector('.manual-post-embed');
        embed.replaceChildren(makeFallback(card._manualItem));
      });
    }
  };

  const integrate = async () => {
    if (!document.getElementById('storeGroupList')) return;
    ensureStyles();

    try {
      const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) return;
      const items = await response.json();
      const cards = [];

      items
        .slice()
        .sort((a, b) => String(b.registeredAt || '').localeCompare(String(a.registeredAt || '')))
        .forEach(item => {
          if (!item?.statusId || document.querySelector(`[data-manual-post="true"][data-status="${CSS.escape(String(item.statusId))}"]`)) return;
          const group = findStoreGroup(item.store);
          const rail = group?.querySelector('.store-post-carousel');
          if (!rail) return;
          const card = makeCard(item);
          rail.prepend(card);
          cards.push(card);
          group.dataset.types = `${group.dataset.types || ''} ${typeMap[item.category] || 'x_post_other'}`.trim();
        });

      renderEmbeds(cards);
    } catch (error) {
      console.warn('CardRadar manual posts could not be loaded.', error);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', integrate, { once: true });
  } else {
    integrate();
  }
})();
