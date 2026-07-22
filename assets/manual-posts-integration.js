(() => {
  const DATA_URL = 'manual_posts.json';

  const normalizeName = (value) => String(value || '').replace(/[\s　]/g, '').replace('ドラスタ', 'ドラスタ');
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
        padding: 16px;
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(31,39,52,.98), rgba(17,22,31,.98));
        scroll-snap-align: start;
      }
      .manual-post-card .manual-post-badge {
        display: inline-flex;
        margin-bottom: 10px;
        padding: 4px 9px;
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
      }
      .manual-post-card .manual-post-title { font-size: 16px; font-weight: 800; }
      .manual-post-card .manual-post-meta { margin-top: 7px; color: #aab3c0; font-size: 12px; line-height: 1.55; }
      .manual-post-card .manual-post-note { margin-top: 14px; color: #d8dee8; font-size: 13px; line-height: 1.65; }
      .manual-post-card .manual-post-actions { margin-top: 16px; }
      .manual-post-card .manual-post-actions a {
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

  const findStoreGroup = (storeName) => {
    const target = normalizeName(storeName);
    return [...document.querySelectorAll('.store-group')].find(group => {
      const name = group.querySelector('.store-group-name')?.textContent || '';
      return normalizeName(name) === target;
    });
  };

  const makeCard = (item) => {
    const article = document.createElement('article');
    article.className = 'manual-post-card store-post-card';
    article.dataset.status = item.statusId || '';
    article.dataset.store = item.store || '';
    article.dataset.types = typeMap[item.category] || 'x_post_other';
    article.dataset.manualPost = 'true';

    const date = item.registeredAt
      ? new Date(item.registeredAt).toLocaleString('ja-JP')
      : '日時不明';

    const badge = document.createElement('div');
    badge.className = 'manual-post-badge';
    badge.textContent = `手動登録・${item.category || '未分類'}`;

    const title = document.createElement('div');
    title.className = 'manual-post-title';
    title.textContent = item.store || '店舗未設定';

    const meta = document.createElement('div');
    meta.className = 'manual-post-meta';
    meta.textContent = `@${item.account || 'unknown'} / 登録 ${date}`;

    const note = document.createElement('div');
    note.className = 'manual-post-note';
    note.textContent = '手動で登録した最新投稿です。画像と買取表の内容はXで確認してください。';

    const actions = document.createElement('div');
    actions.className = 'manual-post-actions';
    const link = document.createElement('a');
    link.href = item.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Xで投稿を開く';
    actions.appendChild(link);

    article.append(badge, title, meta, note, actions);
    return article;
  };

  const integrate = async () => {
    if (!document.getElementById('storeGroupList')) return;
    ensureStyles();

    try {
      const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) return;
      const items = await response.json();

      items
        .slice()
        .sort((a, b) => String(b.registeredAt || '').localeCompare(String(a.registeredAt || '')))
        .forEach(item => {
          if (!item?.statusId || document.querySelector(`[data-manual-post="true"][data-status="${CSS.escape(String(item.statusId))}"]`)) return;
          const group = findStoreGroup(item.store);
          const rail = group?.querySelector('.store-post-carousel');
          if (!rail) return;
          rail.prepend(makeCard(item));
          group.dataset.types = `${group.dataset.types || ''} ${typeMap[item.category] || 'x_post_other'}`.trim();
        });
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
