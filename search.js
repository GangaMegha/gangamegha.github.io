/* Self-contained site search. No dependencies. Index lives in search-data.js. */
(function () {
  var overlay, input, countEl, listEl, docs = [];

  function esc(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}

  // edit distance, capped (cheap early exit)
  function dist(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i; var best = cur[0];
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i-1] === b[j-1] ? 0 : 1));
        if (cur[j] < best) best = cur[j];
      }
      if (best > max) return max + 1;
      prev = cur.slice();
    }
    return prev[b.length];
  }

  // Best match of one term inside one field. Returns {score, ranges}.
  function matchField(term, text) {
    var low = text.toLowerCase(), ranges = [], score = 0, idx = 0, k;
    // direct substring occurrences
    while ((k = low.indexOf(term, idx)) !== -1) {
      var atWordStart = k === 0 || /[^a-z0-9]/.test(low[k - 1]);
      var wholeWord = atWordStart && (k + term.length === low.length || /[^a-z0-9]/.test(low[k + term.length]));
      // Short terms only count at a word boundary: otherwise an acronym like
      // "RAG" matches the middle of "coverage" and buries the real hits.
      if (term.length < 4 && !atWordStart) { idx = k + term.length; continue; }
      score = Math.max(score, wholeWord ? 10 : atWordStart ? 7 : 4);
      ranges.push([k, k + term.length - 1]);
      idx = k + term.length;
      if (ranges.length > 24) break;
    }
    if (score) return { score: score, ranges: ranges };
    // fuzzy: compare against each word, tolerate typos on longer terms
    if (term.length >= 4) {
      var tol = term.length >= 7 ? 2 : 1, re = /[a-z0-9]+/g, m;
      while ((m = re.exec(low))) {
        if (Math.abs(m[0].length - term.length) > tol) continue;
        if (dist(term, m[0], tol) <= tol) {
          return { score: 3, ranges: [[m.index, m.index + m[0].length - 1]] };
        }
      }
    }
    return null;
  }

  function search(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(function (t) { return t.length > 1; });
    if (!terms.length) return [];
    var out = [];
    docs.forEach(function (d) {
      var total = 0, tHits = [], bHits = [], ok = true;
      terms.forEach(function (t) {
        if (!ok) return;
        var inT = matchField(t, d.title), inS = matchField(t, d.section), inB = matchField(t, d.body);
        if (!inT && !inS && !inB) { ok = false; return; }
        total += (inT ? inT.score * 6 : 0) + (inS ? inS.score * 2 : 0) + (inB ? inB.score * 3 : 0);
        if (inT) tHits = tHits.concat(inT.ranges);
        if (inB) bHits = bHits.concat(inB.ranges);
      });
      if (ok) out.push({ doc: d, score: total, t: tHits, b: bHits });
    });
    return out.sort(function (a, b) { return b.score - a.score; }).slice(0, 25);
  }

  function mark(text, ranges, from, to) {
    ranges = (ranges || []).slice().sort(function (a, b) { return a[0] - b[0]; });
    var out = '', cur = from;
    ranges.forEach(function (r) {
      if (r[0] < cur || r[0] < from || r[1] >= to) return;
      out += esc(text.slice(cur, r[0])) + '<mark>' + esc(text.slice(r[0], r[1] + 1)) + '</mark>';
      cur = r[1] + 1;
    });
    return out + esc(text.slice(cur, to));
  }

  function snippet(text, ranges) {
    var LIMIT = 230;
    var first = ranges && ranges.length ? Math.min.apply(null, ranges.map(function (r) { return r[0]; })) : 0;
    var start = Math.max(0, first - 70);
    if (start > 0) { var sp = text.indexOf(' ', start); if (sp > -1 && sp < start + 25) start = sp + 1; }
    var end = Math.min(text.length, start + LIMIT);
    return (start > 0 ? '…' : '') + mark(text, ranges, start, end) + (end < text.length ? '…' : '');
  }

  function render(results, q) {
    if (!q) { countEl.textContent = ''; listEl.innerHTML = ''; return; }
    countEl.textContent = results.length + (results.length === 1 ? ' result found' : ' results found');
    listEl.innerHTML = results.map(function (r) {
      return '<article class="sr">' +
        '<a class="sr-t" href="' + r.doc.url + '">' + mark(r.doc.title, r.t, 0, r.doc.title.length) + '</a>' +
        '<div class="sr-s">' + esc(r.doc.section) + '</div>' +
        '<p class="sr-b">' + snippet(r.doc.body, r.b) + '</p></article>';
    }).join('') || '<p class="sr-none">Nothing matched. Try a different word.</p>';
  }

  function run() { var q = input.value.trim(); render(q ? search(q) : [], q); }
  function open() { overlay.hidden = false; document.body.style.overflow = 'hidden'; input.focus(); input.select(); run(); }
  function close() { overlay.hidden = true; document.body.style.overflow = ''; }

  document.addEventListener('DOMContentLoaded', function () {
    overlay = document.getElementById('searchOverlay');
    if (!overlay) return;
    docs = window.SEARCH_DATA || [];
    input = document.getElementById('searchInput');
    countEl = document.getElementById('searchCount');
    listEl = document.getElementById('searchResults');
    var btn = document.getElementById('searchBtn');
    if (btn) btn.addEventListener('click', open);
    document.getElementById('searchClose').addEventListener('click', close);
    document.getElementById('searchClear').addEventListener('click', function () { input.value = ''; run(); input.focus(); });
    input.addEventListener('input', run);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !overlay.hidden) close();
      if ((e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key === 'k')) && overlay.hidden) {
        var t = e.target.tagName;
        if (t !== 'INPUT' && t !== 'TEXTAREA') { e.preventDefault(); open(); }
      }
    });
  });
})();
