#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：ポータル（index.html）のバックナンバー表を、リポジトリにある日付つきファイルから作り直す（2026-10-07追加）。

なぜ：ポータルのアーティファクトはアカウントごとに別物で、archive-data もアカウントごとに別々に増える。
移行元と移行先のどちらで作った号も GitHub（https://yuai-oda-info.github.io/dxdaily/）には残るので、
表は「リポジトリに実在する日付つきファイル」を正にして作り直す。どのアカウントの公開タスクが動いても同じ結果になる。

対象の表と元ファイル：
  #bn         ヘッドライン  news-YYYY-MM-DD.html
  #bn-study   勉強会        study-YYYY-MM-DD.html
  #bn-nursing 看護          nursing-YYYY-MM-DD.html
  #bn-doctors 医師          doctors-YYYY-MM-DD.html
  #bn-pharm   薬剤師        pharm-YYYY-MM-DD.html
  #bn-connect 相談支援      connect-YYYY-MM-DD.html
  #bn-se      病院SE        hospitalit-YYYY-MM-DD.html
  #bn-reim    診療報酬      reimbursement-YYYY-MM-DD.html
  #bn-gov     国の医療DX    gov-YYYY-MM-DD.html（gov だけは最新の版も載せる）
（事例DX・海外DX・サイバーDX・感染症DXの表は fix_sitenav.py／medikoto_themes.py が別に作る）

ルール：
- 行＝その種類の日付つきファイル1本につき1行、新しい順。ポータルの最新号の日付（archive-data の latest.date）の行は載せない（gov を除く）。
- テーマの文：既存の表にその日付の行があればその文をそのまま使う。無ければ各ページの search-lite（日付・種類・テーマ）、
  それも無ければ各ファイルの見出し・<title> から取る。
- 「開く」のリンクは必ずリポジトリ内の日付つきファイル（claude.ai のURLは残さない）。
- archive-data の各URLが claude.ai のままで、同じ日付のファイルがリポジトリにあれば、そのファイル名に直す。
- 表の枠・見出し・説明文・CSS は変えない（<tbody> の中身だけ入れ替える）。何度実行しても結果は同じ。
使い方：fix_sitenav.py から run(root) が呼ばれる。単独なら python3 tools/medikoto_backnumber.py .
"""
import os, re, sys, glob, json, datetime, html as H

WD = '月火水木金土日'

# (表のid, ファイルの接頭辞, search-lite の k, archive-data のキー)
TABLES = [
    ('bn',          'news',          'news',    'url'),
    ('bn-study',    'study',         'study',   'study_url'),
    ('bn-nursing',  'nursing',       'nursing', 'nursing_url'),
    ('bn-doctors',  'doctors',       'doctors', 'doctors_url'),
    ('bn-pharm',    'pharm',         'pharm',   'pharm_url'),
    ('bn-connect',  'connect',       'connect', 'connect_url'),
    ('bn-se',       'hospitalit',    'se',      'se_url'),
    ('bn-reim',     'reimbursement', 'reim',    'reim_url'),
    ('bn-gov',      'gov',           'gov',     'gov_url'),
]
ARCHIVE_ONLY = [('global', 'global_url')]   # 表は fix_sitenav.py が作る。archive-data のURLだけ直す

DATE_RE = re.compile(r'^(?P<pre>[a-z]+)-(?P<d>\d{4}-\d{2}-\d{2})\.html$')


def jp(ds):
    d = datetime.date.fromisoformat(ds)
    return '%d年%d月%d日（%s）' % (d.year, d.month, d.day, WD[d.weekday()])


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def dated_files(root, pre):
    out = {}
    for f in glob.glob(os.path.join(root, pre + '-2*.html')):
        m = DATE_RE.match(os.path.basename(f))
        if m and m.group('pre') == pre:
            out[m.group('d')] = os.path.basename(f)
    return out


def search_lite_themes(root):
    """全ページの search-lite を合わせて {(日付, k): テーマ} を作る。新しいファイルの値を優先する。"""
    themes = {}
    def fdate(p):
        m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(p))
        return m.group(1) if m else ''
    files = sorted(glob.glob(os.path.join(root, '*-2*.html')), key=fdate)   # 古い→新しいの順に読み、新しい方で上書き
    for f in files:
        try:
            h = read(f)
        except Exception:
            continue
        m = re.search(r'id="search-lite"[^>]*>(.*?)</script>', h, re.S)
        if not m:
            continue
        try:
            rows = json.loads(m.group(1))
        except Exception:
            continue
        for r in rows:
            if isinstance(r, list) and len(r) >= 4 and r[3]:
                themes[(r[0], r[2])] = r[3]
    return themes


def strip_tags(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def theme_from_file(root, fn, k):
    """search-lite に無いときの控え：ページの中身から1行を取る。"""
    try:
        h = read(os.path.join(root, fn))
    except Exception:
        return ''
    if k == 'news':
        t = []
        for sid in ('sec-col1', 'sec-col2'):
            i = h.find('id="%s"' % sid)
            if i >= 0:
                m = re.search(r'class="coltheme"[^>]*>(.*?)</p>', h[i:i + 30000], re.S)
                if m:
                    t.append(strip_tags(m.group(1)))
        if t:
            return t
    if k == 'gov':
        m = re.search(r'<p class="snapnote">(.*?)</p>', h, re.S)
        if m:
            return '保存版（' + strip_tags(m.group(1))[:60] + '）'
    m = re.search(r'<title>(.*?)</title>', h, re.S)
    if m:
        t = strip_tags(m.group(1))
        t = re.sub(r'^MediKoto[^｜]*｜', '', t)
        return t
    return ''


def theme_cell(k, theme):
    if k == 'news':
        if isinstance(theme, list):
            a = H.escape(theme[0])
            if len(theme) > 1:
                b = theme[1]
                if not b.startswith('セキュリティ・BCP講座'):
                    b = 'セキュリティ・BCP講座：' + b
                a += '<br><span style="color:var(--muted);font-size:.86em">%s</span>' % H.escape(b)
            return a
    if isinstance(theme, list):
        theme = theme[0]
    return H.escape(theme or '')


def rebuild_table(x, tid, pre, k, files, existing_latest, sl, root):
    m = re.search(r'(<div id="%s">.*?<tbody>)(.*?)(</tbody>)' % re.escape(tid), x, re.S)
    if not m:
        return x, None
    body = m.group(2)
    # 既存行のテーマ（日付 → テーマのセルHTML）
    old = {}
    for r in re.findall(r'<tr[^>]*>.*?</tr>', body, re.S):
        tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)
        if len(tds) >= 3:
            dm = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', tds[0])
            if dm:
                ds = '%04d-%02d-%02d' % tuple(int(v) for v in dm.groups())
                old[ds] = tds[1]
    rows = []
    for ds in sorted(files, reverse=True):
        if k != 'gov' and ds == existing_latest:
            continue                      # 最新号はポータルの一面から開くので表には載せない
        cell = old.get(ds)
        if not cell:
            t = sl.get((ds, k))
            if k == 'news':
                t2 = theme_from_file(root, files[ds], k)
                if isinstance(t2, list) and t2:
                    t = t2 if not t else [t] + t2[1:]
            if not t:
                t = theme_from_file(root, files[ds], k)
            cell = theme_cell(k, t) or '（テーマ未記載）'
        rows.append('<tr><td class="d">%s</td><td>%s</td><td><a href="%s" rel="noopener">開く</a></td></tr>'
                    % (jp(ds), cell, files[ds]))
    if not rows:
        return x, 0
    new = m.group(1) + '\n' + '\n'.join(rows) + '\n' + m.group(3)
    return x[:m.start()] + new + x[m.end():], len(rows)


def run(root):
    out = []
    p = os.path.join(root, 'index.html')
    if not os.path.exists(p):
        return ['!! バックナンバー: index.html が無い']
    x = read(p)
    # ポータルの最新号の日付
    latest = ''
    a0 = x.find('id="archive-data">')
    A = None
    if a0 > 0:
        a0 += len('id="archive-data">')
        a1 = x.find('</script>', a0)
        try:
            A = json.loads(x[a0:a1])
            latest = (A.get('latest') or {}).get('date', '')
        except Exception as ex:
            out.append('!! バックナンバー: archive-data を読めない（%s）' % ex)
    if not latest:
        latest = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()
    sl = search_lite_themes(root)
    summary = []
    allfiles = {}
    for tid, pre, k, key in TABLES:
        files = dated_files(root, pre)
        allfiles[key] = files
        x, n = rebuild_table(x, tid, pre, k, files, latest, sl, root)
        if n is None:
            summary.append('%s:枠なし' % k)
        else:
            summary.append('%s %d' % (k, n))
    for k, key in ARCHIVE_ONLY:
        allfiles[key] = dated_files(root, k)
    # archive-data の claude.ai のURLを、同じ日付のファイルがあればファイル名に直す
    fixed = 0
    if A is not None:
        ents = [A.get('latest')] + list(A.get('archive', []))
        for e in ents:
            if not isinstance(e, dict) or not e.get('date'):
                continue
            for key, files in allfiles.items():
                u = e.get(key, '')
                if u and 'claude.ai' in u and e['date'] in files:
                    e[key] = files[e['date']]
                    fixed += 1
        b0 = x.find('id="archive-data">') + len('id="archive-data">')
        b1 = x.find('</script>', b0)
        x = x[:b0] + json.dumps(A, ensure_ascii=False) + x[b1:]
    with open(p, 'w', encoding='utf-8') as f:
        f.write(x)
    out.append('OK: バックナンバー表をリポジトリのファイルから作り直し（%s／最新号 %s は除外・gov は含む／archive-data のURL %d件をファイル名に）'
               % ('・'.join(summary), latest, fixed))
    return out


if __name__ == '__main__':
    for line in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(line)
