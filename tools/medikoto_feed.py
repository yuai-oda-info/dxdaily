#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto feed v1（2026-10-05）
RSS（feed.xml）を毎朝作り直す。1日1件＝その日の号。直近10日ぶん。

やること（何度実行しても同じ結果になる）
  1. news-YYYY-MM-DD.html（ヘッドラインの保存版）を新しい順に10本読み、RSS 2.0 の feed.xml を書く。
     件名＝「M月D日（曜）号｜<勉強会で扱う1本目>ほかN件」
     リンク＝その日のヘッドライン保存版（日付つきURL。固定入口 news.html は指さない）
     本文＝勉強会で扱う8本（見出し・説明文・公表日・出典）＋コラムの題＋その日のページへのリンク
     pubDate＝その号の「作成日時」。lastBuildDate＝いちばん新しい号の作成日時（実行のたびに差分を出さない）
  2. ポータル（index.html）の <head> に RSS の自動検出用 <link rel="alternate"> を入れる（無ければ）。
  3. ポータルのショートカット行の末尾に「RSS配信」チップ（→ rss.html）を入れる（無ければ）。
  4. sitemap.xml に rss.html を載せる（無ければ）。feed.xml 自体は sitemap に入れない。

リンクには utm_source=rss を付ける（Googleアナリティクスで「RSSから来た人」を数えるため）。guid には付けない。
編集責任者の表示はサイトに置かない方針のため、managingEditor / webMaster は出さない。

tools/fix_sitenav.py（v11）から毎朝呼ばれる。単独でも実行できる： python3 tools/medikoto_feed.py .
"""
import os, re, sys, glob, datetime, html as H
from email.utils import format_datetime

BASE = 'https://yuai-oda-info.github.io/dxdaily/'
FEED_NAME = 'feed.xml'
FEED_URL = BASE + FEED_NAME
GUIDE = 'rss.html'
DAYS = 10                       # バックナンバーの「直近10日は開いたまま」とそろえる
UTM = 'utm_source=rss&utm_medium=feed&utm_campaign=medikoto_daily'
JST = datetime.timezone(datetime.timedelta(hours=9))
WD = '月火水木金土日'
CIRC = '①②③④⑤⑥⑦⑧⑨⑩'

CH_TITLE = 'MediKoto｜医療・介護のデジタル実践ポータル'
CH_DESC = ('医療・介護DXの毎日更新サイト。毎朝の号を1日1件でお届けします'
           '（ヘッドラインの件数、今日の勉強会で扱う8本、コラム、その日のページへのリンク）。')
COPY = '© 2026 Information Management Office, Oda Hospital (Kashima, Saga), Yuaikai Medical Corporation'
DISCLAIMER = 'MediKotoは医療・介護DXの学習・情報共有を目的とした非公式サイトです（公的機関とは関係ありません）。'

# その日のページ（日付つき保存版があるものだけ並べる）
DAY_PAGES = [
    ('news', 'ヘッドライン'), ('study', '今日の勉強会'), ('weekly-study', '事例DX'),
    ('gov', '国の医療DX'), ('cyber', 'サイバーDX'), ('infection', '感染症DX'),
    ('nursing', '看護'), ('doctors', '医師'), ('pharm', '薬剤師'),
    ('connect', '相談支援・連携'), ('hospitalit', '病院SE'), ('reimbursement', '診療報酬'),
    ('global', '海外DX'),
]

HEAD_LINK = ('<link rel="alternate" type="application/rss+xml" title="MediKoto（毎朝の号）" href="%s">' % FEED_URL)
RSS_ICON = ('<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true" '
            'style="vertical-align:-1px;margin-right:.3em"><circle cx="5" cy="19" r="2.4"/>'
            '<path d="M3 10.5a10.5 10.5 0 0 1 10.5 10.5h-3A7.5 7.5 0 0 0 3 13.5z"/>'
            '<path d="M3 3.5A17.5 17.5 0 0 1 20.5 21h-3A14.5 14.5 0 0 0 3 6.5z"/></svg>')
CHIP = '<a href="%s" class="sc-rss">%sRSS配信</a>' % (GUIDE, RSS_ICON)


def today_jst():
    return datetime.datetime.now(JST).date()


def txt(s):
    """タグを外して空白を詰めた素の文字列"""
    s = re.sub(r'<[^>]+>', '', s or '')
    return re.sub(r'\s+', ' ', H.unescape(s)).strip()


def u(path, frag=''):
    return BASE + path + '?' + UTM + (('#' + frag) if frag else '')


def made_at(src, d):
    m = re.search(r'作成日時：\s*(\d{4})年(\d{1,2})月(\d{1,2})日（.）\s*(\d{1,2}):(\d{2})', src)
    if m:
        y, mo, da, hh, mi = map(int, m.groups())
        return datetime.datetime(y, mo, da, hh, mi, tzinfo=JST)
    return datetime.datetime(d.year, d.month, d.day, 6, 0, tzinfo=JST)


def parse_news(path):
    """ヘッドライン保存版から、節・行・勉強会の8本・コラムの題を取り出す"""
    src = open(path, encoding='utf-8').read()
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', src[src.find('<body'):], flags=re.S)
    secs = []
    marks = list(re.finditer(r'<p class="secband" id="([^"]+)"[^>]*>(.*?)</p>', body, re.S))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        chunk = body[m.end():end]
        head = m.group(2)
        name = txt(re.sub(r'<small>.*?</small>', '', head, flags=re.S))
        name = re.sub(r'^\d+\s*', '', name)
        rows = []
        for r in re.finditer(r'<div class="hlrow">(.*?)(?=<div class="hlrow">|<p class="secband"|</section>|$)', chunk, re.S):
            rh = r.group(1)
            t = re.search(r'<p class="hltitle">(.*?)</p>', rh, re.S)
            if not t:
                continue
            a = re.search(r'<a [^>]*>(.*?)</a>', t.group(1), re.S)
            title = txt(a.group(1)) if a else txt(t.group(1))
            meta = re.search(r'<p class="hlmeta">(.*?)</p>', rh, re.S)
            meta = txt(meta.group(1)) if meta else ''
            pub = re.search(r'公表日：\s*(\d{4}-\d{2}-\d{2})', meta)
            srcn = re.search(r'出典：\s*(.*?)(?:\s*▸|$)', meta)
            geo = re.search(r'<span class="geo2?">(.*?)</span>', t.group(1))
            sm = re.search(r'<p class="hlsum">(.*?)</p>', rh, re.S)
            rows.append({
                'title': title,
                'study': 'badge-study' in t.group(1),
                'pub': pub.group(1) if pub else '',
                'src': srcn.group(1).strip() if srcn else '',
                'geo': txt(geo.group(1)) if geo else '',
                'sum': txt(sm.group(1)) if sm else '',
            })
        secs.append({'id': m.group(1), 'name': name, 'rows': rows})
    cols = []
    for k in ('sec-col1', 'sec-col2', 'sec-col3'):
        m = re.search(r'<section id="%s">\s*<h2>(.*?)</h2>.*?<p class="coltheme">(.*?)</p>' % k, body, re.S)
        if m:
            cols.append((txt(m.group(1)), txt(m.group(2))))
    return src, secs, cols


def study_titles(path):
    """その号で勉強会が扱った見出しの集合（前日と同じ件名を避けるのに使う）"""
    try:
        _, secs, _ = parse_news(path)
    except Exception:
        return set()
    return {lead_key(r['title']) for s in secs for r in s['rows'] if r['study']}


def lead_key(t):
    """同じ話題かどうかの目安＝見出しの先頭6文字（「支払基金が改組、…」の言い換えも同じ扱いにする）"""
    return re.sub(r'[\s、。「」（）・,]', '', t)[:6]


def build_item(root, path, prev_titles=frozenset()):
    ds = re.search(r'news-(\d{4}-\d{2}-\d{2})\.html$', path).group(1)
    d = datetime.date.fromisoformat(ds)
    src, secs, cols = parse_news(path)
    when = made_at(src, d)
    fn = os.path.basename(path)
    total = sum(len(s['rows']) for s in secs)
    picks = [(s, r) for s in secs for r in s['rows'] if r['study']]
    day = '%d月%d日（%s）号' % (d.month, d.day, WD[d.weekday()])

    if picks:
        # 件名は、前の号の勉強会で扱っていない最初の1本（無ければ1本目）。毎日同じ件名が並ぶのを防ぐ
        fresh = [r for s, r in picks if lead_key(r['title']) not in prev_titles]
        lead = (fresh or [picks[0][1]])[0]['title']
        title = '%s｜%sほか%d件' % (day, lead, max(total - 1, 0)) if total > 1 else '%s｜%s' % (day, lead)
    elif total:
        lead = secs[0]['rows'][0]['title'] if secs and secs[0]['rows'] else ''
        title = '%s｜%sほか%d件' % (day, lead, total - 1)
    else:
        m = re.search(r'<title>(.*?)</title>', src, re.S)
        title = '%s｜%s' % (day, txt(m.group(1)) if m else 'MediKoto')

    # 短い説明（description）：本文を表示しないリーダー向け
    plain = []
    if total:
        plain.append('きょうのヘッドライン%d件。' % total)
    if picks:
        plain.append('今日の勉強会で扱う%d本：' % len(picks) +
                     '　'.join('%s%s' % (CIRC[i] if i < len(CIRC) else '・', r['title']) for i, (s, r) in enumerate(picks)))
    description = ''.join(plain) or 'MediKoto %s' % day

    # 本文（content:encoded）
    e = H.escape
    out = []
    if total:
        bysec = '・'.join('%s %d' % (e(s['name']), len(s['rows'])) for s in secs if s['rows'])
        out.append('<p>きょうのヘッドラインは<b>%d件</b>（%s）。%s</p>' % (
            total, bysec, 'このうち、今日の勉強会で扱う%d本です。' % len(picks) if picks else ''))
    for i, (s, r) in enumerate(picks):
        no = CIRC[i] if i < len(CIRC) else '・'
        tag = e(s['name']) + ('（%s）' % e(r['geo']) if r['geo'] else '')
        meta = '・'.join(x for x in [('公表日 ' + r['pub']) if r['pub'] else '', ('出典：' + e(r['src'])) if r['src'] else ''] if x)
        out.append('<p>%s <b>%s</b>｜<a href="%s">%s</a>%s%s</p>' % (
            no, tag, e(u(fn, s['id'])), e(r['title']),
            ('<br>' + e(r['sum'])) if r['sum'] else '',
            ('<br><small>%s</small>' % meta) if meta else ''))
    if cols:
        out.append('<p><b>コラム</b><br>' + '<br>'.join(
            '<a href="%s">%s</a>：%s' % (e(u(fn, 'sec-col%d' % (i + 1))), e(h2), e(th)) for i, (h2, th) in enumerate(cols)) + '</p>')
    links = []
    for key, label in DAY_PAGES:
        f = '%s-%s.html' % (key, ds)
        if os.path.exists(os.path.join(root, f)):
            links.append('<a href="%s">%s</a>' % (e(u(f)), label))
    if links:
        out.append('<p><b>この日のページ</b><br>' + '｜'.join(links) + '</p>')
    out.append('<p><small>%s 制度・締切・算定要件などは、必ず公式の通知・公募要領で最終確認してください。</small></p>' % DISCLAIMER)
    content = '\n'.join(out).replace(']]>', ']]&gt;')

    cats = []
    for s, r in picks:
        if s['name'] not in cats:
            cats.append(s['name'])
    return {
        'date': d, 'when': when, 'title': title, 'link': u(fn), 'guid': BASE + fn,
        'description': description, 'content': content, 'cats': cats,
    }


def build_feed(root, today=None):
    today = today or today_jst()
    files = []
    for f in glob.glob(os.path.join(root, 'news-2*.html')):
        m = re.search(r'news-(\d{4}-\d{2}-\d{2})\.html$', f)
        if m and datetime.date.fromisoformat(m.group(1)) <= today:
            files.append(f)
    files = sorted(files, reverse=True)
    items = []
    for i, f in enumerate(files[:DAYS]):
        prev = study_titles(files[i + 1]) if i + 1 < len(files) else set()
        items.append(build_item(root, f, prev))
    if not items:
        return None, 0
    e = H.escape
    last = max(it['when'] for it in items)
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
         'xmlns:content="http://purl.org/rss/1.0/modules/content/" '
         'xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">',
         '<channel>',
         '<title>%s</title>' % e(CH_TITLE),
         '<link>%s</link>' % BASE,
         '<atom:link href="%s" rel="self" type="application/rss+xml"/>' % FEED_URL,
         '<description>%s</description>' % e(CH_DESC),
         '<language>ja</language>',
         '<copyright>%s</copyright>' % e(COPY),
         '<lastBuildDate>%s</lastBuildDate>' % format_datetime(last),
         '<docs>https://www.rssboard.org/rss-specification</docs>',
         '<generator>MediKoto feed v1</generator>',
         '<sy:updatePeriod>daily</sy:updatePeriod>',
         '<sy:updateFrequency>1</sy:updateFrequency>']
    for it in items:
        x.append('<item>')
        x.append('<title>%s</title>' % e(it['title']))
        x.append('<link>%s</link>' % e(it['link']))
        x.append('<guid isPermaLink="true">%s</guid>' % e(it['guid']))
        x.append('<pubDate>%s</pubDate>' % format_datetime(it['when']))
        for c in it['cats']:
            x.append('<category>%s</category>' % e(c))
        x.append('<description>%s</description>' % e(it['description']))
        x.append('<content:encoded><![CDATA[%s]]></content:encoded>' % it['content'])
        x.append('</item>')
    x += ['</channel>', '</rss>', '']
    return '\n'.join(x), len(items)


def patch_portal(root):
    p = os.path.join(root, 'index.html')
    if not os.path.exists(p):
        return ['!! RSS: index.html が無い']
    h = open(p, encoding='utf-8').read()
    msgs, h0 = [], h
    head_end = h.find('</head>')
    if head_end > 0 and 'application/rss+xml' not in h[:head_end]:
        m = re.search(r'<link rel="canonical"[^>]*>', h[:head_end])
        at = m.end() if m else head_end
        h = h[:at] + '\n' + HEAD_LINK + h[at:]
        msgs.append('OK: RSS: ポータルの<head>に自動検出の行を入れた')
    m = re.search(r'<p class="shortcut">(.*?)</p>', h, re.S)
    if m and GUIDE not in m.group(1):
        h = h[:m.end() - 4] + CHIP + h[m.end() - 4:]
        msgs.append('OK: RSS: ショートカット行に「RSS配信」を入れた')
    elif not m:
        msgs.append('!! RSS: ショートカット行（p.shortcut）が見つからない')
    if h != h0:
        open(p, 'w', encoding='utf-8').write(h)
    return msgs


def patch_sitemap(root):
    p = os.path.join(root, 'sitemap.xml')
    if not (os.path.exists(p) and os.path.exists(os.path.join(root, GUIDE))):
        return ''
    x = open(p, encoding='utf-8').read()
    if (BASE + GUIDE + '<') in x:
        return ''
    x = x.replace('</urlset>', '<url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (BASE, GUIDE, today_jst().isoformat()))
    open(p, 'w', encoding='utf-8').write(x)
    return 'OK: RSS: sitemap に rss.html を追加'


def run(root):
    msgs = []
    xml, n = build_feed(root)
    if xml is None:
        return ['!! RSS: news-YYYY-MM-DD.html が見つからない（feed.xml は前回のまま）']
    p = os.path.join(root, FEED_NAME)
    old = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    if xml != old:
        open(p, 'w', encoding='utf-8').write(xml)
    msgs.append('OK: RSS: feed.xml %d件（%s）' % (n, '更新' if xml != old else '変更なし'))
    msgs += patch_portal(root)
    s = patch_sitemap(root)
    if s:
        msgs.append(s)
    return msgs


if __name__ == '__main__':
    for line in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(line)
