#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ロゴを「医療・介護の現場のためのデジタル新聞」の左横へ移し、共通ナビの上の1行にする（2026-10-19）。

並び：ロゴ＋「医療・介護の現場のためのデジタル新聞」｜作成日時 → 共通ナビ → 題字（MediKoto ○○）。

毎朝のGitHub公開では、各ページをアーティファクト（本番アカウント）のHTMLで丸ごと上書きする。
アーティファクト側の MediKoto unity v1 の mast() は旧い並び（ナビ→デジタル新聞の行→題字）のままのことがあるため、
fix_sitenav.py から毎回これを呼んで並びをそろえる。
  ・mast() に数行を足し、CSS を1ブロック足すだけ。何度実行しても同じ結果になる。
  ・2026-10-19 に手で直した版（mast() の中で「デジタル新聞」の行を作る形。目印「ロゴは「デジタル新聞」の左へ」）はそのまま。
単独でも実行できる： python3 tools/medikoto_logo_row.py .
"""
import os, sys, glob

MARK = 'MediKoto logo-row v1'
DONE_BY_HAND = 'ロゴは「デジタル新聞」の左へ'     # 2026-10-19 に mast() を直接直した版の目印
JS_ANCHOR = "hd.classList.add('uv-hd');"
JS_ADD = (" /* " + MARK + "：ロゴを「デジタル新聞」の左へ・共通ナビの上の行へ */"
          " var tp=M.querySelector('.uv-top'),lo=lw||lg;if(tp){tp.classList.add('uv-top-out');hd.insertBefore(tp,hd.firstChild);"
          "if(lo){var s0=tp.firstElementChild,g=document.createElement('span');g.className='uv-tl';tp.insertBefore(g,s0);g.appendChild(lo);g.appendChild(s0);}}")
CSS = ('<style>/* ' + MARK + '（2026-10-19） */\n'
       '.uv-hd>.uv-top-out{flex:1 1 100%!important;border-bottom:0!important;align-items:center;padding:.35rem 0 0!important;margin:0!important}\n'
       '.uv-top-out .uv-tl{display:flex;align-items:center;gap:.9rem;text-align:left!important;min-width:0}\n'
       '.uv-top-out .uv-tl>.uv-logo{flex:none}\n'
       '.uv-top-out>span:last-child{flex:none}\n'
       '@media (max-width:640px){.uv-hd>.uv-top-out{flex-wrap:wrap;row-gap:.15rem}.uv-top-out .uv-tl{gap:.55rem}'
       '.uv-top-out .uv-tl>span{white-space:nowrap}.uv-top-out>span:last-child{flex:1 1 auto;text-align:right}'
       '.uv-top-out .uv-logo img,.uv-top-out img.uv-logo{height:24px!important}}\n'
       '</style>\n')


def fix(h):
    if 'function mast()' not in h or MARK in h or DONE_BY_HAND in h:
        return h
    if h.count(JS_ANCHOR) != 1 or '</body>' not in h:
        return h
    h = h.replace(JS_ANCHOR, JS_ANCHOR + JS_ADD, 1)
    i = h.rfind('</body>')
    return h[:i] + CSS + h[i:]


def run(root='.'):
    n = 0
    for p in sorted(glob.glob(os.path.join(root, '*.html'))):
        t = open(p, encoding='utf-8').read()
        t2 = fix(t)
        if t2 != t:
            open(p, 'w', encoding='utf-8').write(t2)
            n += 1
    return ['OK: ヘッダー：ロゴを「デジタル新聞」の左・共通ナビの上へ（今回 %d ページを直した）' % n]


if __name__ == '__main__':
    for m in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(m)
