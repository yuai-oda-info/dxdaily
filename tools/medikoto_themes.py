#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto themes v1（2026-10-02）
サイバーDX・感染症DX とデータソース一覧の毎朝の処理。tools/fix_sitenav.py（v10）から呼ばれる。

やること（何度実行しても同じ結果になる）
  1. 全HTMLから出典URLを数え、data/sources.json の情報源ごとの「最後に使った日」を更新する。
  2. 一覧にない発信元が出典として2件以上使われたら、参照先として自動で追加する（追加日つき）。
  3. ポータル（index.html）に、THEME MAP の行・サイバーDX／感染症DXのバックナンバー2表・
     データソースのボタンとポップアップを差し込む（前回の差し込みは消してから入れ直す）。
  4. sources.html（データソース一覧の単独ページ）を作り直す。
  5. sitemap.xml に cyber.html／infection.html と保存版を載せる。
単独でも実行できる： python3 tools/medikoto_themes.py .
"""
import os, re, sys, json, glob, datetime, html as H

BASE = 'https://yuai-oda-info.github.io/dxdaily/'
WD = '月火水木金土日'
HERE = os.path.dirname(os.path.abspath(__file__))
MK0, MK1 = '<!-- MediKoto themes v1 -->', '<!-- /MediKoto themes v1 -->'
AUTO_GROUP = '自動で追加した参照先'

def today_jst():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()

def jdate(d):
    return '%d年%d月%d日（%s）' % (d.year, d.month, d.day, WD[d.weekday()])

# ---------------------------------------------------------------- ページの対応
PAGE_FILES = [  # キー, ファイル名の先頭（固定入口 X.html と保存版 X-YYYY-MM-DD.html）
    ('portal', ['index']), ('news', ['news']), ('study', ['study']), ('weekly', ['weekly-study']),
    ('gov', ['gov']), ('cyb', ['cyber']), ('inf', ['infection']), ('nurs', ['nursing']),
    ('doc', ['doctors']), ('pharm', ['pharmacists', 'pharm']), ('conn', ['connect']), ('se', ['hospitalit']),
    ('reim', ['reimbursement', 'gigikaishaku']), ('ovs', ['global']),
]
SEL = [  # キー, 表示名, 色, 一覧の掲載ページキー, URL, 更新, 補足
    ('portal', 'ポータル', 'sn-portal', 'portal', './', '毎日更新', 'ポータルは、補助金・締切表、学会・研修情報、資料室の出典です。日付つきの号を残していないため、数はその日のポータル1号分です。'),
    ('news', 'ヘッドライン', 'sn-news', 'hl', 'news.html', '毎日更新', 'その日に各ページへ載った記事を1枚に集めた面です。'),
    ('study', '今日の勉強会', 'sn-study', 'hl', 'study.html', '毎日更新', 'ヘッドラインの大項目から1件ずつ題を選んで作るため、確認先はヘッドラインと同じです。'),
    ('weekly', '事例DX', 'sn-study', None, 'weekly-study.html', '毎日更新（直近7日の事例）', '医師・薬剤師・相談支援・連携・病院SEの直近7日の実践事例から選びます。確認先はそれぞれのページと同じです。'),
    ('gov', '国の医療DX', 'sn-gov', 'gov', 'gov.html', '週1回見直し', '厚生労働省・デジタル庁などの一次情報だけで作っています。'),
    ('cyb', 'サイバーDX', 'sn-cyb', 'cyb', 'cyber.html', '週1回見直し・緊急の注意喚起は毎朝', '医療機関のサイバー対策の義務・点検・加算・支援と、公的機関の注意喚起の出典です。'),
    ('inf', '感染症DX', 'sn-inf', 'inf', 'infection.html', '週1回見直し', '発生届・サーベイランス・加算・医療措置協定の出典です。流行状況の数字は扱いません。'),
    ('nurs', '看護', 'sn-nurs', 'nurs', 'nursing.html', '毎日更新', ''),
    ('doc', '医師', 'sn-doc', 'doc', 'doctors.html', '毎日更新', '「研究で有効」「国内で導入」「承認」「保険適用」を分けて書くため、論文誌と行政の両方を使います。'),
    ('pharm', '薬剤師', 'sn-pharm', 'pharm', 'pharmacists.html', '毎日更新', ''),
    ('conn', '相談支援・連携', 'sn-conn', 'conn', 'connect.html', '毎日更新', ''),
    ('se', '病院SE', 'sn-se', 'se', 'hospitalit.html', '毎日更新', ''),
    ('reim', '診療報酬', 'sn-reim', 'reim', 'reimbursement.html', '毎日更新', '点数・要件・期限は厚生労働省と厚生局の原典で確かめ、民間の解説には「報道」のラベルを付けます。'),
    ('ovs', '海外DX', 'sn-ovs', 'ovs', 'global.html', '毎日更新', '各ページに載った海外の記事を集めた面です。'),
]
LABELS = {'公的': 'pub', '施設公式': 'fac', '企業発表': 'ent', '報道': 'med', '研究': 'res'}
PNAME = {'portal': 'ポータル', 'hl': 'ヘッドライン', 'gov': '国の医療DX', 'cyb': 'サイバーDX', 'inf': '感染症DX', 'nurs': '看護', 'doc': '医師',
         'pharm': '薬剤師', 'conn': '相談支援・連携', 'se': '病院SE', 'reim': '診療報酬', 'ovs': '海外DX'}
PCOL = {'portal': 'sn-portal', 'hl': 'sn-news', 'gov': 'sn-gov', 'cyb': 'sn-cyb', 'inf': 'sn-inf', 'nurs': 'sn-nurs', 'doc': 'sn-doc',
        'pharm': 'sn-pharm', 'conn': 'sn-conn', 'se': 'sn-se', 'reim': 'sn-reim', 'ovs': 'sn-ovs'}
SCAN_KEY_TO_PAGE = {'portal': 'portal', 'news': 'hl', 'study': 'hl', 'weekly': 'hl', 'gov': 'gov', 'cyb': 'cyb', 'inf': 'inf', 'nurs': 'nurs',
                    'doc': 'doc', 'pharm': 'pharm', 'conn': 'conn', 'se': 'se', 'reim': 'reim', 'ovs': 'ovs'}
E = lambda s: H.escape(s or '', quote=True)

def page_of(fn):
    b = fn[:-5]
    for key, pres in PAGE_FILES:
        for p in pres:
            if b == p or re.fullmatch(re.escape(p) + r'-\d{4}-\d{2}-\d{2}', b):
                return key, (datetime.date.fromisoformat(b[-10:]) if b != p else None)
    return None, None

def norm(dom):
    dom = dom.lower()
    return dom[4:] if dom.startswith('www.') else dom

# ---------------------------------------------------------------- 1. 数える
def case_media_urls(h):
    """事例データ（JSON）から、出典が報道・まとめのURLだけを返す。"""
    out = []
    for sid in ('j-data', 'j-feat'):
        m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % sid, h, re.S)
        if not m:
            continue
        try:
            rows = json.loads(m.group(1).replace('<\\/', '</'))
        except Exception:
            continue
        for r in rows:
            if isinstance(r, dict) and isinstance(r.get('src'), dict):          # j-data
                s = r['src']
                if s.get('l') in ('報道', 'まとめ') and str(s.get('u', '')).startswith('http'):
                    out.append(s['u'])
            elif isinstance(r, dict) and isinstance(r.get('src'), list):        # j-feat
                for s in r['src']:
                    if isinstance(s, list) and len(s) > 3 and s[0] in ('報道', 'まとめ') and str(s[3]).startswith('http'):
                        out.append(s[3])
    return out

def scan(root, ignore):
    pages = {k: {'files': 0, 'dom': {}} for k, _ in PAGE_FILES}
    doms = {}
    today = today_jst()
    for f in sorted(glob.glob(os.path.join(root, '*.html'))):
        key, d = page_of(os.path.basename(f))
        if not key:
            continue
        h = open(f, encoding='utf-8').read()
        h = re.sub(re.escape(MK0) + '.*?' + re.escape(MK1), '', h, flags=re.S)   # 差し込んだ一覧は数えない
        # 2026-10-10 事例データ（サイバーDX「事例と対策」の script#j-data / #j-feat）の出典のうち、
        # 報道・まとめだけを数える（各組織の発表ページは1件ずつの出典なので数えない）
        case_urls = case_media_urls(h)
        h = re.sub(r'<section class="men" id="c-jirei">.*?</section>', '', h, flags=re.S)
        h = re.sub(r'<script.*?</script>', '', h, flags=re.S)
        h = re.sub(r'<nav class="sitenav.*?</nav>', '', h, flags=re.S)
        pages[key]['files'] += 1
        for u in re.findall(r'href="(https?://[^"#]+)', h) + case_urls:
            m = re.match(r'https?://([^/:]+)', u)
            if not m:
                continue
            dom = norm(m.group(1))
            if any(dom == x or dom.endswith('.' + x) for x in ignore):
                continue
            u = u.split('?')[0]
            pages[key]['dom'].setdefault(dom, set()).add(u)
            info = doms.setdefault(dom, {'urls': set(), 'pages': set(), 'last': None, 'ulast': {}, 'case': False})
            if u in case_urls:
                info['case'] = True
            info['urls'].add(u)
            info['pages'].add(key)
            dd = d or today
            if info['last'] is None or dd > info['last']:
                info['last'] = dd
            if u not in info['ulast'] or dd > info['ulast'][u]:
                info['ulast'][u] = dd
    return pages, doms

# ---------------------------------------------------------------- 2. 情報源の更新（自動追加・最後に使った日）
def guess_label(dom):
    if re.search(r'(\.go\.jp|\.lg\.jp|\.gov$|\.gov\.[a-z]{2}$|\.nhs\.uk$|\.europa\.eu$|\.int$)', dom):
        return '公的'
    if dom in ('prtimes.jp', 'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'atpress.ne.jp', 'value-press.com'):
        return '企業発表'
    if re.search(r'(\.ac\.jp|\.edu$|hospital|clinic|byoin|\.hp\.)', dom):
        return '施設公式'
    if re.search(r'(jstage|pubmed|ncbi|springer|nature\.com|sciencedirect|wiley|jamanetwork|nejm|thelancet|bmj\.com|oup\.com)', dom):
        return '研究'
    if re.search(r'\.or\.jp$', dom):
        return '公的'
    return '報道'

def bare(u):
    return re.sub(r'^https?://(www\.)?', '', u).lower()

def item_urls(it, doms):
    """登録先が使われたURL（paths があれば、その先頭に合うURLだけ）。"""
    paths = [bare(x) for x in it.get('paths', [])]
    out = []
    for d in it.get('domains', []):
        if d not in doms:
            continue
        for u in doms[d]['urls']:
            if not paths or any(bare(u).startswith(x) for x in paths):
                out.append((d, u))
    return out

def apply_manual(root, data, today):
    """data/sources_manual.json（手で決めた追加・変更）を1回ずつ取り込む。取り込んだ id は data['manual_applied'] に残す。"""
    mp = os.path.join(root, 'data', 'sources_manual.json')
    if not os.path.exists(mp):
        return []
    man = json.load(open(mp, encoding='utf-8'))
    done = set(data.setdefault('manual_applied', []))
    msgs = []
    allit = lambda: [(g, it) for g in data['groups'] for it in g['items']]
    for dom, v in man.get('domain_names', {}).items():
        data.setdefault('domain_names', {})[dom] = v
    for op in man.get('ops', []):
        oid = op.get('id')
        if not oid or oid in done:
            continue
        if op['op'] == 'add':
            it = dict(op['item'])
            if any(x['name'] == it['name'] for _, x in allit()):
                done.add(oid)
                continue
            g = next((g for g in data['groups'] if g['name'] == op['group']), None)
            if g is None:
                g = {'name': op['group'], 'items': []}
                data['groups'].append(g)
            it.setdefault('status', 'active')
            it.setdefault('added', op.get('date', today.isoformat()))
            it.setdefault('added_reason', op.get('reason', ''))
            g['items'].append(it)
            data.setdefault('log', []).append({'date': it['added'], 'action': '追加', 'name': it['name'], 'reason': it['added_reason']})
            msgs.append('情報源を追加: %s' % it['name'])
        elif op['op'] == 'reword':   # 追加理由・記録の言い回しを直す（公開ページに出る文）
            for _, x in allit():
                if op['from'] in x.get('added_reason', ''):
                    x['added_reason'] = x['added_reason'].replace(op['from'], op['to'])
            for lg in data.get('log', []):
                if op['from'] in lg.get('reason', ''):
                    lg['reason'] = lg['reason'].replace(op['from'], op['to'])
        elif op['op'] == 'update':
            hit = [x for _, x in allit() if x['name'] == op['name']]
            for x in hit:
                x.update(op['set'])
                if op.get('rename'):
                    x['name'] = op['rename']
            if hit:
                data.setdefault('log', []).append({'date': op.get('date', today.isoformat()), 'action': '変更', 'name': op.get('rename') or op['name'], 'reason': op.get('reason', '')})
                msgs.append('情報源を変更: %s' % (op.get('rename') or op['name']))
        done.add(oid)
    data['manual_applied'] = sorted(done)
    return msgs

def update_registry(data, pages, doms, today):
    msgs = []
    covered = {}
    for g in data['groups']:
        for it in g['items']:
            for d in it.get('domains', []):
                covered[d] = it
    base = data.get('baseline_domains', {})
    if isinstance(base, list):
        base = {d: 0 for d in base}
    minu = data.get('rules', {}).get('auto_min_urls', 2)
    names = data.get('domain_names', {})
    auto = next((g for g in data['groups'] if g['name'] == AUTO_GROUP), None)
    for dom, info in sorted(doms.items(), key=lambda x: -len(x[1]['urls'])):
        if dom in covered:
            continue
        n = len(info['urls'])
        grow = n - base.get(dom, 0) if dom in base else n
        need = data.get('rules', {}).get('auto_min_urls_cases', 1) if info.get('case') else minu
        if grow < need:
            continue
        if auto is None:
            auto = {'name': AUTO_GROUP, 'items': []}
            data['groups'].append(auto)
        lab = (names.get(dom) or [None, None])[1] or guess_label(dom)
        pg = sorted({SCAN_KEY_TO_PAGE[k] for k in info['pages'] if k in SCAN_KEY_TO_PAGE})
        it = {'name': (names.get(dom) or [dom])[0], 'url': 'https://%s/' % dom, 'label': lab,
              'what': '出典として載せた記事から自動で追加しました（内容は週1回の見直しで書き足します）', 'freq': '随時',
              'pages': pg, 'domains': [dom], 'note': '', 'kind': '参照先', 'fixed': False, 'status': 'active', 'auto': True,
              'added': today.isoformat(), 'added_reason': '自動追加（出典に載せたURLの発信元）'}
        if info.get('case'):
            it['kind'] = '巡回先'
            it['what'] = '事例を探すときに見た報道・まとめとして自動で追加しました（内容は週1回の見直しで書き足します）'
            it['added_reason'] = '自動追加（事例一覧の出典に使った報道・まとめ）'
        auto['items'].append(it)
        covered[dom] = it
        data.setdefault('log', []).append({'date': today.isoformat(), 'action': '追加', 'name': it['name'], 'reason': it['added_reason']})
        msgs.append('情報源を自動追加: %s（%s・%d件）' % (it['name'], lab, n))
    for g in data['groups']:
        for it in g['items']:
            last = [doms[d]['ulast'][u] for d, u in item_urls(it, doms)]
            if last:
                it['last_used'] = max(last).isoformat()
    data['updated'] = today.isoformat()
    return msgs

def item_count(it, doms):
    return len(item_urls(it, doms))

# ---------------------------------------------------------------- 3. 一覧の中身（ポップアップと単独ページで共通）
def kind_chip(it):
    if it.get('status') == 'excluded':
        return '<span class="kd2 kd-x">除外</span>'
    if it.get('kind') == '巡回先':
        return '<span class="kd2 kd-p">巡回%s</span>' % ('・固定' if it.get('fixed') else '')
    return '<span class="kd2 kd-r">参照</span>'

def fragment(data, pages, doms, today, page_link_prefix=''):
    items = [it for g in data['groups'] for it in g['items'] if it.get('status', 'active') == 'active']
    n_all = len(items)
    n_daily = sum(1 for it in items if it.get('freq') == '毎日')
    n_urls = sum(len(v['urls']) for v in doms.values())
    names = data.get('domain_names', {})
    # 発信元の表示名（登録先の名前を優先）
    dn = {}
    for it in items:
        if it.get('paths'):
            continue
        for d in it.get('domains', []):
            dn.setdefault(d, (it['name'].split('（')[0], it['label']))
    for d, v in names.items():
        dn[d] = (v[0], v[1])
    # ページ選択
    btns, panels = [], []
    for k, label, col, rk, href, kind, note in SEL:
        c = pages.get(k, {'files': 0, 'dom': {}})
        urls = sum(len(v) for v in c['dom'].values())
        top = sorted(((d, len(v)) for d, v in c['dom'].items()), key=lambda x: -x[1])[:10]
        btns.append('<button type="button" class="pgb" data-k="%s" aria-pressed="%s" style="--pc:var(--%s)"><span class="pgb-n">%s</span><span class="pgb-c">%s件</span></button>'
                    % (k, 'true' if k == 'news' else 'false', col, label, format(urls, ',')))
        mx = top[0][1] if top else 1
        bars = ''.join('<li class="pgr" tabindex="0" data-tip="%s｜%d件｜%s"><span class="pgr-n">%s%s</span><span class="pgr-t"><i style="width:%.1f%%"></i></span><span class="pgr-v">%d</span></li>'
                       % (E(dn.get(d, (d, ''))[0]), n, d, E(dn.get(d, (d, ''))[0]),
                          ('<span class="sb sb-%s">%s</span>' % (LABELS[dn[d][1]], dn[d][1])) if d in dn and dn[d][1] in LABELS else '<span class="pgr-d">%s</span>' % d,
                          n / mx * 100, n) for d, n in top) or '<li class="pgreg-none">まだ出典がありません。</li>'
        reg = [it for it in items if rk and rk in it.get('pages', [])]
        regl = ''.join('<li><span class="pgreg-n">%s</span>%s<span class="sb sb-%s">%s</span><span class="fq fq-%s">%s</span></li>'
                       % (('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(it['url']), E(it['name']))) if it.get('url') else E(it['name']),
                          kind_chip(it), LABELS.get(it['label'], 'med'), it['label'], 'd' if it.get('freq') == '毎日' else 'w', it.get('freq', '')) for it in reg)
        if not reg:
            regl = '<li class="pgreg-none">このページ専用の確認先はありません（上の補足を参照）。</li>'
        files_txt = '%d号' % c['files'] if k not in ('portal', 'cyb', 'inf') else ('%d版' % c['files'] if k in ('cyb', 'inf') else '%d/%d号' % (today.month, today.day))
        panels.append('<div class="pgp" id="pg-%s" style="--pc:var(--%s)"%s>' % (k, col, '' if k == 'news' else ' hidden') +
                      '<div class="pgp-head"><h3 class="pgp-h">%s</h3><span class="pgp-kind">%s</span><a class="pg-open" href="%s%s">このページを開く →</a></div>' % (label, kind, page_link_prefix, href) +
                      '<div class="pgp-stats"><div><b>%s</b><span>出典に載せたURL</span></div><div><b>%d</b><span>発信元（ドメイン）</span></div><div><b>%s</b><span>集計した号</span></div></div>' % (format(urls, ','), len(c['dom']), files_txt) +
                      ('<p class="pgp-note">%s</p>' % note if note else '') +
                      '<div class="pgp-cols"><div><h4 class="pgp-h4">よく使っている発信元<span>実績・上位%d</span></h4><ol class="pgbars">%s</ol></div>' % (len(top), bars) +
                      '<div><h4 class="pgp-h4">決まった確認先<span>取材のルールで見る先・%d件</span></h4><ul class="pgreg">%s</ul></div></div></div>' % (len(reg), regl))
    # 全体の上位12
    top12 = sorted(((d, len(v['urls'])) for d, v in doms.items()), key=lambda x: -x[1])[:12]
    mx = top12[0][1] if top12 else 1
    bars12 = ''.join('<li class="dsb" tabindex="0" data-tip="%s｜%d件｜%s"><span class="dsb-n">%s%s</span><span class="dsb-track"><i style="width:%.1f%%"></i></span><span class="dsb-v">%s</span></li>'
                     % (E(dn.get(d, (d, ''))[0]), n, d, E(dn.get(d, (d, ''))[0]),
                        ('<span class="sb sb-%s">%s</span>' % (LABELS[dn[d][1]], dn[d][1])) if d in dn and dn[d][1] in LABELS else '',
                        n / mx * 100, format(n, ',')) for d, n in top12)
    # 最近の追加・変更（30日）
    since = today - datetime.timedelta(days=30)
    url_of = {it['name']: it.get('url') for it in items}
    by = {}
    for lg in data.get('log', []):
        if lg.get('date') and datetime.date.fromisoformat(lg['date']) >= since:
            by.setdefault((lg['date'], lg['action'], lg.get('reason', '')), []).append(lg['name'])
    ra = []
    for (d, act, why), nms in sorted(by.items(), key=lambda x: x[0][0], reverse=True):
        dd = datetime.date.fromisoformat(d)
        chips = ''.join(('<a class="ra-n" href="%s" target="_blank" rel="noopener">%s</a>' % (E(url_of[n]), E(n))) if url_of.get(n) else '<span class="ra-n">%s</span>' % E(n) for n in nms)
        ra.append('<li><div class="ra-h"><b>%d月%d日</b><span>%s：%s</span><em>%d件</em></div><div class="ra-list">%s</div></li>' % (dd.month, dd.day, act, E(why), len(nms), chips))
    # 登録している情報源の一覧
    groups = []
    gch = ['<button type="button" class="dsc" data-g="" aria-pressed="true">すべて<span>%d</span></button>' % n_all]
    gi = 0
    for g in data['groups']:
        rows = [it for it in g['items'] if it.get('status', 'active') == 'active']
        if not rows:
            continue
        gch.append('<button type="button" class="dsc" data-g="%d" aria-pressed="false">%s<span>%d</span></button>' % (gi, E(g['name']), len(rows)))
        rr = []
        for it in rows:
            cnt = item_count(it, doms)
            nm = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(it['url']), E(it['name']))) if it.get('url') else '<b>%s</b>' % E(it['name'])
            if it.get('added'):
                ad = datetime.date.fromisoformat(it['added'])
                if ad >= since:
                    nm += '<span class="addmk" title="%s">追加 %d/%d</span>' % (E(it.get('added_reason', '')), ad.month, ad.day)
            host = re.sub(r'^https?://(www\.)?', '', it.get('url') or '').split('/')[0] or '学会・施設ごとのサイト'
            pg = ''.join('<span class="dspg" style="--pc:var(--%s)"><i></i>%s</span>' % (PCOL[p], PNAME[p]) for p in it.get('pages', []) if p in PNAME)
            last = it.get('last_used')
            lastt = ('<span class="lu">最終 %d/%d</span>' % (int(last[5:7]), int(last[8:10]))) if last else ''
            txt = ' '.join([it['name'], it.get('what', ''), host, it.get('note', ''), it['label'], it.get('kind', '')] + [PNAME.get(p, '') for p in it.get('pages', [])])
            rr.append('<li class="dsr" data-g="%d" data-text="%s"><div class="dsr-name">%s<span class="dsr-host">%s</span>%s</div><div class="dsr-lab">%s<span class="sb sb-%s">%s</span></div><div class="dsr-what">%s</div><div class="dsr-freq"><span class="fq fq-%s">%s</span></div><div class="dsr-pages">%s</div><div class="dsr-cnt">%s%s</div></li>'
                      % (gi, E(txt), nm, E(host), ('<span class="dsr-note">%s</span>' % E(it['note'])) if it.get('note') else '', kind_chip(it), LABELS.get(it['label'], 'med'), it['label'],
                         E(it.get('what', '')), 'd' if it.get('freq') == '毎日' else 'w', it.get('freq', ''), pg,
                         ('<b>%s</b><span>URL</span>' % format(cnt, ',')) if cnt else '<span class="dsr-na">—</span>', lastt))
        groups.append('<section class="dsg" data-g="%d"><h3 class="dsg-h">%s<span>%d件</span></h3><div class="dsr-head" aria-hidden="true"><span>情報源</span><span>区分・種別</span><span>主に見ている情報</span><span>確認</span><span>主な掲載ページ</span><span>掲載URL</span></div><ul class="dsr-list">%s</ul></section>' % (gi, E(g['name']), len(rows), ''.join(rr)))
        gi += 1
    excl = [it for g in data['groups'] for it in g['items'] if it.get('status') == 'excluded']
    excl_html = ''
    if excl:
        excl_html = '<details class="ds-excl"><summary>除外した情報源 %d件</summary><ul>%s</ul></details>' % (len(excl), ''.join('<li><b>%s</b>　%s（%s）</li>' % (E(it['name']), E(it.get('excluded_reason', '')), it.get('excluded', '')) for it in excl))
    cap = data.get('rules', {}).get('private_cap', '2〜3.5割（上限3.5割）')
    return ''.join([
        '<p class="ds-eyebrow">DATA SOURCES</p><h1 class="ds-h1">MediKotoが情報を集めている先</h1>',
        '<p class="ds-lead">MediKotoの記事は、ここに挙げた公開情報から作っています。国や公的機関の一次情報を優先し、業界メディアや企業の発表は話題を見つけるために使います。掲載するときは、実際に開いて確かめたページにだけリンクし、各記事に出典と公表日を付けています。</p>',
        '<div class="ds-stats"><div class="dst"><b>%d</b><span>登録している情報源</span></div><div class="dst"><b>%d</b><span>うち毎日確認する先</span></div><div class="dst"><b>%s</b><span>出典に載せたURL<br><small>全ての号・重複なし</small></span></div><div class="dst"><b>%d</b><span>URLの発信元（ドメイン）</span></div></div>' % (n_all, n_daily, format(n_urls, ','), len(doms)),
        '<section class="ds-sec" id="by-page"><h2 class="ds-h2">ページごとの参照先<span>ページを選ぶと、そのページが使っている情報源が出ます</span></h2>',
        '<div class="pgsel" role="group" aria-label="ページを選ぶ">%s</div>' % ''.join(btns), ''.join(panels),
        '<p class="ds-note">「よく使っている発信元」は、そのページの全ての号から出典として載せたURLを数えたものです（同じURLは何度載せても1件）。「決まった確認先」は、取材のルールで見に行く先です。</p></section>',
        '<section class="ds-sec"><h2 class="ds-h2">全ページの合計<span>出典に載せたURLが多い発信元・上位12</span></h2><ol class="dsbars" aria-label="出典に載せたURLの数（上位12）">%s</ol>' % bars12,
        '<p class="ds-note">MediKotoの全ページ・全ての号から数えています。厚生労働省は、報道発表・審議会資料・通知など省のサイト全体の合計です。</p></section>',
        '<section class="ds-sec"><h2 class="ds-h2">見る先と使い方の決まり</h2><div class="ds-rules">'
        '<div><b>巡回先と参照先</b><p><span class="kd2 kd-p">巡回</span>は決まった頻度で必ず見に行く先、<span class="kd2 kd-r">参照</span>は記事を追ううちに行き当たったときに使う先です。参照先の新着は週1回の見直しで確認します。急ぎや法令に関わる<span class="kd2 kd-p">巡回・固定</span>の先は、使用実績にかかわらず見続けます。</p></div>'
        '<div><b>一次情報を最優先</b><p>制度・点数・安全性は、厚生労働省・PMDA・厚生局などの原典で確かめてから書きます。確かめられない数値は載せません。</p></div>'
        '<div><b>民間情報は「見つける」ために</b><p>業界メディアや企業の発表は、新しい話題を見つける入口です。効果や精度の数字は、施設の資料や論文で裏を取ります。民間情報は全体の%sにしています。国の医療DX・診療報酬・医薬品の安全性は、公的な一次情報が中心です。</p></div>' % cap +
        '<div><b>新しい情報源は自動で追加</b><p>毎朝の更新で、出典に載せたURLの発信元をこの一覧と照らし合わせ、載っていない先が2件以上使われたら自動で追加します（追加日つき）。閉鎖・誤りが続いた先などは「除外」にして、見に行かず出典にも使いません。</p></div></div></section>',
        ('<section class="ds-sec" id="ds-added"><h2 class="ds-h2">最近の追加・変更<span>直近30日</span></h2><ul class="ralist">%s</ul></section>' % ''.join(ra)) if ra else '',
        '<section class="ds-sec" id="ds-list"><h2 class="ds-h2">登録している情報源の一覧<span id="ds-count">%d件を表示</span></h2>' % n_all,
        '<div class="ds-filter"><div class="mkf-box ds-q"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4.2-4.2"/></svg><input id="ds-q" type="search" placeholder="名前・情報・ページ名で絞り込む（例：脆弱性、看護、補助金）" aria-label="情報源を絞り込む"></div>',
        '<div class="ds-chips" role="group" aria-label="種類で絞り込む">%s</div></div>' % ''.join(gch),
        ''.join(groups), excl_html,
        '<p class="ds-empty" id="ds-empty" hidden>条件に合う情報源がありません。絞り込みを外してください。</p></section>',
        '<p class="ds-foot">この一覧は毎朝の更新で作り直しています（最終更新：%s）。所在の確認だけに使う個人のブログや、書き方の参考にしている媒体は載せていません。情報源の追加や誤りのご連絡は、ポータル奥付の「情報提供・連携」からお願いします。</p>' % jdate(today),
    ])

# ---------------------------------------------------------------- 4. ポータルへの差し込み
def asset(name):
    p = os.path.join(HERE, name)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''

def cyber_alert(root, today):
    p = os.path.join(root, 'cyber.html')
    if not os.path.exists(p):
        return None
    m = re.search(r'class="alertband"[^>]*data-pub="(\d{4}-\d{2}-\d{2})"[^>]*data-until="(\d{4}-\d{2}-\d{2})"', open(p, encoding='utf-8').read())
    if not m:
        return None
    pub, until = datetime.date.fromisoformat(m.group(1)), datetime.date.fromisoformat(m.group(2))
    return (pub, until) if today <= until else None

def bn_rows(root, prefix, fixed_name, first_text):
    rows = []
    for f in sorted(glob.glob(os.path.join(root, prefix + '-2*.html')), reverse=True):
        ds = os.path.basename(f)[len(prefix) + 1:len(prefix) + 11]
        d = datetime.date.fromisoformat(ds)
        m = re.search(r'<meta name="mk-change" content="([^"]*)"', open(f, encoding='utf-8').read())
        rows.append('<tr><td class="d">%s</td><td>%s</td><td><a href="%s" rel="noopener">開く</a></td></tr>' % (jdate(d), m.group(1) if m else '保存版', os.path.basename(f)))
    if not rows:
        rows = ['<tr><td class="d">—</td><td>%s</td><td><a href="%s" rel="noopener">開く</a></td></tr>' % (first_text, fixed_name)]
    return rows

def portal(root, frag, today):
    p = os.path.join(root, 'index.html')
    if not os.path.exists(p):
        return '!! テーマ: index.html が無い'
    x = open(p, encoding='utf-8').read()
    x = re.sub(re.escape(MK0) + '.*?' + re.escape(MK1) + r'\n?', '', x, flags=re.S)
    x = re.sub(r'<!--mk-theme-row-->.*?<!--/mk-theme-row-->\n?', '', x, flags=re.S)
    x = re.sub(r'<!--mk-theme-bn-->.*?<!--/mk-theme-bn-->\n?', '', x, flags=re.S)
    x = re.sub(r'<a class="ds-ghost"[^>]*>.*?</a>', '', x, flags=re.S)
    notes = []
    # THEME MAP の行（国が進める医療DX の直下）
    al = cyber_alert(root, today)
    alert = ('<span class="ed-alert" data-until="%s">緊急 %d/%d</span>' % (al[1].isoformat(), al[0].month, al[0].day)) if al else ''
    row = ('<!--mk-theme-row--><div class="row themerow" id="themes"><p class="ed-rk" style="color:var(--cyb)">THEME MAP</p><p class="ed-rt" style="font-size:1.2rem">テーマで深掘り</p>'
           '<p class="ed-th"><a href="cyber.html" style="--e:var(--cyb)">サイバーDX</a>%s<span class="ed-thd">チェックリスト19項目・注意喚起</span></p>'
           '<p class="ed-th"><a href="infection.html" style="--e:var(--inf)">感染症DX</a><span class="ed-thd">発生届・サーベイランス・加算</span></p></div><!--/mk-theme-row-->') % alert
    m = re.search(r'<a class="row" id="gov"[^>]*>.*?</a>', x, re.S)
    if m:
        x = x[:m.end()] + '\n' + row + x[m.end():]
    else:
        notes.append('!! テーマ: 一面に「国が進める医療DX」の行が無い')
    # バックナンバー2表（国の医療DXの表の下）
    def blk(cls, title, bid, lead, rows):
        return ('<div class="bnc %s"><details class="bnfold"><summary><h4 class="sub4">%sのバックナンバー</h4></summary>'
                '<p style="font-size:.78rem;color:var(--mut);margin:.1rem 0 .4rem">%s</p><div id="%s"><div class="tablewrap"><table>'
                '<thead><tr><th>日付</th><th>変わったこと</th><th>リンク</th></tr></thead><tbody>%s</tbody></table></div></div></details></div>') % (cls, title, lead, bid, ''.join(rows))
    bn = ('<!--mk-theme-bn-->' +
          blk('bnc-cyber', 'MediKoto Cyber（サイバーDX）', 'bn-cyber', '内容が動いた週だけ、その時点の版を保存しています（毎週の保存はしません）。最新版は共通ナビの「サイバーDX」からどうぞ。', bn_rows(root, 'cyber', 'cyber.html', '公開中の最新版')) + '\n' +
          blk('bnc-infect', 'MediKoto Infection（感染症DX）', 'bn-infect', '内容が動いた週だけ、その時点の版を保存しています（毎週の保存はしません）。最新版は共通ナビの「感染症DX」からどうぞ。', bn_rows(root, 'infection', 'infection.html', '公開中の最新版')) +
          '<!--/mk-theme-bn-->')
    m = re.search(r'<div class="bnc bnc-gov">.*?</details></div>', x, re.S)
    if m:
        x = x[:m.end()] + '\n' + bn + x[m.end():]
    else:
        notes.append('!! テーマ: バックナンバーに国の医療DXの表が無い')
    x = x.replace('最新版は「MediKotoの4つの入口」の「国の医療DX」からどうぞ。', '最新版は共通ナビの「国の医療DX」からどうぞ。')
    # データソースのボタン（情報提供・連携の右。ごく薄く、マウスを重ねても変わらない）
    m = re.search(r'(<p class="contact-badge">.*?)(</p>)', x, re.S)
    if m:
        x = x[:m.start(2)] + '<a class="ds-ghost" id="ds-open" href="sources.html" aria-haspopup="dialog" aria-label="データソース一覧を開く">データソース</a>' + x[m.start(2):]
    else:
        notes.append('!! テーマ: 奥付の「情報提供・連携」が無い')
    # ポップアップ・CSS・スクリプト
    pop = (MK0 + '\n<style id="mk-themes-css">' + asset('medikoto_themes.css') + '</style>\n'
           '<div class="dsm" id="dsm" hidden><div class="dsm-back" data-close></div><div class="dsm-box" role="dialog" aria-modal="true" aria-labelledby="dsm-t">'
           '<div class="dsm-bar"><span class="dsm-t" id="dsm-t">データソース一覧</span><button type="button" class="dsm-x" id="dsm-x" data-close>閉じる<span aria-hidden="true">×</span></button></div>'
           '<div class="dsm-body" id="dsm-body" tabindex="-1"><div class="dsw dsw-pop">' + frag + '</div></div></div></div>'
           '<div class="ds-tip" id="ds-tip" role="tooltip" hidden></div>\n<script id="mk-themes-js">' + asset('medikoto_themes.js') + '</script>\n' + MK1)
    i = x.find('<style>/* MediKoto sitenav v')          # 共通ナビのCSSより前に置く（毎朝の並びを変えない）
    if i < 0:
        i = x.rfind('</body>')
    x = (x[:i] + pop + '\n' + x[i:]) if i >= 0 else (x + pop)
    open(p, 'w', encoding='utf-8').write(x)
    return notes or ['OK: ポータルにTHEME MAP・バックナンバー2表・データソースを差し込み%s' % ('（緊急 %d/%d を表示）' % (al[0].month, al[0].day) if al else '')]

def sources_page(root, frag, today):
    idx = os.path.join(root, 'index.html')
    logo = ''
    if os.path.exists(idx):
        m = re.search(r'data:image/png;base64,[A-Za-z0-9+/=]+', open(idx, encoding='utf-8').read())
        logo = m.group(0) if m else ''
    ga = ''  # GA4 はポータルと同じタグを写す（無ければ入れない）
    if os.path.exists(idx):
        g = re.search(r'<!-- Google tag \(gtag\.js\) -->.*?</script>\s*<script>.*?</script>', open(idx, encoding='utf-8').read(), re.S)
        ga = (g.group(0) + '\n') if g else ''
    doc = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + ga +
           '<title>MediKoto データソース一覧</title>\n<meta name="description" content="MediKotoが情報を集めている先と、ページごとの参照先の一覧（%s更新）">\n'
           '<link rel="canonical" href="%ssources.html">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&family=Zen+Kaku+Gothic+New:wght@700;900&display=swap">\n'
           '<style>' % (jdate(today), BASE) + asset('medikoto_themes_base.css') + asset('medikoto_themes.css') + '</style>\n</head>\n<body>\n<div class="wrap dsw">'
           '<header class="ds-bar"><a class="ds-logo" href="./"><img src="%s" alt="MediKoto（メディコト）　医療・介護のデジタル実践ポータル"></a>' % logo +
           '<div><div class="ds-copy"><span style="color:var(--medi)">医療と介護の、</span><span style="color:var(--koto)">今とこれからのこと。</span></div><div class="ds-brand">DX ／ AI ／ SECURITY ／ BCP</div></div><span class="ds-pill">データソース一覧</span></header>'
           '<p class="ds-backrow"><a class="ds-back" href="./">← ポータルに戻る</a></p>' + frag +
           '<p class="credit"><span class="cr1">DX / AI / SECURITY / BCP</span><br>© 2026 Information Management Office, Oda Hospital (Kashima, Saga), Yuaikai Medical Corporation<br>Produced by Shinichi Morikawa</p>'
           '<div class="ds-tip" id="ds-tip" role="tooltip" hidden></div></div>\n<script>' + asset('medikoto_themes.js') + '</script>\n</body>\n</html>\n')
    open(os.path.join(root, 'sources.html'), 'w', encoding='utf-8').write(doc)
    return 'OK: sources.html を作り直し'

def sitemap(root, today):
    p = os.path.join(root, 'sitemap.xml')
    if not os.path.exists(p):
        return ''
    x = open(p, encoding='utf-8').read()
    add = []
    for f in ['cyber.html', 'infection.html'] + [os.path.basename(f) for f in sorted(glob.glob(os.path.join(root, 'cyber-2*.html')) + glob.glob(os.path.join(root, 'infection-2*.html')))]:
        if not os.path.exists(os.path.join(root, f)) or (BASE + f + '<') in x:
            continue
        lm = f[-15:-5] if re.search(r'\d{4}-\d{2}-\d{2}\.html$', f) else today.isoformat()
        add.append('<url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (BASE, f, lm))
    if add:
        x = x.replace('</urlset>', '\n'.join(add) + '\n</urlset>')
        open(p, 'w', encoding='utf-8').write(x)
    return 'OK: sitemap に %d件追加' % len(add) if add else ''

# ---------------------------------------------------------------- 5. 学会・セミナー欄：終わった催しを外す
EV_KW = re.compile(r'申込|締切|受付|期限|期間|〆')
EV_DATE = re.compile(r'(?:(\d{4})年)?(?:(\d{1,2})月)?(\d{1,2})日')

def event_end(text, today):
    """催しの最終日（読めなければ None）。（）の中と、申込・締切などの語より後ろの日付は数えない。"""
    t = re.sub(r'（[^）]*）|\([^)]*\)', ' ', text)
    t = re.sub(r'^\s*(開催|会期|日時)[：:]\s*', '', t)
    y = m = None
    found = []
    for seg in t.split('／'):
        k = EV_KW.search(seg)
        part = seg[:k.start()] if k else seg
        for mm in EV_DATE.finditer(part):
            if mm.group(1):
                y = int(mm.group(1))
            if mm.group(2):
                m = int(mm.group(2))
            if m is None:
                continue
            yy = y
            if yy is None:   # 年が書いていないとき：今年。半年以上前になるなら来年
                yy = today.year
                try:
                    if datetime.date(yy, m, int(mm.group(3))) < today - datetime.timedelta(days=180):
                        yy += 1
                except ValueError:
                    continue
            try:
                found.append(datetime.date(yy, m, int(mm.group(3))))
            except ValueError:
                pass
    return max(found) if found else None

def _div_end(h, i):
    """h[i] から始まる <div ...> に対応する </div> の直後の位置。"""
    depth = 0
    for mm in re.finditer(r'<div\b|</div>', h[i:]):
        depth += 1 if mm.group(0) != '</div>' else -1
        if depth == 0:
            return i + mm.end()
    return -1

def prune_events(root, today):
    """ポータル・各ページの学会・セミナー欄（div.evcard）から、最終日が今日より前の催しを外す。
    対象は日付なしの固定入口と、今日の日付つきファイル（過去の号はその日の記録なので触らない）。"""
    fixed = {'index', 'news', 'study', 'weekly-study', 'gov', 'cyber', 'infection', 'nursing', 'doctors', 'pharmacists',
             'connect', 'hospitalit', 'reimbursement', 'global'}
    tag = today.isoformat()
    out = []
    for f in sorted(glob.glob(os.path.join(root, '*.html'))):
        b = os.path.basename(f)[:-5]
        if not (b in fixed or b.endswith('-' + tag)):
            continue
        h = open(f, encoding='utf-8').read()
        if 'class="evcard' not in h:
            continue
        removed = []
        pos = 0
        res = []
        for mm in re.finditer(r'<div class="evcard"[^>]*>', h):
            if mm.start() < pos:
                continue
            e = _div_end(h, mm.start())
            if e < 0:
                break
            card = h[mm.start():e]
            dm = re.search(r'<p class="evd">(.*?)</p>', card, re.S)
            end = event_end(re.sub(r'<[^>]+>', '', dm.group(1)), today) if dm else None
            res.append(h[pos:mm.start()])
            if end and end < today:
                tm = re.search(r'<p class="evt">(.*?)</p>', card, re.S)
                removed.append(re.sub(r'<[^>]+>', '', tm.group(1)) if tm else '?')
            else:
                open_tag = '<div class="evcard"%s>' % ((' data-end="%s"' % end.isoformat()) if end else '')
                res.append(open_tag + card[mm.end() - mm.start():])
            pos = e
        res.append(h[pos:])
        x = ''.join(res)
        if removed:
            # 列ごとの件数表記を合わせ、空になった列には一言を置く
            def fixcol(cm):
                col = cm.group(0)
                n = col.count('<div class="evcard')
                col = re.sub(r'(<span class="evnote">[^<]*?に)\d+(件</span>)', lambda z: z.group(1) + str(n) + z.group(2), col, count=1) if n else col
                if n == 0 and 'class="evnone"' not in col:
                    col = col[:-6] + '<p class="evnone" style="margin:.4rem 0;font-size:.85rem;color:var(--mut,#5E6B74)">開催が近い予定は確認中です（終わった催しは日付で自動的に外しています）。</p></div>'
                return col
            cols = []
            p0 = 0
            for cm in re.finditer(r'<div class="evcol[^"]*">', x):
                if cm.start() < p0:
                    continue
                e = _div_end(x, cm.start())
                if e < 0:
                    break
                cols.append(x[p0:cm.start()])
                cols.append(fixcol(re.match(r'.*', x[cm.start():e], re.S)))
                p0 = e
            cols.append(x[p0:])
            x = ''.join(cols)
            out.append('%s %d件（%s）' % (os.path.basename(f), len(removed), '・'.join(removed)))
        if x != h:
            open(f, 'w', encoding='utf-8').write(x)
    return ('OK: 学会・セミナー欄から終わった催しを外した：' + '／'.join(out)) if out else 'OK: 学会・セミナー欄に終わった催しは無し'

# ---------------------------------------------------------------- まとめて実行
def run(root):
    today = today_jst()
    sp = os.path.join(root, 'data', 'sources.json')
    if not os.path.exists(sp):
        return ['!! テーマ: data/sources.json が無い（データソースの処理を飛ばした）']
    data = json.load(open(sp, encoding='utf-8'))
    ev = prune_events(root, today)          # 先に外す（外した催しの出典は数えない）
    pages, doms = scan(root, data.get('ignore_domains', []))
    msgs = apply_manual(root, data, today)
    msgs += update_registry(data, pages, doms, today)
    json.dump(data, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    frag = fragment(data, pages, doms, today)
    msgs += portal(root, frag, today)
    msgs.append(sources_page(root, fragment(data, pages, doms, today), today))
    s = sitemap(root, today)
    if s:
        msgs.append(s)
    msgs.append(ev)
    return msgs

if __name__ == '__main__':
    for line in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(line)
