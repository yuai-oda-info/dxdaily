#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：全HTMLの共通ナビ（11項目）とCSSをそろえ、weekly-study.html を作り直す。
使い方: python3 tools/fix_sitenav.py . [--check]
"""
import os, re, sys, glob

MARK = 'MediKoto sitenav v8'

NAV = [
    ('portal',  'ポータル',      'sn-portal', './'),
    ('news',    'ヘッドライン',  'sn-news',   'news.html'),
    ('study',   '今日の勉強会',  'sn-study',  'study.html'),
    ('weekly',  '週間実践DX',    'sn-study',  'weekly-study.html'),
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
@media (min-width:641px){.sitenav a{padding:.42rem .45rem;font-size:.84rem;}}
@media (min-width:641px) and (max-width:900px){.sitenav{display:grid;grid-template-columns:repeat(6,1fr);}.sitenav a{flex:none;min-width:0;}}
@media (max-width:640px){.sitenav{display:grid;grid-template-columns:repeat(3,1fr);}.sitenav a{font-size:.76rem;padding:.38rem .3rem;flex:none;min-width:0;overflow:hidden;text-overflow:ellipsis;}}
@media (max-width:380px){.sitenav{grid-template-columns:repeat(2,1fr);}}
/* バックナンバー枠の色（HTMLだけ増えてCSSが抜ける事故を防ぐため、ここでも定義する） */
.bnc-gov{background:var(--govbg,#E3F7FA);}
.bnc-gov .sub4{color:var(--gov,#0A8E9C);}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .bnc-gov{background:#0C262B;}
  :root:not([data-theme="light"]) .bnc-gov .sub4{color:#6FD8E6;}}
:root[data-theme="dark"] .bnc-gov{background:#0C262B;}
:root[data-theme="dark"] .bnc-gov .sub4{color:#6FD8E6;}
/* 疑義解釈まとめ（別ページ）への入口。色変数だけに頼らずリテラルの控えを必ず添える */
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

PREFIX = [('weekly-study', 'weekly'), ('index', 'portal'), ('news', 'news'), ('study', 'study'), ('nursing', 'nursing'),
          ('doctors', 'doctors'), ('pharmacists', 'pharm'), ('pharm', 'pharm'),
          ('connect', 'connect'), ('hospitalit', 'se'), ('reimbursement', 'reim'), ('gov', 'gov'),
          ('gigikaishaku', 'reim')]   # 疑義解釈まとめは診療報酬の下位ページ扱い


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
             '<span class="gigi-lab">別ページ／改定内容と疑義解釈を調べる</span>'
             '<span class="gigi-t">令和8年度改定 実務まとめ（個別改定項目＋疑義解釈）</span>'
             '<span class="gigi-d">令和8年度改定で何がどう変わったか%sと、その後に出た疑義解釈を、'
             '同じテーマ分けで1ページに。改定項目を開くと、その項目の問と答えがぶら下がります。</span>'
             '</span><span class="gigi-go">開く →</span></a>')


def gigi_count(root):
    f = os.path.join(root, 'gigikaishaku.html')
    if not os.path.exists(f):
        return ''
    n = len(re.findall(r'"kd":"', open(f, encoding='utf-8').read()))
    return ('（改定項目%d件）' % n) if n else ''


def put_gigi(h, href, note_n=''):
    if 'class="gigi"' in h:
        return h, ''
    m = re.search(r'<nav class="hub"[^>]*>.*?</nav>', h, re.S)
    if not m:
        return h, '!! hubナビが見つからない（入口を入れられない）'
    return h[:m.end()] + '\n' + (GIGI_BAND % (href, note_n)) + h[m.end():], '疑義解釈まとめへの入口を挿入'


WK_CATS = ['国の医療DX', '看護', '医師', '薬剤師', '相談支援・連携', '病院SE', '診療報酬', '海外']
WK_URL = 'https://yuai-oda-info.github.io/dxdaily/weekly-study.html'
WK_RS = ['公的・施設公式の出典', '制度・締切に直結', '導入前後の数値', '現場の行動に直結', '有効期限が長い']
WK_RX = [r'厚生労働|厚労省|PMDA|医薬品医療機器|デジタル庁|内閣府|総務省|経済産業省|中医協|中央社会保険医療協議会|厚生局|支払基金|国保中央会|AMED|IPA|JPCERT|NISC|評価機構|学会|協会|医師会|薬剤師会|大学|病院|CMS|FDA|ONC|ASTP|CISA|HHS|NHS|NIST|政府',
         r'承認|保険適用|改定|法改正|施行|告示|通知|省令|締切|期限|補助金|ガイドライン|指針|届出|算定|診療報酬|制度|経過措置',
         r'\d[\d.,]*\s*(?:%|％|件|分|秒|時間|人|円|倍)[^。]{0,25}(?:→|から)[^。]{0,25}\d[\d.,]*\s*(?:%|％|件|分|秒|時間|人|円|倍)|\d[^。]{0,25}(?:削減|短縮|減少|増加)',
         r'注意喚起|チェック|確認|手順|点検|照合|休薬|更新プログラム|脆弱性|アップデート|訓練',
         r'ガイドライン|指針|制度|法律|研究|論文|計画|方針|工程表|基準']
WK_CSS = """<style>/* MediKoto weekly v2 */
:root{--gov:#0E8E9C;--nurs:#C25573;--doc:#285F9D;--pharm:#2F8F6B;--conn:#7A5230;--se:#8E7414;--reim:#5B3FA6;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--gov:#6FD8E6;--nurs:#E794B0;--doc:#7FB3F0;--pharm:#5FCB9E;--conn:#D2A27E;--se:#E3C64F;--reim:#B79DF5;}}
:root[data-theme="dark"]{--gov:#6FD8E6;--nurs:#E794B0;--doc:#7FB3F0;--pharm:#5FCB9E;--conn:#D2A27E;--se:#E3C64F;--reim:#B79DF5;}
.wkjump{display:flex;flex-wrap:wrap;gap:.4rem;margin:.9rem 0 0;}
.wkjump a{font-size:.84rem;font-weight:700;text-decoration:none;color:var(--c,#C56A15);border:1px solid var(--rule,#D9DDE0);border-radius:8px;padding:.3rem .7rem;background:var(--panel,#F2F3EF);}
.wkjump a:hover{border-color:var(--c,#C56A15);}
.wkmeta{font-size:.8rem;color:var(--mut,#7C8A94);margin:.15rem 0 .4rem;}
.wkimp{display:inline-block;font-size:.74rem;font-weight:700;border:1px solid var(--rule,#D9DDE0);border-radius:5px;padding:0 .4rem;margin:0 .3rem .2rem 0;color:var(--sub,#4A5A66);}
.wkimp.sc{border-color:#C56A15;color:#C56A15;}
.wkx{font-size:.9rem;line-height:1.85;margin:.3rem 0 0;}
.wknone{font-size:.86rem;color:var(--mut,#7C8A94);margin:.3rem 0 0;}
table.wkt{border-collapse:collapse;width:100%;font-size:.88rem;}
table.wkt th{text-align:left;color:var(--mut,#7C8A94);font-size:.78rem;border-bottom:2px solid var(--rule2,#1A242E);padding:.35rem .6rem;}
table.wkt td{border-bottom:1px solid var(--rule,#D9DDE0);padding:.45rem .6rem;vertical-align:top;}
table.wkt td.d{white-space:nowrap;font-weight:700;}
</style>"""


def _wk_text(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip()


def _wk_score(txt, src):
    r = [i for i, rx in enumerate(WK_RX) if re.search(rx, src if i == 0 else txt)]
    if re.search(r'PR TIMES|企業発表', src) and not re.search(r'公的情報|導入施設発表', src):
        r = [i for i in r if i != 0]
    return r


def _wk_sc(t):
    return '<div class="script"><p class="slab">司会用そのまま読み上げ</p><p>%s</p></div>' % t


def _wk_cut(x, n):
    o = ''
    for q in re.findall(r'[^。]+。', x):
        if len(o + q) > n and o:
            break
        o += q
    return o or x[:n]


def _wk_badges(r):
    return '<span class="wkimp sc">重要度 %d/5</span>' % len(r) + ''.join('<span class="wkimp">%s</span>' % WK_RS[i] for i in r)


def _wk_pick(cands):
    best = {}
    for c in cands:
        k = _wk_text(c['t'])
        if k not in best or len(c['r']) > len(best[k]['r']):
            best[k] = c
    return sorted(best.values(), key=lambda c: (len(c['r']), c['d']), reverse=True)


def build_weekly(root, check=False):
    fs = sorted(glob.glob(os.path.join(root, 'study-20[0-9][0-9]-[0-9][0-9]-[0-9][0-9].html')))
    days = []
    for f in reversed(fs):
        h = open(f, encoding='utf-8').read()
        secs = re.findall(r'<section class="men" id="(k\d)">\s*<header class="menhead"><span class="menno" style="color:([^"]+)">\d+</span><h2>(.*?)</h2>.*?</header>\s*<p class="hh"[^>]*>(.*?)</p>(.*?)</section>', h, re.S)
        if not secs:
            continue
        d = os.path.basename(f)[6:16]
        lab = re.search(r'<p class="dateline"><b>(.*?)</b>', h)
        days.append((d, _wk_text(lab.group(1)) if lab else d, os.path.basename(f), secs, h))
        if len(days) == 7:
            break
    if not days:
        return '週間勉強会: 対象の勉強会が無いため作成せず'
    base = days[0][4]
    i1, i2, i3 = base.find('<h1'), base.find('<div class="flowbar"'), base.find('<nav class="sitenav bottom"')
    if min(i1, i2, i3) < 0:
        return '!! 週間勉強会: study の型が見つからず作成せず'
    j = base.find('</header>', i1)
    themes = {}
    m = re.search(r'id="search-lite">(.*?)</script>', base, re.S)
    try:
        import json
        themes = dict((r[0], r[3]) for r in json.loads(m.group(1)) if r[2] == 'study')
    except Exception:
        pass
    cats, cols = {}, {}
    for d, lab, fn, secs, _ in days:
        md = '%d/%d%s' % (int(d[5:7]), int(d[8:10]), (re.search(r'（.）', lab).group(0) if '（' in lab else ''))
        for k, col, h2, hh, rest in secs:
            sc = re.search(r'<p class="slab">.*?</p>\s*<p>(.*?)</p>', rest, re.S)
            src = re.search(r'出典：(.*?)</p>', rest, re.S)
            txt, srct = _wk_text(hh + ' ' + (sc.group(1) if sc else '')), _wk_text(src.group(1) if src else '')
            cats.setdefault(_wk_text(h2), []).append(dict(d=d, md=md, col=col, t=hh.strip(), x=_wk_text(sc.group(1)) if sc else '', s=srct,
                                                          href='%s#%s' % (fn, k), r=_wk_score(txt + ' ' + srct, srct)))
        nf = os.path.join(root, 'news-%s.html' % d)
        if os.path.exists(nf):
            for n, sec in re.findall(r'<section[^>]*id="sec-col(\d)"[^>]*>(.*?)</section>', open(nf, encoding='utf-8').read(), re.S):
                h2 = _wk_text((re.search(r'<h2>(.*?)</h2>', sec, re.S) or re.search('()', '')).group(1))
                ser = re.sub(r'^コラム\s*[①②③：:]?\s*', '', h2)
                th = re.search(r'<p class="coltheme">(.*?)</p>', sec, re.S)
                if not th:
                    continue
                body = _wk_text(re.sub(r'<h3.*?</h3>', '', sec.split('<div class="colbody">', 1)[-1].split('<div class="imp"', 1)[0], flags=re.S))
                srct = _wk_text(' '.join(re.findall(r'<p class="(?:il|c3meta)">(.*?)</p>', sec, re.S)))
                cols.setdefault(ser, []).append(dict(d=d, md=md, t=th.group(1).strip(), b=body, s='',
                                                     href='news-%s.html#sec-col%s' % (d, n), r=_wk_score(body + ' ' + th.group(1), srct), n=n))
    ses = []
    for d, lab, fn, _, _ in days:
        hf = os.path.join(root, 'hospitalit-%s.html' % d)
        m = os.path.exists(hf) and re.search(r'id="jirei">(.*?)(?:<h4|</section>)', open(hf, encoding='utf-8').read(), re.S)
        for row in re.findall(r'<tr>(<td>.*?)</tr>', m.group(1) if m else '', re.S):
            td = re.findall(r'<td>(.*?)</td>', row, re.S)
            if len(td) == 4 and 'geo' not in td[0]:
                t = [_wk_text(x) for x in td]
                ses.append(dict(d=d, md='%d/%d' % (int(d[5:7]), int(d[8:10])), t=t[0], x=t, src=td[3], href='hospitalit-%s.html#jirei' % d, r=_wk_score(' '.join(t), t[3])))
    span = '%s〜%s' % (days[-1][1], days[0][1])
    order = WK_CATS + [c for c in cats if c not in WK_CATS]
    out_b = [WK_CSS, '<nav class="wkjump" aria-label="大項目">']
    out_b += ['<a href="#w%d" style="--c:%s">%s</a>' % (n + 1, cats[c][0]['col'] if c in cats else 'var(--mut)', c) for n, c in enumerate(order)]
    out_b.append('<a href="#wse">病院SE実践事例</a><a href="#wcol">コラム3本</a><a href="#wdays">日付から開く</a></nav>')
    out_b.append('<section class="men" id="wopen">\n<header class="menhead"><span class="menno">始</span><h2>はじめに</h2></header>%s</section>\n' % _wk_sc('週間勉強会を始めます。%sの勉強会から、重要度の高い8題と、病院SEの実践事例1例、コラム3本を振り返ります。' % span))
    for n, c in enumerate(order):
        col = cats[c][0]['col'] if c in cats else 'var(--mut)'
        out_b.append('<section class="men" id="w%d">\n<header class="menhead"><span class="menno" style="color:%s">%d</span><h2>%s</h2><span class="minchip">週の1題</span></header>' % (n + 1, col, n + 1, c))
        if c in cats:
            p = _wk_pick(cats[c])[0]
            out_b.append('<p class="hh" style="font-size:1.08rem"><a href="%s" style="color:inherit">%s</a></p><p class="wkmeta">%s の勉強会より（候補%d題）</p>%s%s<p class="hsrc">くわしくは → <a href="%s">その日の勉強会</a>｜出典：%s</p>'
                         % (p['href'], p['t'], p['md'], len(cats[c]), _wk_badges(p['r']), _wk_sc(p['x'].replace('今日の確認です', '今週の確認です').replace('きょうは、', '').replace('きょうは', '')), p['href'], p['s']))
        else:
            out_b.append('<p class="wknone">この1週間は新着がありませんでした。</p>')
        out_b.append('</section>\n')
    out_b.append('<section class="men" id="wse">\n<header class="menhead"><span class="menno" style="color:var(--se)">SE</span><h2>病院SE実践事例</h2><span class="minchip">国内1例</span></header>')
    if ses:
        p = _wk_pick(ses)[0]
        out_b.append('<p class="hh" style="font-size:1.05rem">%s</p><p class="wkmeta">%s の病院SEページより（候補%d例）</p>%s%s<p class="wkx"><b>導入前 → 導入後：</b>%s</p><p class="hsrc">出典：%s ／ くわしくは → <a href="%s">その日の病院SE実践事例</a></p>'
                     % (p['t'], p['md'], len(ses), _wk_badges(p['r']), _wk_sc('病院SEの実践事例です。%sの取り組みです。%s導入前は「%s」、導入後は「%s」です。' % ((p['t'], _wk_cut(p['x'][1], 110)) + tuple(v.strip() for v in (p['x'][2].split('→') + [''])[:2]))), p['x'][2], p['src'], p['href']))
    else:
        out_b.append('<p class="wknone">この1週間の国内事例はありません。</p>')
    out_b.append('</section>\n')
    out_b.append('<section class="men" id="wcol">\n<header class="menhead"><span class="menno" style="color:var(--acc)">コラム</span><h2>今週のコラム3本</h2><span class="minchip">読みもの</span></header>')
    picked = sorted((dict(_wk_pick(v)[0], ser=k) for k, v in cols.items()), key=lambda c: c["n"])[:3]
    for p in picked:
        out_b.append('<p class="wkmeta" style="margin-top:1rem">%s ／ %s ヘッドライン掲載</p><p class="hh" style="font-size:1.05rem"><a href="%s" style="color:inherit">%s</a></p>%s%s<p class="hsrc">全文 → <a href="%s">ヘッドラインのコラム</a></p>'
                     % (p['ser'], p['md'], p['href'], p['t'], _wk_badges(p['r']), _wk_sc('コラム、%sです。%s。%s' % (p['ser'], _wk_text(p['t']), _wk_cut(p['b'], 150))), p['href']))
    if not picked:
        out_b.append('<p class="wknone">この1週間のコラムはありません。</p>')
    out_b.append(_wk_sc('今週の振り返りは以上です。気になった題は、リンクからその日の勉強会とヘッドラインで確かめてください。'))
    out_b.append('</section>\n')
    trs = ''.join('<tr><td class="d">%s</td><td>%s</td><td><a href="%s">開く</a></td></tr>' % (lab, themes.get(d, ''), fn) for d, lab, fn, _, _ in days)
    out_b.append('<section class="men" id="wdays">\n<header class="menhead"><span class="menno">日付</span><h2>日付から開く</h2></header>'
                 '<div style="overflow-x:auto"><table class="wkt"><thead><tr><th>日付</th><th>その日のテーマ</th><th>リンク</th></tr></thead><tbody>%s</tbody></table></div>'
                 '<p class="wknone">選び方：直近7号の勉強会の全題を、MediKotoの重要度ルール（①公的・施設公式の出典 ②制度・締切に直結 ③導入前後の数値 ④現場の行動に直結 ⑤有効期限が長い）で採点し、大項目ごとに点数が最も高い1題を載せます（同点は新しい号、同じ見出しは1件扱い）。病院SE実践事例は病院SEページの国内事例から、コラムは系統ごとに、同じ方法で1本ずつ。採点は語句にもとづく自動判定です。毎朝作り直します。</p>\n' % trs)
    head = ('<h1 style="font-family:\'Zen Kaku Gothic New\',\'BIZ UDPゴシック\',sans-serif;font-weight:900;font-size:1.72rem;color:var(--acc);margin:0 0 .2rem;line-height:1.35">週間勉強会</h1>\n'
            '<p class="dateline"><b>%s</b><span>直近7号から選出・毎日更新</span><span>発行：MediKoto（メディコト）</span></p>\n'
            '<p class="slogan" style="font-size:1.05rem;margin:.3rem 0 0">この1週間の勉強会から、重要度の高い題を大項目ごとに1題、病院SE実践事例（国内）を1例、コラムを3本選びました。'
            '<small>週1回の振り返りやミーティングに。司会用の読み上げ原稿つきで、約15分です。</small></p>\n'
            '<p class="mh-meta">病院・クリニック・介護/在宅事業者の職場内共有用</p>\n') % span
    desc = 'この1週間の「今日の勉強会」から、重要度ルールで大項目ごとに1題とコラム3本を選んだ週のまとめ。週1回の振り返りに。（%s更新）' % days[0][1]
    title = 'MediKoto 週間勉強会｜この1週間の重要な医療DX・AIの話題'
    top = base[:i1]
    top = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, top, 1, re.S)
    top = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda x: x.group(1) + title, top)
    top = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*', lambda x: x.group(1) + desc, top)
    top = re.sub(r'(<link rel="canonical" href="|<meta property="og:url" content=")[^"]*', lambda x: x.group(1) + WK_URL, top)
    out = top + head + base[j:i2] + '\n'.join(out_b) + base[i3:]
    p = os.path.join(root, 'weekly-study.html')
    old = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    strip = lambda x: re.sub(r'<nav class="sitenav.*?</nav>|<style>/\* MediKoto sitenav v\d+ \*/.*?</style>', '', x, flags=re.S)
    msg = '週間勉強会: %s（%d号から選出）' % (span, len(days))
    if strip(old) != strip(out) and not check:
        open(p, 'w', encoding='utf-8').write(out)
        msg += ' を更新'
    sm = os.path.join(root, 'sitemap.xml')
    if os.path.exists(sm) and not check:
        x = open(sm, encoding='utf-8').read()
        x2 = re.sub(r'<url><loc>%s</loc>.*?</url>\n?' % re.escape(WK_URL), '', x).replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (WK_URL, days[0][0]))
        if x2 != x:
            open(sm, 'w', encoding='utf-8').write(x2)
    return msg


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
    print(build_weekly(root, check))
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
            if len(hrefs) != len(NAV) or any(re.search(r'-\d{4}-\d{2}-\d{2}\.html$', u) or 'claude.ai' in u for u in hrefs):
                bad.append(os.path.basename(f))
                break
    if bad:
        print('!! ナビが正しくないファイル:', ', '.join(sorted(set(bad))))
        return 1
    print('OK: 全ファイルの共通ナビは11項目・日付なしリンク')
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
