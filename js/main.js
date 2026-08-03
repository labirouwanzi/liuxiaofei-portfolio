/* ============================================================
   刘晓菲 · 个人作品展示网页 — 交互逻辑
   侧边栏导航 + 双网格文章 + 模态框
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* 图片加载失败降级:换内置占位图,避免裂图 */
  var PLACEHOLDER = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"%3E%3Crect width="800" height="500" fill="%23EFE7D8"/%3E%3Crect x="0" y="0" width="800" height="500" fill="none" stroke="%23D8CFBE" stroke-width="2"/%3E%3Ctext x="400" y="250" font-size="28" fill="%235A554D" font-family="serif" text-anchor="middle"%3E刘晓菲·作品%3C/text%3E%3C/svg%3E';
  function guardImg(img) {
    if (!img) return;
    img.addEventListener('error', function onErr() {
      img.removeEventListener('error', onErr);
      if (img.src !== PLACEHOLDER) img.src = PLACEHOLDER;
    });
  }

  /* ---------- 数据 ---------- */
  var ARTICLES = (window.ARTICLES && window.ARTICLES.articles) || [];

  /* ---------- 卡片 HTML(小红书风格) ---------- */
  function cardHTML(a) {
    var cover = a.cover || {};
    return (
      '<article class="card" tabindex="0" role="button" data-id="' + esc(a.id) + '" aria-label="查看全文:' + esc(a.title) + '">' +
        '<div class="card__cover"><img src="' + esc(cover.src || PLACEHOLDER) + '" alt="' + esc(cover.alt || a.title || '') + '" loading="lazy"></div>' +
        '<div class="card__body">' +
          '<h3 class="card__title">' + esc(a.title) + '</h3>' +
          '<div class="card__meta">' +
            '<span class="card__tag">' + esc(a.category || '文章') + '</span>' +
            '<time>' + esc(a.date || '') + '</time>' +
          '</div>' +
        '</div>' +
      '</article>'
    );
  }

  /* 按分类渲染到指定容器 */
  function renderGrid(containerId, category) {
    var el = document.getElementById(containerId);
    if (!el) return;
    var list = ARTICLES.filter(function (a) { return (a.category || '文章') === category; });
    if (!list.length) {
      el.innerHTML = '<p class="empty">内容整理中,敬请期待。</p>';
      return;
    }
    el.innerHTML = list.map(cardHTML).join('');
    Array.prototype.forEach.call(el.querySelectorAll('.card__cover img'), guardImg);
  }

  /* 文档级卡片点击 / 键盘(两个网格通用) */
  document.addEventListener('click', function (e) {
    var card = e.target.closest('.card');
    if (card) openArticle(card.getAttribute('data-id'));
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      var card = e.target.closest('.card');
      if (card) { e.preventDefault(); openArticle(card.getAttribute('data-id')); }
    }
  });

  /* ---------- 正文内容块渲染 ---------- */
  function renderBlocks(blocks) {
    return (blocks || []).map(function (b) {
      switch (b.type) {
        case 'p':
          return '<p>' + esc(b.text) + '</p>';
        case 'h2':
          return '<h3 class="body-h">' + esc(b.text) + '</h3>';
        case 'img':
          return '<figure><img src="' + esc(b.src || PLACEHOLDER) + '" alt="' + esc(b.alt || '') + '" loading="lazy">' +
                 (b.caption ? '<figcaption>' + esc(b.caption) + '</figcaption>' : '') + '</figure>';
        case 'blockquote':
          return '<blockquote>' + esc(b.text) + '</blockquote>';
        default:
          return '';
      }
    }).join('');
  }

  /* ---------- 模态框 ---------- */
  var modal = document.getElementById('articleModal');
  var modalBody = document.getElementById('modalBody');

  function openArticle(id) {
    var a = null;
    for (var i = 0; i < ARTICLES.length; i++) { if (ARTICLES[i].id === id) { a = ARTICLES[i]; break; } }
    if (!a || !modal) return;

    document.getElementById('modalTitle').textContent = a.title || '';
    document.getElementById('modalCategory').textContent = a.category || '';
    document.getElementById('modalDate').textContent = a.date || '';

    var cover = a.cover || {};
    var coverImg = document.getElementById('modalCover');
    coverImg.src = cover.src || PLACEHOLDER;
    coverImg.alt = cover.alt || a.title || '';
    guardImg(coverImg);

    modalBody.innerHTML = renderBlocks(a.content);
    Array.prototype.forEach.call(modalBody.querySelectorAll('img'), guardImg);

    var source = document.getElementById('modalSource');
    if (a.source && a.source.url) {
      source.href = a.source.url;
      source.style.display = 'inline-flex';
    } else {
      source.style.display = 'none';
    }

    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    modal.querySelector('.modal__panel').scrollTop = 0;
    var closeBtn = modal.querySelector('.modal__close');
    if (closeBtn) closeBtn.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.style.overflow = '';
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.getAttribute && t.getAttribute('data-close') != null) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if (modal && !modal.hidden) closeModal();
      else if (bcard && !bcard.hidden) closeCard();
    }
  });

  /* ---------- 联系我 · 名片 ---------- */
  var bcard = document.getElementById('bcard');
  var contactBtn = document.getElementById('contactBtn');
  function openCard() {
    if (!bcard) return;
    bcard.hidden = false;
    document.body.style.overflow = 'hidden';
    var c = bcard.querySelector('.bcard__close');
    if (c) c.focus();
  }
  function closeCard() {
    if (!bcard) return;
    bcard.hidden = true;
    document.body.style.overflow = '';
  }
  if (contactBtn) contactBtn.addEventListener('click', openCard);
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.getAttribute && t.getAttribute('data-close-card') != null) closeCard();
  });

  /* ---------- 板块转场入场 ---------- */
  var sections = document.querySelectorAll('.section');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    sections.forEach(function (s) { io.observe(s); });
    if (sections[0]) sections[0].classList.add('in');
  } else {
    sections.forEach(function (s) { s.classList.add('in'); });
  }

  /* ---------- 侧边栏导航高亮当前板块 ---------- */
  var navLinks = document.querySelectorAll('.sidebar__nav a');
  var ids = ['intro', 'videos', 'daily', 'pingyao'];
  function onScroll() {
    var y = window.scrollY + 130;
    var current = 'intro';
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.offsetTop <= y) current = id;
    });
    navLinks.forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- 年份 ---------- */
  var y = new Date().getFullYear();
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = y;
  var yearFoot = document.getElementById('yearFoot');
  if (yearFoot) yearFoot.textContent = y;

  /* ---------- 启动 ---------- */
  renderGrid('dailyGrid', '日常稿件');
  renderGrid('pingyaoGrid', '平遥电影节专题');
})();
