/* Collapse the nav links behind a hamburger, but only when they would not fit
   on one line. The threshold is measured from the links themselves rather than
   written as a fixed breakpoint, so adding or renaming an item moves it
   automatically. With JavaScript off nothing collapses and the links wrap as
   they did before, so no page becomes unreachable. */
(function () {
  var bar = document.querySelector('.nav-in');
  if (!bar) return;
  var nav = bar.querySelector('nav');
  var links = bar.querySelector('.nlinks');
  var burger = bar.querySelector('.burger');
  if (!nav || !links || !burger) return;

  var GAP = 22;      // gap between links, plus a little slack
  var RESERVE = 90;  // room for the burger and the gaps around the controls
  var need = 0;

  function close() {
    bar.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
  }

  function fit() {
    var room = bar.clientWidth - bar.querySelector('.brand').offsetWidth - RESERVE;
    [].forEach.call(nav.querySelectorAll('.searchbtn, .toggle'), function (b) {
      room -= b.offsetWidth;
    });
    var collapse = need > room;
    bar.classList.toggle('is-collapsed', collapse);
    if (!collapse) close();
  }

  function measure() {
    bar.classList.remove('is-collapsed', 'is-open');
    need = 0;
    [].forEach.call(links.children, function (a) { need += a.offsetWidth + GAP; });
    fit();
  }

  burger.addEventListener('click', function () {
    var open = !bar.classList.contains('is-open');
    bar.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var a = links.querySelector('a'); if (a) a.focus(); }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && bar.classList.contains('is-open')) { close(); burger.focus(); }
  });

  document.addEventListener('click', function (e) {
    if (bar.classList.contains('is-open') && !nav.contains(e.target)) close();
  });

  window.addEventListener('resize', fit);
  // webfonts change the link widths, so measure again once they have loaded
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  measure();
})();
