#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：GitHub Pages 公開ファイルの共通ナビ（nav.sitenav）を現行版にそろえる。

・バックナンバー（日付つき）を含む全HTMLのナビを「10項目・日付なしリンク」に統一する。
・ナビが無い古いページには、ロゴ直下と免責文の直上に挿入する。
・共通ナビのCSS（--sn-se の色定義、スマホの等幅グリッド）を追記して上書きする。
・ナビ以外（本文・相互リンク・バックナンバー表）には一切触らない。

使い方:  python3 tools/fix_sitenav.py .        # リポジトリ直下で実行
        python3 tools/fix_sitenav.py . --check # 書き換えずに要修正ファイルを一覧表示
"""
import os, re, sys, glob

MARK = 'MediKoto sitenav v4'

# 共通ナビ 10項目（キー, 表示名, 色変数, リンク先＝日付なしの固定入口）
NAV = [
    ('portal',  'ポータル',      'sn-portal', './'),
    ('news',    'ニュース',      'sn-news',   'news.html'),
    ('study',   '10分勉強会',    'sn-study',  'study.html'),
    ('gov',     '国の医療DX',    'sn-gov',    'gov.html'),
    ('nursing', '看護',          'sn-nurs',   'nursing.html'),
    ('doctors', '医師',          'sn-doc',    'doctors.html'),
    ('pharm',   '薬剤師',        'sn-pharm',  'pharmacists.html'),
    ('connect', '相談支援・連携', 'sn-conn',   'connect.html'),
    ('se',      '病院SE',        'sn-se',     'hospitalit.html'),
    ('reim',    '診療報酬',      'sn-reim',   'reimbursement.html'),
]

CSS = """<style>/* %s */
.sitenav{--sn-portal:#163672;--sn-news:#163672;--sn-study:#C56A15;--sn-nurs:#C25573;--sn-doc:#285F9D;--sn-pharm:#2F8F6B;--sn-conn:#7A5230;--sn-se:#8E7414;--sn-reim:#5B3FA6;--sn-gov:#0FA9BC;--sn-bg:#F2F3EF;--sn-line:#D9DDE0;
  display:flex;flex-wrap:wrap;gap:.4rem;border:1px solid var(--sn-line);border-radius:12px;padding:.45rem;margin:.6rem 0 0;font-family:"Zen Kaku Gothic New","BIZ UDPGothic","BIZ UDPゴシック",sans-serif;}
.sitenav a{flex:1 1 auto;text-align:center;font-size:.86rem;font-weight:700;text-decoration:none;border:1px solid var(--sn-line);border-radius:8px;padding:.42rem .6rem;background:var(--sn-bg);color:var(--sn-c);white-space:nowrap;line-height:1.5;}
.sitenav a:hover{border-color:var(--sn-c);}
.sitenav a.cur{background:var(--sn-c);color:#fff;border-color:var(--sn-c);}
.sitenav a:focus-visible{outline:2px solid var(--sn-c);outline-offset:2px;}
.sitenav.top{margin:.6rem 0 1.1rem;}
.sitenav.bottom{margin:2rem 0 0;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .sitenav{--sn-portal:#8FB7F4;--sn-news:#8FB7F4;--sn-study:#E89A55;--sn-nurs:#E794B0;--sn-doc:#7FB3F0;--sn-pharm:#5FCB9E;--sn-conn:#D2A27E;--sn-se:#E3C64F;--sn-reim:#B79DF5;--sn-gov:#6FD8E6;--sn-bg:#18232B;--sn-line:#2E3C46;}
  :root:not([data-theme="light"]) .sitenav a.cur{color:#10181E;}}
:root[data-theme="dark"] .sitenav{--sn-portal:#8FB7F4;--sn-news:#8FB7F4;--sn-study:#E89A55;--sn-nurs:#E794B0;--sn-doc:#7FB3F0;--sn-pharm:#5FCB9E;--sn-conn:#D2A27E;--sn-se:#E3C64F;--sn-reim:#B79DF5;--sn-gov:#6FD8E6;--sn-bg:#18232B;--sn-line:#2E3C46;}
:root[data-theme="dark"] .sitenav a.cur{color:#10181E;}
@media (max-width:640px){.sitenav{display:grid;grid-template-columns:repeat(3,1fr);}.sitenav a{font-size:.76rem;padding:.38rem .3rem;flex:none;min-width:0;overflow:hidden;text-overflow:ellipsis;}}
@media (max-width:380px){.sitenav{grid-template-columns:repeat(2,1fr);}}
</style>""" % MARK

# ファイル名 → そのページのキー（現在ページを塗るため）。長い接頭辞から先に判定する。
PREFIX = [('index', 'portal'), ('news', 'news'), ('study', 'study'), ('nursing', 'nursing'),
          ('doctors', 'doctors'), ('pharmacists', 'pharm'), ('pharm', 'pharm'),
          ('connect', 'connect'), ('hospitalit', 'se'), ('reimbursement', 'reim'), ('gov', 'gov')]


def page_key(path):
    b = os.path.basename(path)
    for pre, key in PREFIX:
        if b == pre + '.html' or b.startswith(pre + '-'):
            return key
    return None            # contact.html・doc-*.html など（どの項目も塗らない）


def nav_html(pos, cur):
    a = []
    for key, label, var, href in NAV:
        c = ' class="cur" aria-current="page"' if key == cur else ''
        a.append('<a href="%s" style="--sn-c:var(--%s)"%s>%s</a>' % (href, var, c, label))
    return '<nav class="sitenav %s" aria-label="MediKotoのページ">%s</nav>' % (pos, ''.join(a))


def put_css(h):
    """共通ナビのCSSを本文の一番最後に足す。ページ本体の<style>は<body>内にあるので、
    それより後ろに置かないと古い指定（スマホで最後の1個だけ伸びる等）に負ける。"""
    if MARK in h:
        return h
    i = h.rfind('</body>')
    if i < 0:
        i = h.rfind('</html>')
    if i >= 0:
        return h[:i] + CSS + '\n' + h[i:]
    return h.rstrip() + '\n' + CSS + '\n'


def put_nav(h, cur, insert_if_missing):
    top, bot = nav_html('top', cur), nav_html('bottom', cur)
    n = len(re.findall(r'<nav class="sitenav (?:top|bottom)"', h))
    if n:
        h = re.sub(r'<nav class="sitenav top"[^>]*>.*?</nav>', lambda m: top, h, flags=re.S)
        h = re.sub(r'<nav class="sitenav bottom"[^>]*>.*?</nav>', lambda m: bot, h, flags=re.S)
        return h, ('ナビ差し替え(%d本)' % n)
    if not insert_if_missing:
        return h, 'ナビ無し・対象外'
    done = []
    # 上：ヘッダーのロゴ（data URI のimgを含む<a>）の直後
    m = (re.search(r'<header[^>]*>\s*<a [^>]*>\s*<img src="data:image/png;base64,[^"]+"[^>]*>\s*</a>', h, re.S)
         or re.search(r'<h1 class="logowrap"[^>]*>.*?</h1>', h, re.S)
         or re.search(r'<img src="data:image/png;base64,[^"]+"[^>]*>\s*</a>', h, re.S))
    if m:
        h = h[:m.end()] + '\n' + top + h[m.end():]
        done.append('上')
    # 下：免責文の直上（無ければクレジットの直上）
    i = h.find('<p class="disclaimer">')
    if i < 0:
        m2 = re.search(r'<(?:p|footer|div)[^>]*class="[^"]*\bcredit\b', h)
        i = m2.start() if m2 else -1
    if i >= 0:
        h = h[:i] + bot + '\n' + h[i:]
        done.append('下')
    return h, ('ナビ挿入(%s)' % '＋'.join(done) if done else '!! 挿入位置が見つからない')


def fix(path, check=False):
    src = open(path, encoding='utf-8').read()
    cur = page_key(path)
    h = put_css(src)
    h, note = put_nav(h, cur, insert_if_missing=(cur is not None))
    changed = (h != src)
    if changed and not check:
        open(path, 'w', encoding='utf-8').write(h)
    return changed, note


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    check = '--check' in sys.argv
    files = sorted(f for f in glob.glob(os.path.join(root, '*.html')))
    nchg = 0
    for f in files:
        changed, note = fix(f, check)
        if changed:
            nchg += 1
            print('%-34s %s' % (os.path.basename(f), note))
        if note.startswith('!!'):
            print('%-34s %s' % (os.path.basename(f), note))
    print('---- %d / %d ファイルを%s' % (nchg, len(files), '要修正として検出' if check else '更新'))
    # 検証：全ファイルのナビが10本・日付なしになっているか
    bad = []
    for f in files:
        h = open(f, encoding='utf-8').read()
        for m in re.finditer(r'<nav class="sitenav[^"]*"[^>]*>.*?</nav>', h, re.S):
            hrefs = re.findall(r'<a href="([^"]*)"', m.group(0))
            if len(hrefs) != 10 or any(re.search(r'-\d{4}-\d{2}-\d{2}\.html$', u) or 'claude.ai' in u for u in hrefs):
                bad.append(os.path.basename(f))
                break
    if bad:
        print('!! ナビが正しくないファイル:', ', '.join(sorted(set(bad))))
        return 1
    print('OK: 全ファイルの共通ナビは10項目・日付なしリンク')
    return 0


if __name__ == '__main__':
    sys.exit(main())
