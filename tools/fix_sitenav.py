#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：GitHub Pages 公開ファイルの共通ナビ（nav.sitenav）と、色が抜けやすい枠のCSSを現行版にそろえる。"""
import os, re, sys, glob

MARK = 'MediKoto sitenav v7'

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

CSS = """<style>/* __MARK__ */
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
.bnc-gov{background:var(--govbg,#E3F7FA);}
.bnc-gov .sub4{color:var(--gov,#0A8E9C);}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .bnc-gov{background:#0C262B;}
  :root:not([data-theme="light"]) .bnc-gov .sub4{color:#6FD8E6;}}
:root[data-theme="dark"] .bnc-gov{background:#0C262B;}
:root[data-theme="dark"] .bnc-gov .sub4{color:#6FD8E6;}
.gigi{display:flex;flex-wrap:wrap;align-items:center;gap:.35rem 1rem;margin:1.1rem 0 0;
  text-decoration:none;color:inherit;background:var(--panel,#F2F3EF);
  border:1.5px solid var(--reim,#5B3FA6);border-left:6px solid var(--reim,#5B3FA6);
  border-radius:10px;padding:.8rem 1.1rem;}
.gigi:hover{background:var(--reimbg,#F1EDF9);}
.gigi:focus-visible{outline:2px solid var(--reim,#5B3FA6);outline-offset:2px;}
.gigi-ic{font-size:1.5rem;line-height:1;flex:none;}
.gigi-b{flex:1 1 20rem;min-width:0;}
.gigi-lab{display:block;font-size:.7rem;font-weight:700;letter-spacing:.08em;color:var(--mut,#7C8A94);}
.gigi-t{display:block;font-family:"Zen Kaku Gothic New","BIZ UDPGothic",sans-serif;font-weight:700;
  font-size:1.08rem;line-height:1.5;color:var(--reim,#5B3FA6);margin:.05rem 0 .15rem;}
.gigi-d{display:block;font-size:.82rem;color:var(--sub,#4A5A66);line-height:1.7;}
.gigi-go{flex:none;font-weight:700;font-size:.88rem;color:var(--paper,#FBFAF7);
  background:var(--reim,#5B3FA6);border-radius:999px;padding:.32rem 1.1rem;white-space:nowrap;}
@media (max-width:560px){.gigi-go{width:100%;text-align:center;}}
</style>""".replace('__MARK__', MARK)

PREFIX = [('index', 'portal'), ('news', 'news'), ('study', 'study'), ('nursing', 'nursing'),
          ('doctors', 'doctors'), ('pharmacists', 'pharm'), ('pharm', 'pharm'),
          ('connect', 'connect'), ('hospitalit', 'se'), ('reimbursement', 'reim'), ('gov', 'gov'),
          ('gigikaishaku', 'reim')]


def page_key(path):
    b = os.path.basename(path)
    for pre, key in PREFIX:
        if b == pre + '.html' or b.startswith(pre + '-'):
            return key
    return None


def nav_html(pos, cur):
    a = []
    for key, label, var, href in NAV:
        c = ' class="cur" aria-current="page"' if key == cur else ''
        a.append('<a href="%s" style="--sn-c:var(--%s)"%s>%s</a>' % (href, var, c, label))
    return '<nav class="sitenav %s" aria-label="MediKotoのページ">%s</nav>' % (pos, ''.join(a))


def put_css(h):
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
    m = (re.search(r'<header[^>]*>\s*<a [^>]*>\s*<img src="data:image/png;base64,[^"]+"[^>]*>\s*</a>', h, re.S)
         or re.search(r'<h1 class="logowrap"[^>]*>.*?</h1>', h, re.S)
         or re.search(r'<img src="data:image/png;base64,[^"]+"[^>]*>\s*</a>', h, re.S))
    if m:
        h = h[:m.end()] + '\n' + top + h[m.end():]
        done.append('上')
    i = h.find('<p class="disclaimer">')
    if i < 0:
        m2 = re.search(r'<(?:p|footer|div)[^>]*class="[^"]*\bcredit\b', h)
        i = m2.start() if m2 else -1
    if i >= 0:
        h = h[:i] + bot + '\n' + h[i:]
        done.append('下')
    return h, ('ナビ挿入(%s)' % '＋'.join(done) if done else '!! 挿入位置が見つからない')


GIGI_ART = 'https://claude.ai/code/artifact/9a8233e1-dc26-4415-87d7-3caa667630f5'

GIGI_BAND = ('<a class="gigi" href="%s" rel="noopener">'
             '<span class="gigi-ic" aria-hidden="true">\U0001F4D1</span>'
             '<span class="gigi-b">'
             '<span class="gigi-lab">別ページ／過去の問を調べる</span>'
             '<span class="gigi-t">疑義解釈 実務まとめ（令和8年度改定）</span>'
             '<span class="gigi-d">令和8年度改定の疑義解釈%sを、加算名・テーマ・キーワードで探せる形に'
             '貯めています。今日のニュースではなく、前に出た問を調べたいときはこちら。</span>'
             '</span><span class="gigi-go">開く →</span></a>')


def gigi_count(root):
    f = os.path.join(root, 'gigikaishaku.html')
    if not os.path.exists(f):
        return ''
    n = len(re.findall(r'<article class="qa"', open(f, encoding='utf-8').read()))
    return ('（全%d問）' % n) if n else ''


def put_gigi(h, href, note_n=''):
    if 'class="gigi"' in h:
        return h, ''
    m = re.search(r'<nav class="hub"[^>]*>.*?</nav>', h, re.S)
    if not m:
        return h, '!! hubナビが見つからない（入口を入れられない）'
    return h[:m.end()] + '\n' + (GIGI_BAND % (href, note_n)) + h[m.end():], '疑義解釈まとめへの入口を挿入'


def fix(path, check=False, gigi_href=GIGI_ART, gigi_n=''):
    src = open(path, encoding='utf-8').read()
    cur = page_key(path)
    h = put_css(src)
    h, note = put_nav(h, cur, insert_if_missing=(cur is not None))
    if os.path.basename(path) == 'reimbursement.html':
        h, n2 = put_gigi(h, gigi_href, gigi_n)
        if n2:
            note = (note + '／' + n2) if note else n2
    changed = (h != src)
    if changed and not check:
        open(path, 'w', encoding='utf-8').write(h)
    return changed, note


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    check = '--check' in sys.argv
    files = sorted(f for f in glob.glob(os.path.join(root, '*.html')))
    gigi_href = 'gigikaishaku.html' if os.path.exists(os.path.join(root, 'gigikaishaku.html')) else GIGI_ART
    gigi_n = gigi_count(root)
    nchg = 0
    for f in files:
        changed, note = fix(f, check, gigi_href, gigi_n)
        if changed:
            nchg += 1
            print('%-34s %s' % (os.path.basename(f), note))
        if note.startswith('!!'):
            print('%-34s %s' % (os.path.basename(f), note))
    print('---- %d / %d ファイルを%s' % (nchg, len(files), '要修正として検出' if check else '更新'))
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
    r = os.path.join(root, 'reimbursement.html')
    if os.path.exists(r):
        ok = 'class="gigi"' in open(r, encoding='utf-8').read()
        print(('OK: 診療報酬ページに疑義解釈まとめへの入口あり（' + gigi_href + gigi_n + '）') if ok
              else '!! 診療報酬ページに疑義解釈まとめへの入口が無い')
        if not ok:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
