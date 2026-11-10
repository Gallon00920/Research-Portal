"""Turn the standalone news updater app.js into web/news.js for the Research Panel.
Usage: py -I make_news_js.py <src app.js> <dst news.js>
"""
import pathlib
import sys

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
dst = pathlib.Path(sys.argv[2])
s = src


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:70], n)
    s = s.replace(old, new)


# data/news.json is served by backend/server.py locally and copied into site/data by build_static.py;
# the refresh button dispatches this repository's update-news.yml
rep('const GITHUB_REPO = "Gallon00920/Credit_bearing_news_updater";',
    '''/* repository that hosts this site: set by build_static.py on GitHub Pages, otherwise read from the Pages URL */
function repoFromPagesUrl() {
  const host = /^([^.]+)\\.github\\.io$/i.exec(location.hostname);
  const first = location.pathname.split("/").filter(Boolean)[0];
  return host && first ? `${host[1]}/${first}` : "";
}
const GITHUB_REPO = (window.AID_CONFIG && window.AID_CONFIG.repo) || repoFromPagesUrl();''')
rep('''async function init() {
  loadLocalState();
  bindStaticEvents();
  wireHeader();
  renderStatic();
  await loadData();
}''', '''async function init(language) {
  loadLocalState();
  state.language = language;
  bindStaticEvents();
  renderStatic();
  await loadData();
}''')
# the panel owns the header, so drop the hide-on-scroll helper
a = s.index("/* Header hides on scroll down")
b = s.index("function readStorage(")
s = s[:a] + s[b:]
rep("init();\n", "")
rep('  document.documentElement.lang = state.language === "zh" ? "zh-Hans" : "en";\n', "")
rep('  document.querySelectorAll("[data-lang-pill]").forEach((node) => node.classList.toggle("active", node.dataset.langPill === state.language));\n'
    '  $("#languageToggle").classList.toggle("right", state.language === "zh");\n', "")
rep('''  $("#languageToggle").addEventListener("click", () => {
    state.language = state.language === "zh" ? "en" : "zh";
    writeStorage(STORAGE.language, state.language);
    state.summary = state.summary ? buildSummary(computeView().shown) : null;
    renderAll();
  });
''', "")
rep('''  document.addEventListener("click", onClick);
  document.addEventListener("change", onChange);
  document.addEventListener("input", onInput);
  document.addEventListener("submit", onSubmit);''', '''  const root = document.getElementById("view-news");
  root.addEventListener("click", onClick);
  root.addEventListener("change", onChange);
  root.addEventListener("input", onInput);
  root.addEventListener("submit", onSubmit);''')

# the panel has its own data-i18n / data-icon handling: only touch nodes inside the news view
rep('document.querySelectorAll("[data-i18n]")', 'document.querySelectorAll("#view-news [data-i18n]")')
rep('document.querySelectorAll("[data-icon]")', 'document.querySelectorAll("#view-news [data-icon]")')

header = '''/* AID Credit News Radar — embedded in the AID Research Panel as the "News tracker" view.
   Generated from Credit_bearing_news_updater/src/app.js by make_news_js.py; the data is read
   from that site's published data/news.json, and the hourly pipeline keeps running there.
   Exposes window.NewsTracker = { mount(lang), setLanguage(lang) }; lang is "en" | "cn" | "zh". */
(function () {
"use strict";
'''
footer = '''
/* ---------- panel integration ---------- */
let mounted = false;
function toNewsLang(lang) {
  return lang === "zh" || lang === "cn" ? "zh" : "en";
}
window.NewsTracker = {
  mount(lang) {
    const language = toNewsLang(lang);
    if (!mounted) {
      mounted = true;
      init(language);
      return;
    }
    if (language !== state.language) this.setLanguage(language);
  },
  setLanguage(lang) {
    const language = toNewsLang(lang);
    if (language === state.language) return;
    state.language = language;
    if (!mounted) return;
    state.summary = state.summary ? buildSummary(computeView().shown) : null;
    renderAll();
  },
};
})();
'''
dst.write_text(header + s + footer, encoding="utf-8")
print("wrote", dst, len(header + s + footer), "bytes")
