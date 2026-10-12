/* 回望灯火阑珊 —— 阅读器
   进度、目录抽屉、全文检索、昼夜、字号、续读、那盏灯。
   无依赖，无追踪，偏好只存在本机。 */
(function () {
  'use strict';

  var root = document.documentElement;
  var LS = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var $ = function (s) { return document.querySelector(s); };

  /* ---------------------------------------------------------- 阅读进度 */
  var bar = $('#progress');
  if (bar) {
    var tick = false;
    var draw = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 40 ? Math.min(100, (window.scrollY / h) * 100) : 0) + '%';
      tick = false;
    };
    addEventListener('scroll', function () {
      if (!tick) { tick = true; requestAnimationFrame(draw); }
    }, { passive: true });
    addEventListener('resize', draw, { passive: true });
    draw();
  }

  /* ------------------------------------------------------------ 昼夜 */
  var btnTheme = $('#btn-theme');
  var syncTheme = function () {
    if (btnTheme) {
      var dark = root.dataset.theme === 'dark';
      btnTheme.setAttribute('aria-label', dark ? '切到白昼' : '切到夜间');
      btnTheme.setAttribute('aria-pressed', dark ? 'true' : 'false');
    }
  };
  if (btnTheme) {
    btnTheme.addEventListener('click', function () {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      LS.set('hw-theme', root.dataset.theme);
      syncTheme();
    });
    syncTheme();
  }

  /* ------------------------------------------------------------ 字号 */
  var sizes = ['s', 'm', 'l'];
  var btnSize = $('#btn-size');
  if (btnSize) {
    btnSize.addEventListener('click', function () {
      var i = sizes.indexOf(root.dataset.size || 'm');
      root.dataset.size = sizes[(i + 1) % sizes.length];
      LS.set('hw-size', root.dataset.size);
      btnSize.setAttribute('aria-label', '字号：' + root.dataset.size.toUpperCase());
    });
  }

  /* ------------------------------------------------------- 目录抽屉 */
  var drawer = $('#drawer'), scrim = $('#scrim'), btnToc = $('#btn-toc'), btnClose = $('#btn-close');
  var q = $('#q'), results = $('#results'), drawerToc = $('#drawer-toc');
  var lastFocus = null;

  function openDrawer() {
    if (!drawer) return;
    lastFocus = document.activeElement;
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    if (scrim) scrim.hidden = false;
    document.body.style.overflow = 'hidden';
    var cur = drawer.querySelector('.is-current');
    if (cur) cur.scrollIntoView({ block: 'center' });
    if (q) q.focus();
    loadIndex();
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    if (scrim) scrim.hidden = true;
    document.body.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }
  if (btnToc) btnToc.addEventListener('click', openDrawer);
  if (btnClose) btnClose.addEventListener('click', closeDrawer);
  if (scrim) scrim.addEventListener('click', closeDrawer);

  /* ------------------------------------------------------- 全文检索 */
  var idxURL = (document.querySelector('script[data-index]') || {}).dataset;
  idxURL = idxURL ? idxURL.index : '';
  var idx = null, loading = false;

  function loadIndex() {
    if (idx || loading || !idxURL) return;
    loading = true;
    fetch(idxURL).then(function (r) { return r.json(); }).then(function (d) {
      idx = d; loading = false; if (q && q.value) search(q.value);
    }).catch(function () { loading = false; });
  }

  var esc = function (s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  };

  function search(term) {
    term = term.trim();
    if (!results) return;
    if (!term) {
      results.hidden = true;
      results.innerHTML = '';
      if (drawerToc) drawerToc.hidden = false;
      return;
    }
    if (drawerToc) drawerToc.hidden = true;
    results.hidden = false;
    if (!idx) { results.innerHTML = '<p class="hit__none">正在取全文……</p>'; return; }

    var low = term.toLowerCase(), out = [], n = 0;
    for (var i = 0; i < idx.length && n < 40; i++) {
      var ch = idx[i], hay = ch.c.toLowerCase(), from = 0, per = 0;
      while (per < 3 && n < 40) {
        var at = hay.indexOf(low, from);
        if (at < 0) break;
        var s = Math.max(0, at - 24), e = Math.min(ch.c.length, at + term.length + 40);
        out.push('<a class="hit" href="' + ch.u + '">' +
          '<span class="hit__title">' + (ch.n < 10 ? '0' + ch.n : ch.n) + '　' + esc(ch.t) + '</span>' +
          '<span class="hit__snip">' + (s > 0 ? '…' : '') + esc(ch.c.slice(s, at)) +
          '<mark>' + esc(ch.c.slice(at, at + term.length)) + '</mark>' +
          esc(ch.c.slice(at + term.length, e)) + (e < ch.c.length ? '…' : '') + '</span></a>');
        from = at + term.length; per++; n++;
      }
    }
    results.innerHTML = out.length
      ? out.join('')
      : '<p class="hit__none">全书里没有「' + esc(term) + '」。</p>';
  }

  if (q) {
    var timer;
    q.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { search(q.value); }, 130);
    });
  }

  /* ------------------------------------------- 续读：记住读到哪一章 */
  var article = $('.chapter[data-chapter]');
  var KEY = 'hw-mark';

  if (article) {
    var title = article.querySelector('.chapter__title');
    var mark = {
      u: location.pathname,
      t: title ? title.textContent.trim() : document.title,
      y: 0
    };
    var save = function () {
      mark.y = Math.round(window.scrollY);
      LS.set(KEY, JSON.stringify(mark));
    };
    var st;
    addEventListener('scroll', function () {
      clearTimeout(st);
      st = setTimeout(save, 400);
    }, { passive: true });
    addEventListener('pagehide', save);
    save();

    // 只有明确点了「继续读」才跳回原位，不做意外滚动
    if (location.hash === '#resume') {
      try {
        var old = JSON.parse(LS.get(KEY) || '{}');
        if (old.u === location.pathname && old.y > 200) {
          history.replaceState(null, '', location.pathname);
          addEventListener('load', function () { window.scrollTo(0, old.y); });
        }
      } catch (e) {}
    }
  }

  var resume = $('#btn-resume');
  if (resume) {
    try {
      var m = JSON.parse(LS.get(KEY) || 'null');
      if (m && m.u && m.t) {
        resume.href = m.u + '#resume';
        var slot = resume.querySelector('[data-resume-title]');
        if (slot) slot.textContent = '《' + m.t + '》';
        resume.hidden = false;
      }
    } catch (e) {}
  }

  /* ------------------------------------------------------ 那盏灯：音乐 */
  var bulb = $('#btn-bgm'), audio = $('#bgm');
  if (bulb && audio) {
    audio.volume = 0.28;
    bulb.addEventListener('click', function () {
      if (audio.paused) {
        audio.play().then(function () {
          bulb.classList.add('is-on');
        }).catch(function () {});
      } else {
        audio.pause();
        bulb.classList.remove('is-on');
      }
    });
    audio.addEventListener('pause', function () { bulb.classList.remove('is-on'); });
  }

  /* ------------------------------------------------------ 本章朗读 */
  var narration = $('#chapter-narration');
  if (narration) {
    var panel = $('#listen'), status = $('#narration-status');
    var version = $('#narration-version'), speed = $('#narration-speed');
    var listenKey = 'hw-audio:' + location.pathname;
    var saved = {}, restoreAt = 0;
    try { saved = JSON.parse(LS.get(listenKey) || '{}') || {}; } catch (e) {}
    if (saved.revision === panel.dataset.revision) {
      restoreAt = Number(saved.time) || 0;
      if (saved.version === 'voice') version.selectedIndex = 1;
      narration.src = version.value;
      if (restoreAt > 0) status.textContent = '已记住上次进度，点播放继续收听。';
    }
    var preferredSpeed = LS.get('hw-audio-speed');
    if (Array.from(speed.options).some(function (o) { return o.value === preferredSpeed; })) speed.value = preferredSpeed;
    narration.playbackRate = Number(speed.value);
    narration.addEventListener('loadedmetadata', function () {
      if (restoreAt > 0 && isFinite(narration.duration)) narration.currentTime = Math.min(restoreAt, Math.max(0, narration.duration - .1));
      restoreAt = 0;
      narration.playbackRate = Number(speed.value);
    });
    function rememberAudio() {
      if (restoreAt > 0 || !isFinite(narration.duration)) return;
      LS.set(listenKey, JSON.stringify({ revision: panel.dataset.revision, time: narration.ended ? 0 : narration.currentTime, version: version.selectedIndex ? 'voice' : 'mixed' }));
    }
    var lastRemember = 0;
    narration.addEventListener('timeupdate', function () {
      if (Date.now() - lastRemember > 3000) { rememberAudio(); lastRemember = Date.now(); }
    });
    narration.addEventListener('pause', rememberAudio);
    addEventListener('pagehide', rememberAudio);
    narration.addEventListener('play', function () {
      if (audio) audio.pause();
      status.textContent = '正在收听 · guige 讲述';
    });
    if (audio) audio.addEventListener('play', function () { narration.pause(); });
    narration.addEventListener('ended', function () { rememberAudio(); status.textContent = '本章已听完。'; });
    narration.addEventListener('error', function () { status.textContent = '音频暂时无法加载，请稍后重新播放。'; });
    panel.querySelectorAll('[data-seek]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (isFinite(narration.duration)) narration.currentTime = Math.max(0, Math.min(narration.duration, narration.currentTime + Number(button.dataset.seek)));
      });
    });
    speed.addEventListener('change', function () { narration.playbackRate = Number(speed.value); LS.set('hw-audio-speed', speed.value); });
    version.addEventListener('change', function () {
      var wasPlaying = !narration.paused;
      restoreAt = restoreAt || narration.currentTime;
      narration.src = version.value;
      narration.load();
      if (wasPlaying) narration.play().catch(function () { status.textContent = '点播放继续收听。'; });
    });
  }

  /* -------------------------------------------------------- 键盘 */
  addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target.tagName;
    var typing = t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT' || t === 'BUTTON' || t === 'AUDIO' || e.target.isContentEditable;

    if (e.key === 'Escape') {
      if (drawer && drawer.classList.contains('is-open')) { closeDrawer(); }
      return;
    }
    if (typing) return;

    if (e.key === 'ArrowLeft') {
      var p = document.querySelector('a[rel="prev"]');
      if (p) location.href = p.href;
    } else if (e.key === 'ArrowRight') {
      var nx = document.querySelector('a[rel="next"]');
      if (nx) location.href = nx.href;
    } else if (e.key === '/' ) {
      e.preventDefault();
      openDrawer();
    }
  });
})();
