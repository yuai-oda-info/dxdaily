#!/usr/bin/env python3
"""MediKoto：ヘッドラインの図解（figure.v6fig）を整える（2026-11-11追加）。

1) 「数字で見る」（ul.v6nums）の数字が隣の列にはみ出して重なるのを防ぐ。
   数字の大きさを画面幅（vw）ではなく図解の欄の幅（cqi）で決め、欄が狭いとき（460px以下）は
   「数字｜説明」の縦並びに切り替える。それでも入らないときは同じ図解の数字をそろえて小さくする（JS）。
2) 図解の出典行「数字は出典（○○）の記載どおり。」の ○○ を、その記事の出典URLへのリンクにする。

何度かけても同じ結果（目印 mk-v6fig-fix があれば CSS/JS は足さない。リンク済みの行は触らない）。
使い方: python3 tools/medikoto_v6fig.py [フォルダ]   ／ fix_sitenav.py から run(root) で呼ばれる。
"""
import glob
import os
import re
import sys

MARK = 'mk-v6fig-fix'
CSS = ('<style id="%s">'
       'figure.v6fig{container-type:inline-size}'
       'figure.v6fig .v6nums .n{font-size:clamp(1.5rem,calc(11cqi - 12px),3rem);white-space:nowrap}'
       'figure.v6fig .v6nums .n small{white-space:nowrap}'
       'figure.v6fig .src a{color:inherit;text-decoration:underline;text-underline-offset:2px}'
       'figure.v6fig .src a:hover{color:var(--ink)}'
       # 欄が狭いとき（PCの2段組みの中・スマホ）は「数字｜説明」の縦並びにする
       '@container (max-width:460px){'
       'figure.v6fig .v6nums{grid-template-columns:minmax(0,1fr)}'
       'figure.v6fig .v6nums li{display:grid;grid-template-columns:8.8rem minmax(0,1fr);align-items:baseline;gap:.9rem;padding:.5rem 0!important;border-left:0!important}'
       'figure.v6fig .v6nums li+li{border-top:1px solid var(--rule)}'
       'figure.v6fig .v6nums .n{font-size:2rem}'
       'figure.v6fig .v6nums .n small{display:inline;margin:0 0 0 .2rem;font-size:.72rem}'
       'figure.v6fig .v6nums .l{margin:0}}'
       '</style>\n') % MARK
JS = ('<script id="%s-js">(function(){function fit(){var us=document.querySelectorAll(".v6nums");'
      'for(var j=0;j<us.length;j++){var ns=us[j].querySelectorAll(".n"),i,k=0,over;'
      'for(i=0;i<ns.length;i++)ns[i].style.fontSize="";'
      'do{over=false;for(i=0;i<ns.length;i++)if(ns[i].scrollWidth>ns[i].clientWidth+1)over=true;'
      'if(over){var s=parseFloat(getComputedStyle(ns[0]).fontSize)-1.5;if(s<14)break;'
      'for(i=0;i<ns.length;i++)ns[i].style.fontSize=s+"px";}k++;}while(over&&k<30);}}'
      'if(document.readyState!=="loading")fit();else document.addEventListener("DOMContentLoaded",fit);'
      'window.addEventListener("load",fit);var t;window.addEventListener("resize",function(){clearTimeout(t);t=setTimeout(fit,150);});'
      'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);})();</script>\n') % MARK

FIG = re.compile(r'<figure class="v6fig".*?</figure>', re.S)
SRC = re.compile(r'(<p class="src">[^<（]*出典（)([^<（）]+)(）)')
HREF = re.compile(r'<a href="(https?://[^"]+)"[^>]*target="_blank"')


def patch(h):
    """戻り値：(新しいHTML, 足したリンク数, CSS/JSを足したか)"""
    if 'class="v6fig"' not in h and 'v6nums' not in h:
        return h, 0, False
    out, pos, nlink = [], 0, 0
    for m in FIG.finditer(h):
        fig = m.group(0)
        # この図解の直前にある記事見出しのリンク（同じ記事の出典URL）
        li = max(h.rfind('<li', 0, m.start()), h.rfind('<article', 0, m.start()), h.rfind('<div class="first', 0, m.start()))
        urls = HREF.findall(h[li if li >= 0 else max(0, m.start() - 3000):m.start()])
        if urls and SRC.search(fig):
            u = urls[-1]
            fig = SRC.sub(lambda s: '%s<a href="%s" target="_blank" rel="noopener">%s</a>%s' % (s.group(1), u, s.group(2), s.group(3)), fig, count=1)
            nlink += 1
        out.append(h[pos:m.start()])
        out.append(fig)
        pos = m.end()
    out.append(h[pos:])
    h2 = ''.join(out)
    added = False
    if MARK not in h2 and '</body>' in h2:
        i = h2.rfind('</body>')   # 紙面のCSSは本文側にあるので、その後ろ（</body>の直前）に置いて確実に効かせる
        h2 = h2[:i] + CSS + JS + h2[i:]
        added = True
    return h2, nlink, added


def run(root='.'):
    msgs, nf, nl = [], 0, 0
    for f in sorted(glob.glob(os.path.join(root, 'news*.html'))):
        try:
            h = open(f, encoding='utf-8').read()
        except OSError:
            continue
        h2, k, added = patch(h)
        if h2 != h:
            open(f, 'w', encoding='utf-8').write(h2)
            nf += 1
            nl += k
    msgs.append('OK: 図解: %d ファイルを整えた（数字の重なり防止・出典リンク %d 件）' % (nf, nl) if nf
                else 'OK: 図解: 直すところなし（数字の重なり防止・出典リンクは反映済み）')
    return msgs


if __name__ == '__main__':
    for t in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(t)
