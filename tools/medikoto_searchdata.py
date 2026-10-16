#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：ポータル（index.html）の本文検索データを search-data.json に分離する（2026-10-16追加）。

なぜ：ポータルの search-data（各ページ本文の先頭6000字）は1日に約60KBずつ増え、index.html が3.4MBまで育っていた。
本文データはポータルを開いただけでは要らず、検索したときに1回読めばよい。そこで
  - index.html の中の search-data は空（[]）にして data-src="search-data.json" を付け、
  - 本文データは隣の search-data.json に合流させる（既存分＋ポータルが持ってきた分＋リポジトリの日付つきファイルから欠けを補う）。
  - 検索スクリプトは「検索したときに search-data.json を1回だけ読む」形に直す（mk-search-lazy v1。何度実行しても1回だけ）。
  - 検索バーの種類（LAB／PG／タグ色／案内文）に「栄養」を足す。

claude.ai 側のポータルは、同じ search-data.json を添付ファイル（files）として持ち、直近10日分だけを本文に残す。
GitHub 側はこのツールが毎朝合流させるので、日付つきファイルの全号が検索できる。

使い方：fix_sitenav.py から run(root) が呼ばれる。単独なら python3 tools/medikoto_searchdata.py .
"""
import os, re, sys, glob, json, html as H

JSON_NAME = 'search-data.json'
MAXLEN = 6000
# ファイル名の接頭辞 → search-data の k（ポータルの PG と同じ鍵）
PREFIX_K = [
    ('news', 'news'), ('study', 'study'), ('nursing', 'nursing'), ('doctors', 'doctors'), ('pharm', 'pharm'),
    ('connect', 'connect'), ('hospitalit', 'se'), ('nutrition', 'nutrition'), ('reimbursement', 'reim'), ('global', 'global'),
]
K_ORDER = [k for _, k in PREFIX_K]
NUTR = {'c': '#D9603A', 'dc': '#F19B7C'}


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def strip_tags(s):
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', H.unescape(s)).strip()


def find_tag(x):
    m = re.search(r'<script[^>]*\bid="search-data"[^>]*>', x)
    if not m:
        return None
    e = x.find('</script>', m.end())
    return m.start(), m.end(), e


def patch_js(x, out):
    """検索スクリプトを「検索時に1回だけ読む」形に。すでに直っていれば何もしない。"""
    if 'function ensureData(' in x:
        return x
    old_head = "  var S=pj('search-data')||[];\n  var TX={};\n"
    old_tail = "                s:((en.date_jp||'')+' '+g[1]+' '+th+' '+(TX[en.date+'|'+g[0]]||''))});\n    }\n  }\n"
    old_run = "    if(!qs){sout.innerHTML='';paintCounts(null);return;}\n"
    if old_head not in x or old_tail not in x or old_run not in x:
        out.append('!! 検索データ: 検索スクリプトの形が想定と違うので遅延読み込みに直せない（本文データは search-data.json に出すが、ページ内の data-src は付けない）')
        return None
    new_head = ("  /* mk-search-lazy v1（2026-10-16）：本文データ（search-data.json）はポータルを開いただけでは読まず、検索したときに1回だけ読む */\n"
                "  var SD=document.getElementById('search-data'); var SRC=SD?SD.getAttribute('data-src'):null;\n"
                "  var TX={}, idx=[], loaded=false, loading=null;\n"
                "  function buildIdx(S){\n  TX={}; idx=[];\n")
    x = x.replace(old_head, new_head, 1)
    new_tail = old_tail + ("  }\n  buildIdx(pj('search-data')||[]);\n"
                           "  function ensureData(cb){\n"
                           "    if(loaded||!SRC){cb();return;}\n"
                           "    if(!loading){loading=fetch(SRC,{cache:'no-cache'}).then(function(r){return r.ok?r.json():[];}).catch(function(){return [];})\n"
                           "      .then(function(S){loaded=true;buildIdx(S);});}\n"
                           "    loading.then(cb);\n  }\n")
    x = x.replace(old_tail, new_tail, 1)
    x = x.replace(old_run, old_run + "    if(!loaded&&SRC){sout.innerHTML='<p class=\"snone\">本文データを読み込んでいます…</p>';ensureData(run);return;}\n", 1)
    x = re.sub(r"\n  var idx=\[\];\n  for\(var a=0;a<arch\.length;a\+\+\)\{", "\n  for(var a=0;a<arch.length;a++){", x, count=1)
    return x


def patch_search_ui(x):
    """検索バーの種類に「栄養」を足す（あれば何もしない）。"""
    n = 0
    pairs = [
        ('.mkf-tag[data-k="se"]{--k:#8E7414;}', '.mkf-tag[data-k="se"]{--k:#8E7414;}.mkf-tag[data-k="nutrition"]{--k:%s;}' % NUTR['c'], '.mkf-tag[data-k="nutrition"]{--k:#'),
        (':root:not([data-theme="light"]) .mkf-tag[data-k="se"]{--k:#E3C64F;}',
         ':root:not([data-theme="light"]) .mkf-tag[data-k="se"]{--k:#E3C64F;}:root:not([data-theme="light"]) .mkf-tag[data-k="nutrition"]{--k:%s;}' % NUTR['dc'],
         ':root:not([data-theme="light"]) .mkf-tag[data-k="nutrition"]'),
        (':root[data-theme="dark"] .mkf-tag[data-k="se"]{--k:#E3C64F;}',
         ':root[data-theme="dark"] .mkf-tag[data-k="se"]{--k:#E3C64F;}:root[data-theme="dark"] .mkf-tag[data-k="nutrition"]{--k:%s;}' % NUTR['dc'],
         ':root[data-theme="dark"] .mkf-tag[data-k="nutrition"]'),
        ('"se": "病院SE", "reim": "診療報酬"', '"se": "病院SE", "nutrition": "栄養", "reim": "診療報酬"', '"nutrition": "栄養"'),
        ('["se", "病院SE", "se_url", "se_theme", "--se"], ', '["se", "病院SE", "se_url", "se_theme", "--se"], ["nutrition", "栄養", "nutrition_url", "nutrition_theme", "--nutr"], ', '"nutrition_url", "nutrition_theme"'),
        ('病院SE・診療報酬の全ページの本文から探せます。', '病院SE・栄養・診療報酬・海外DXの全ページの本文から探せます。', None),
        ('病院SE・診療報酬・海外DXの全ページから探せます。', '病院SE・栄養・診療報酬・海外DXの全ページから探せます。', None),
    ]
    for old, new, marker in pairs:
        if (marker and marker in x) or old not in x:
            continue
        x = x.replace(old, new, 1)
        n += 1
    return x, n


def run(root):
    out = []
    p = os.path.join(root, 'index.html')
    if not os.path.exists(p):
        return ['!! 検索データ: index.html が無い']
    x = read(p)
    tag = find_tag(x)
    if not tag:
        return ['!! 検索データ: index.html に search-data が無い（何もしない）']
    s, e0, e1 = tag
    try:
        inline = json.loads(x[e0:e1] or '[]')
    except Exception as ex:
        return ['!! 検索データ: search-data を読めない（%s）' % ex]
    jp = os.path.join(root, JSON_NAME)
    J = []
    if os.path.exists(jp):
        try:
            J = json.loads(read(jp))
        except Exception as ex:
            out.append('!! 検索データ: %s を読めないので作り直す（%s）' % (JSON_NAME, ex))
            J = []
    D = {}
    for src in (J, inline):          # ポータルが持ってきた分（新しい）で上書き
        for en in src:
            if isinstance(en, dict) and en.get('d') and en.get('x'):
                D[(en['d'], en.get('k', 'news'))] = en['x']
    n_inline = len(inline)
    # リポジトリの日付つきファイルから欠けている号を補う
    added = 0
    for pre, k in PREFIX_K:
        for f in glob.glob(os.path.join(root, pre + '-2*.html')):
            m = re.match(r'^%s-(\d{4}-\d{2}-\d{2})\.html$' % re.escape(pre), os.path.basename(f))
            if not m or (m.group(1), k) in D:
                continue
            try:
                D[(m.group(1), k)] = strip_tags(read(f))[:MAXLEN]
                added += 1
            except Exception:
                pass
    rows = [{'d': d, 'k': k, 'x': D[(d, k)]} for d, k in sorted(D, key=lambda t: (t[0], K_ORDER.index(t[1]) if t[1] in K_ORDER else 99), reverse=True)]
    with open(jp, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, separators=(',', ':'))
    # ページ側：本文データを空にして data-src を付ける（スクリプトが直せる場合だけ）
    x2 = patch_js(x, out)
    if x2 is not None:
        x = x2
        tag = find_tag(x)
        s, e0, e1 = tag
        x = x[:s] + '<script type="application/json" id="search-data" data-src="%s">[]</script>' % JSON_NAME + x[e1 + len('</script>'):]
    x, n_ui = patch_search_ui(x)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(x)
    out.append('OK: 本文検索データを %s に分離（%d件＝既存 %d＋ポータル %d・ファイルから補充 %d／index.html %dKB／検索の種類に栄養 %s）'
               % (JSON_NAME, len(rows), len(J), n_inline, added, len(x.encode()) // 1024, '追加' if n_ui else 'あり'))
    return out


if __name__ == '__main__':
    for line in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(line)
