(function () {
  var dialog = document.querySelector('.portrait-viewer');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  var image = dialog.querySelector('.portrait-viewer__image');
  var title = dialog.querySelector('#portrait-viewer-title');
  var close = dialog.querySelector('.portrait-viewer__close');
  var nav = dialog.querySelector('.portrait-viewer__nav');
  var previous = dialog.querySelector('.portrait-viewer__previous');
  var next = dialog.querySelector('.portrait-viewer__next');
  var count = dialog.querySelector('.portrait-viewer__count');
  var portraits = Array.from(document.querySelectorAll('.character__link'));
  var opener;
  var index = -1;

  function show(link) {
    title.textContent = link.dataset.label;
    image.alt = link.querySelector('img').alt;
    image.src = link.href;
    nav.hidden = index < 0;
    count.textContent = index < 0 ? '' : (index + 1) + ' / ' + portraits.length;
  }

  function move(step) {
    if (index < 0 || !portraits.length) return;
    index = (index + step + portraits.length) % portraits.length;
    show(portraits[index]);
  }

  document.querySelectorAll('[data-image-viewer]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      opener = link;
      index = portraits.indexOf(link);
      show(link);
      dialog.showModal();
      close.focus();
    });
  });
  previous.addEventListener('click', function () { move(-1); });
  next.addEventListener('click', function () { move(1); });
  dialog.addEventListener('keydown', function (event) {
    if (index < 0) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      move(event.key === 'ArrowLeft' ? -1 : 1);
    }
  });
  close.addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('click', function (event) {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', function () {
    image.removeAttribute('src');
    if (opener) opener.focus();
  });
}());
