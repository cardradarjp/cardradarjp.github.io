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
      .manual-post-card .twitter-tweet,
      .manual-post-card iframe {
        margin: 0 auto !important;
        max-width: 100% !important;
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
    if (window.twttr?.widgets?.createTweet) {
      resolve(window.twttr);
      return;
    }

    const finish = () => {
      if (window.twttr?.widgets?.createTweet) resolve(window.twttr);
      else reject(new Error('X widgets API unavailable'));
    };

    const existing = [...document.scripts].find(script => script.src === WIDGETS_URL);
    if (existing) {
      existing.addEventListener('load', finish, { once: true });
      existing.addEventListener('error', reject, { once: true });
      setTimeout(() => {
        if (window.twttr?.widgets?.createTweet) resolve(window.twttr);
      }, 0);
      return;
    }

    const script = document.createElement('script');
    script.src = WIDGETS_URL;
    script.async = true;
    script.charset = 'utf-8';
    script.addEventListener('load', finish, { once: true });
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

    article.append(badge, embed);
    article._manualItem = item;
    return article;
  };

  const renderEmbeds = async (cards) => {
    if (!cards.length) return;
    try {
      const twttr = await loadWidgets();
      await Promise.all(cards.map(async card => {
        const item = card._manualItem;
        const embed = card.querySelector('.manual-post-embed');
        try {
          const iframe = await twttr.widgets.createTweet(
            String(item.statusId),
            embed,
            {
              theme: 'dark',
              dnt: true,
              conversation: 'none',
              align: 'center',
              lang: 'ja'
            }
          );
          if (!iframe) embed.replaceChildren(makeFallback(item));
        } catch (error) {
          console.warn('CardRadar X embed failed.', item.statusId, error);
          embed.replaceChildren(makeFallback(item));
        }
      }));
    } catch (error) {
      console.warn('CardRadar X widgets could not be loaded.', error);
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

      await renderEmbeds(cards);
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
