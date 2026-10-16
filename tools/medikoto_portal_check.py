#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MediKoto：ポータル（index.html）の「日付」と「対象地域」の自動チェックと手当て（2026-10-16追加）。

見た目で得た信頼を内容の正確さで支えるための、毎朝の機械的な点検。やること：
 A. 日付の自動判定：今週の重要事項（#konshu）・一面の締切行（#tick）・締切表（#simekiri）の各行に締切日 data-due（ISO）を持たせ、
    「今日／明日／あとN日／締切済み」は閲覧日（日本時間）でブラウザが計算し直す（mk-reldate v1）。
    → 10月15日に作った号を16日に見ても「10/15 今日」のまま残らない。
 B. 締切表の重複統合：同じ公式URL、または同じ制度名（正規化）＋締切日の行が複数あれば1行にする。
    対象地域は具体的な方（都道府県）に統一し、確認日は新しい方、空欄（—）は相手の行から補う。題名末尾の「（○○県）」は地域列と重複するので外す。
 C. 一面：掲載件数の横に「今日まず読む3件」（無ければ勉強会ページの題から作る。作成側が置いていればそのまま）。
 D. 色変数：栄養（--nutr／--nutrbg）が :root に無ければ足す。
 F. スマホの見やすさ（mk-mobile v1）：640px以下でナビを「ページ一覧 ▾」、国の重要資料を1行に畳む。推進方針・予算のボタンは輪郭に。「件 掲載」を1行に。今週の重要事項の最後のタブを記憶。
 E. 検証：作成日の時点での不整合（「今日」「明日」の日付違い・過去日の締切行・data-days の食い違い・重複）を数えて報告する。
    報告は fix_sitenav.py の出力に「検証:」の行で出る。0件なら「検証: 不整合なし」。

何度実行しても結果は同じ（data-due はまだ無い所にだけ付け、スクリプトやCSSは1回だけ入れる）。
使い方：fix_sitenav.py から run(root) が呼ばれる。単独なら python3 tools/medikoto_portal_check.py .
"""
import os, re, sys, json, datetime, html as H
from urllib.parse import urlsplit

NUTR = {'c': '#D9603A', 'bg': '#FCEEE8', 'dc': '#F19B7C', 'dbg': '#2A1A14'}

RELDATE_JS = r'''<script>/* mk-reldate v1（2026-10-16）：締切の「今日／明日／あとN日／締切済み」を閲覧日（日本時間）で計算し直す */
(function(){
  function jstToday(){var d=new Date(Date.now()+9*3600*1000);return new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()));}
  function days(iso){var p=iso.split('-');if(p.length!==3){return null;}var t=Date.UTC(+p[0],+p[1]-1,+p[2]);return Math.round((t-jstToday().getTime())/86400000);}
  function lab(n){return n<0?'締切済み':(n===0?'今日':(n===1?'明日':'あと'+n+'日'));}
  function cls(n){return n<0?'done':(n<=7?'hot':(n<=30?'warn':''));}
  /* 今週の重要事項 */
  var ks=document.querySelectorAll('#konshu .kdue[data-due]');
  for(var i=0;i<ks.length;i++){var n=days(ks[i].getAttribute('data-due'));if(n===null){continue;}
    var pill=ks[i].querySelector('.dlpill');if(!pill){continue;}
    pill.className='dlpill '+(n<0?'done':(n<=1?'hot':(n<=7?'warn':'ok')));pill.textContent=(n<0?'期日超過':lab(n));}
  /* 一面の締切行 */
  var ts=document.querySelectorAll('#tick .it[data-due]'), left=0;
  for(var j=0;j<ts.length;j++){var m=days(ts[j].getAttribute('data-due'));if(m===null){continue;}
    var b=ts[j].querySelector('b');if(m<0){ts[j].hidden=true;continue;}left++;if(b){b.textContent=(m===0?'本日':(m===1?'明日':'あと'+m+'日'));}}
  var tk=document.getElementById('tick');
  if(tk&&ts.length&&!left&&!tk.querySelector('.it-none')){var sp=document.createElement('span');sp.className='it it-none';sp.textContent='7日以内の締切はありません（締切表をご確認ください）';tk.insertBefore(sp,tk.querySelector('a.go'));}
  /* 締切表：ピルの文言と日数だけ直す（行の並べ替え・削除は毎朝の作成で行う） */
  var rs=document.querySelectorAll('#simekiri tr.p[data-due]'), near=0, past=0;
  for(var k=0;k<rs.length;k++){var q=days(rs[k].getAttribute('data-due'));if(q===null){continue;}
    rs[k].setAttribute('data-days',String(q));var p=rs[k].querySelector('.dlpill');
    if(p){p.className='dlpill '+cls(q);p.textContent=(q<0?'締切済み':(q===0?'本日':'あと'+q+'日'));}
    if(q<0){rs[k].classList.add('past');past++;}else{rs[k].classList.remove('past');if(q<=30){near++;}}}
  var cn=document.getElementById('cntN');if(cn&&rs.length){cn.textContent=String(near);}
  var pt=document.getElementById('pastTg');
  if(pt&&rs.length){var o=pt.getAttribute('data-open')||'',c=pt.getAttribute('data-close')||'';
    pt.setAttribute('data-open',o.replace(/\d+件/,past+'件'));pt.setAttribute('data-close',c.replace(/\d+件/,past+'件'));
    pt.textContent=(pt.getAttribute('aria-expanded')==='true'?pt.getAttribute('data-close'):pt.getAttribute('data-open'));pt.hidden=(past===0);}
})();
</script>'''

TOP3_CSS = '''<style>/* 一面「今日まず読む3件」v1（2026-10-16） */
.ed-statrow{display:flex;flex-wrap:wrap;align-items:flex-start;gap:.4rem 2rem;margin:.2rem 0 .8rem;}
.ed-statrow .ed-stat{margin:0;flex:none;}
.ed-top3{flex:1 1 20rem;min-width:0;border-left:1px solid var(--rule);padding-left:1.2rem;}
.ed-t3h{font-family:"Zen Kaku Gothic New",sans-serif;font-weight:700;font-size:.78rem;letter-spacing:.14em;color:var(--sub);margin:.15rem 0 .35rem;}
.ed-top3 ol{list-style:none;margin:0;padding:0;display:grid;gap:.3rem;}
.ed-top3 li{display:grid;grid-template-columns:auto 1fr;gap:.5rem;align-items:baseline;font-size:.9rem;line-height:1.55;color:var(--ink);}
.ed-top3 .t3n{font-family:"Zen Kaku Gothic New",sans-serif;font-weight:900;font-size:.9rem;color:var(--t3c,var(--acc));}
.ed-top3 .t3s{display:inline-block;font-size:.68rem;font-weight:700;color:var(--t3c,var(--acc));border:1px solid var(--t3c,var(--acc));border-radius:5px;padding:0 .4rem;margin-left:.4rem;vertical-align:.1em;white-space:nowrap;}
@media (max-width:640px){.ed-top3{border-left:0;padding-left:0;}}
</style>'''

MOBILE_BLOCK = r'''<style>/* mk-mobile v1（2026-10-16）：スマホで一面を最初の画面に／国の重要資料を輪郭に／件掲載の折り返し */
.hoshin a,.yosan a{background:transparent!important;color:#A85A14!important;border:1.5px solid #A85A14!important;font-weight:700;}
.yosan a{color:var(--acc)!important;border-color:var(--acc)!important;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .hoshin a{color:#E89A55!important;border-color:#E89A55!important;}
  :root:not([data-theme="light"]) .yosan a{color:#8FB7F4!important;border-color:#8FB7F4!important;}}
:root[data-theme="dark"] .hoshin a{color:#E89A55!important;border-color:#E89A55!important;}
:root[data-theme="dark"] .yosan a{color:#8FB7F4!important;border-color:#8FB7F4!important;}
.ed-stat span br{display:none;}
.ed-stat span .st2{margin-left:.35em;}
.mkfold{display:none;font-family:"Zen Kaku Gothic New",sans-serif;font-weight:700;font-size:.86rem;color:var(--acc);background:var(--paper,#FFFFFF);border:1.5px solid var(--acc);border-radius:999px;padding:.38rem 1rem;margin:.6rem 0 .4rem;cursor:pointer;width:100%;text-align:left;}
.mkfold .ar{float:right;}
.mkfold-gov{color:var(--sub);border-color:var(--rule);font-size:.8rem;padding:.3rem .9rem;margin:.5rem 0 0;}
@media (max-width:640px){
  .mkfold{display:block;}
  nav.sitenav.top{display:none;}
  nav.sitenav.top.open{display:grid;}
  #hoshin,#yosan{display:none;}
  .govopen #hoshin,.govopen #yosan{display:flex;}
}
</style>
<script>/* mk-mobile v1（2026-10-16）*/
(function(){
  var mq=window.matchMedia('(max-width:640px)');
  var nav=document.querySelector('nav.sitenav.top');
  if(nav){var b=document.createElement('button');b.type='button';b.className='mkfold';b.innerHTML='ページ一覧（15ページ）<span class="ar">▾</span>';
    b.setAttribute('aria-expanded','false');nav.parentNode.insertBefore(b,nav);
    b.addEventListener('click',function(){var o=nav.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');b.querySelector('.ar').textContent=o?'▴':'▾';});}
  var h=document.getElementById('hoshin');
  if(h){var g=document.createElement('button');g.type='button';g.className='mkfold mkfold-gov';g.innerHTML='国の重要資料（医療情報化推進方針・令和9年度予算）<span class="ar">▾</span>';
    g.setAttribute('aria-expanded','false');h.parentNode.insertBefore(g,h);
    g.addEventListener('click',function(){var o=h.parentNode.classList.toggle('govopen');g.setAttribute('aria-expanded',o?'true':'false');g.querySelector('.ar').textContent=o?'▴':'▾';});}
  var st=document.querySelector('.ed-stat span');if(st&&/件<br/i.test(st.innerHTML)){st.innerHTML='件<span class="st2">掲載</span>';}
  /* 今週の重要事項：最後に見たタブを覚える */
  try{var tabs=document.querySelectorAll('.ktabs [role="tab"]');var saved=localStorage.getItem('mk-ktab');
    for(var i=0;i<tabs.length;i++){tabs[i].addEventListener('click',function(){try{localStorage.setItem('mk-ktab',this.id);}catch(e){}});}
    if(saved){var sb=document.getElementById(saved);if(sb&&sb.getAttribute('aria-selected')!=='true'){sb.click();}}}catch(e){}
})();
</script>'''

SECCOL = {'国の医療DX': '--gov', '看護': '--nurs', '医師': '--doc', '薬剤師': '--pharm', '相談支援・連携': '--conn',
          '病院SE': '--se', '栄養': '--nutr', '診療報酬': '--reim', '海外': '--ovs', '海外DX': '--ovs'}
TOP3_PREF = ('国の医療DX', '病院SE', '診療報酬')


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def jst_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()


def to_iso(md, base):
    m = re.match(r'(\d{1,2})/(\d{1,2})', md)
    if not m:
        return None
    mo, d = int(m.group(1)), int(m.group(2))
    try:
        dt = datetime.date(base.year, mo, d)
    except ValueError:
        return None
    if (dt - base).days > 200:
        dt = datetime.date(base.year - 1, mo, d)
    elif (base - dt).days > 200:
        dt = datetime.date(base.year + 1, mo, d)
    return dt.isoformat()


def strip(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def norm_url(u):
    s = urlsplit(u)
    return (s.netloc.lower().replace('www.', '') + s.path.rstrip('/')).lower()


def norm_title(s):
    s = re.sub(r'（[^）]*）|\([^)]*\)', '', s)
    s = re.sub(r'令和\d+年度|R\d+|第\d+回|要望調査|公募|申請|締切|\s', '', s)
    return s


# ---------- A. data-due ----------
def add_due(t, base, report):
    def k_due(m):
        iso = to_iso(m.group('md'), base)
        if not iso:
            return m.group(0)
        n = (datetime.date.fromisoformat(iso) - base).days
        lab = m.group('lab')
        if (lab == '今日' and n != 0) or (lab == '明日' and n != 1) or (lab.startswith('あと') and lab != 'あと%d日' % n):
            report.append('今週の重要事項：「%s」の日付が作成日と違う（%s→直した）' % (lab, iso))
        # 静的な表示も作成日基準で正しくしておく（JSが動かない環境のため）
        lab2 = '期日超過' if n < 0 else ('今日' if n == 0 else ('明日' if n == 1 else 'あと%d日' % n))
        cls2 = 'done' if n < 0 else ('hot' if n <= 1 else ('warn' if n <= 7 else 'ok'))
        return '<div class="kdue" data-due="%s"><span>%s</span><span class="dlpill %s">%s</span>' % (iso, m.group('md'), cls2, lab2)
    t = re.sub(r'<div class="kdue"><span>(?P<md>\d{1,2}/\d{1,2})</span><span class="dlpill [a-z]*">(?P<lab>[^<]*)</span>', k_due, t)
    # すでに data-due が付いている行も、静的な表示（今日／あとN日）を作成日基準に直す（2026-10-16：10/15「今日」が残った）
    def k_fix(m):
        iso, md, lab = m.group('iso'), m.group('md'), m.group('lab')
        try:
            n = (datetime.date.fromisoformat(iso) - base).days
        except ValueError:
            return m.group(0)
        lab2 = '期日超過' if n < 0 else ('今日' if n == 0 else ('明日' if n == 1 else 'あと%d日' % n))
        cls2 = 'done' if n < 0 else ('hot' if n <= 1 else ('warn' if n <= 7 else 'ok'))
        if lab != lab2:
            report.append('今週の重要事項：「%s」の日付が作成日と違う（%s→「%s」に直した）' % (lab, iso, lab2))
        return '<div class="kdue" data-due="%s"><span>%s</span><span class="dlpill %s">%s</span>' % (iso, md, cls2, lab2)
    t = re.sub(r'<div class="kdue" data-due="(?P<iso>\d{4}-\d{2}-\d{2})"><span>(?P<md>\d{1,2}/\d{1,2})</span><span class="dlpill [a-z]*">(?P<lab>[^<]*)</span>', k_fix, t)

    def tick_due(m):
        iso = to_iso(m.group(3), base)
        if not iso:
            return m.group(0)
        n = (datetime.date.fromisoformat(iso) - base).days
        if n < 0:
            report.append('一面の締切行：過去日の行がある（%s）' % m.group(3))
        lab = '本日' if n == 0 else ('明日' if n == 1 else ('あと%d日' % n if n > 1 else m.group(1)))
        if n >= 0 and lab != m.group(1):
            report.append('一面の締切行：「%s」が作成日と合わない（%s→%s）' % (m.group(1), m.group(3), lab))
        return '<span class="it" data-due="%s"><b>%s</b>%s%s' % (iso, lab, m.group(2), m.group(3))
    t = re.sub(r'<span class="it"><b>([^<]*)</b>([ \u3000]+)(\d{1,2}/\d{1,2})', tick_due, t)
    def tick_fix(m):
        try:
            n = (datetime.date.fromisoformat(m.group(1)) - base).days
        except ValueError:
            return m.group(0)
        lab = '本日' if n == 0 else ('明日' if n == 1 else ('あと%d日' % n if n > 1 else m.group(2)))
        if n >= 0 and lab != m.group(2):
            report.append('一面の締切行：「%s」が作成日と合わない（%s→%s・直した）' % (m.group(2), m.group(1), lab))
        return '<span class="it" data-due="%s"><b>%s</b>' % (m.group(1), lab)
    t = re.sub(r'<span class="it" data-due="(\d{4}-\d{2}-\d{2})"><b>([^<]*)</b>', tick_fix, t)

    def row_due(m):
        head, dd = m.group(1), m.group(2)
        iso = to_iso(dd, base)
        if not iso:
            return m.group(0)
        n = (datetime.date.fromisoformat(iso) - base).days
        dm = re.search(r'data-days="(-?\d+)"', head)
        if dm and int(dm.group(1)) != n:
            report.append('締切表：data-days が作成日と合わない（%s：%s→%d・直した）' % (dd, dm.group(1), n))
            head = head.replace(dm.group(0), 'data-days="%d"' % n, 1)
        if 'data-due=' not in head:
            if 'data-days=' in head:
                head = head.replace('data-days=', 'data-due="%s" data-days=' % iso, 1)
            else:
                head = head.replace('<tr class="p', '<tr data-due="%s" class="p' % iso, 1)
        return head + '<td data-l="締切"><span class="dd">' + dd
    t = re.sub(r'(<tr class="p[^"]*"[^>]*>)<td data-l="締切"><span class="dd">(\d{1,2}/\d{1,2}（.）)', row_due, t)
    return t


# ---------- B. 重複統合 ----------
def dedupe(t, base, report):
    sec = re.search(r'<section class="men" id="simekiri">.*?</section>', t, re.S)
    if not sec:
        return t, None, None
    s = sec.group(0)
    rows = list(re.finditer(r'<tr[^>]*class="p[^"]*"[^>]*>.*?</tr>', s, re.S))
    seen, groups = {}, []
    for r in rows:
        h = r.group(0)
        u = re.search(r'<td data-l="公式" class="off"><a href="([^"]+)"', h)
        tt = re.search(r'<span class="tt">(.*?)</span>', h, re.S)
        dd = re.search(r'<span class="dd">(\d{1,2}/\d{1,2})', h)
        dkey = dd.group(1) if dd else None
        ku = ('url', norm_url(u.group(1)), dkey) if u else None
        kt = ('title', norm_title(strip(tt.group(1))), dkey) if tt else None
        g = seen.get(ku) if ku else None
        if g is None and kt:
            g = seen.get(kt)
        if g is None:
            g = [r, []]
            groups.append(g)
        else:
            g[1].append(r)
            report.append('締切表：重複（同じ公式URLまたは制度名・締切日）：%s' % (strip(tt.group(1))[:60] if tt else '?'))
        if ku and ku not in seen:
            seen[ku] = g
        if kt and kt not in seen:
            seen[kt] = g

    def region_cell(h):
        m = re.search(r'<td data-l="地域">(.*?)</td>', h, re.S)
        return m.group(0) if m else ''

    def region_of(h):
        txt = strip(region_cell(h))
        return 'nat' if (not txt or txt.startswith('全国')) else 'pref'

    def check_of(h):
        c = re.search(r'確認 (\d{1,2}/\d{1,2})', h)
        return to_iso(c.group(1), base) if c else None

    for keep, dups in groups:
        if not dups:
            continue
        cands = [keep.group(0)] + [d.group(0) for d in dups]
        cands.sort(key=lambda h: (0 if region_of(h) == 'pref' else 1, -(int((check_of(h) or '0000-00-00').replace('-', '') or 0))))
        merged = cands[0]
        for other in cands[1:]:
            co, cb = check_of(other), check_of(merged)
            if co and (not cb or co > cb):
                merged = re.sub(r'確認 \d{1,2}/\d{1,2}', '確認 ' + re.search(r'確認 (\d{1,2}/\d{1,2})', other).group(1), merged, count=1)
            sm_b = re.search(r'<small>(.*?)</small>', merged)
            sm_o = re.search(r'<small>(.*?)</small>', other)
            if sm_o and not sm_b:
                merged = re.sub(r'(<span class="dd">\d{1,2}/\d{1,2}（.）)', lambda m: m.group(1) + sm_o.group(0), merged, count=1)
            tb = re.search(r'<span class="tt">(.*?)</span>', merged, re.S)
            to_ = re.search(r'<span class="tt">(.*?)</span>', other, re.S)
            if tb and to_ and len(strip(to_.group(1))) > len(strip(tb.group(1))):
                merged = merged.replace(tb.group(0), to_.group(0), 1)
            for col in ('対象', '補助率'):
                mb = re.search(r'<td data-l="%s">(.*?)</td>' % col, merged, re.S)
                mo = re.search(r'<td data-l="%s">(.*?)</td>' % col, other, re.S)
                if mb and mo and strip(mb.group(1)) in ('—', '——', '') and strip(mo.group(1)) not in ('—', '——', ''):
                    merged = merged.replace(mb.group(0), mo.group(0), 1)
        best = next((region_cell(h) for h in cands if region_of(h) == 'pref'), None)
        if best:
            merged = merged.replace(region_cell(merged), best, 1)
            merged = re.sub(r'data-region="[^"]*"', 'data-region="pref"', merged, count=1)
        merged = re.sub(r'<span class="tt">(.*?)\s*（[^）]*(?:都|道|府|県)）\s*</span>', r'<span class="tt">\1</span>', merged, count=1, flags=re.S)
        token = '<!--MERGED-%d-->' % id(keep)
        s = s.replace(keep.group(0), token, 1)
        for d in dups:
            s = s.replace(d.group(0), '', 1)
        s = s.replace(token, merged, 1)
    rows2 = re.findall(r'<tr[^>]*class="p[^"]*"[^>]*data-days="(-?\d+)"', s)
    near = sum(1 for d in rows2 if 0 <= int(d) <= 30)
    tot = len(rows2)
    if rows2:
        s = re.sub(r'id="cntN">\d+<', 'id="cntN">%d<' % near, s, count=1)
        s = re.sub(r'id="cntT">\d+<', 'id="cntT">%d<' % tot, s, count=1)
    return t[:sec.start()] + s + t[sec.end():], near, tot


# ---------- C. 今日まず読む3件 ----------
def study_topics(root, latest):
    p = os.path.join(root, 'study-%s.html' % latest)
    if not os.path.exists(p):
        return []
    t = read(p)
    out = []
    for m in re.finditer(r'<h2>([^<]+)</h2>.*?</header>\s*<p class="hh"[^>]*>(.*?)</p>', t, re.S):
        out.append((strip(m.group(1)), strip(m.group(2))))
    return out


def add_top3(t, root, latest, report):
    if 'ed-top3' in t:
        return t, 'あり'
    m = re.search(r'(<div class="ed-stat"><b>\d+</b><span>件<br>掲載</span></div>)', t)
    if not m:
        return t, '枠なし'
    tops = study_topics(root, latest)
    if not tops:
        report.append('一面：今日まず読む3件を作る材料（study-%s.html の題）が無い' % latest)
        return t, 'なし'
    chosen = [x for n in TOP3_PREF for x in tops if x[0] == n]
    for x in tops:
        if len(chosen) >= 3:
            break
        if x not in chosen:
            chosen.append(x)
    chosen = chosen[:3]
    lis = ''.join('<li style="--t3c:var(%s)"><span class="t3n">%d</span><span>%s<span class="t3s">%s</span></span></li>'
                  % (SECCOL.get(n, '--acc'), i + 1, H.escape(title), H.escape(n)) for i, (n, title) in enumerate(chosen))
    top3 = '<div class="ed-top3"><p class="ed-t3h">今日まず読む3件</p><ol>%s</ol></div>' % lis
    t = t[:m.start()] + '<div class="ed-statrow">' + m.group(1) + top3 + '</div>' + t[m.end():]
    if 'ed-statrow{' not in t:
        t = t.replace('<section class="men" id="search">', TOP3_CSS + '\n<section class="men" id="search">', 1) if '<section class="men" id="search">' in t else t.replace('</head>', TOP3_CSS + '\n</head>', 1)
    return t, '追加'


# ---------- D. 色変数 ----------
def ensure_vars(t):
    n = 0
    if '--nutr:' not in t:
        t2 = t.replace('--se:#8E7414;--sebg:#FBF3DA;', '--se:#8E7414;--sebg:#FBF3DA;--nutr:%s;--nutrbg:%s;' % (NUTR['c'], NUTR['bg']))
        t2 = re.sub(r'(--se:#E3C64F;--sebg:#[0-9A-Fa-f]{6};)', r'\1--nutr:%s;--nutrbg:%s;' % (NUTR['dc'], NUTR['dbg']), t2)
        n = t2.count('--nutr:')
        t = t2
    return t, n


def run(root):
    out, report = [], []
    p = os.path.join(root, 'index.html')
    if not os.path.exists(p):
        return ['!! ポータル検証: index.html が無い']
    t = read(p)
    latest = ''
    a0 = t.find('id="archive-data">')
    if a0 > 0:
        a0 += len('id="archive-data">')
        a1 = t.find('</script>', a0)
        try:
            latest = (json.loads(t[a0:a1]).get('latest') or {}).get('date', '')
        except Exception:
            pass
    try:
        base = datetime.date.fromisoformat(latest) if latest else jst_today()
    except ValueError:
        base = jst_today()
        latest = base.isoformat()
    t = add_due(t, base, report)
    t, near, tot = dedupe(t, base, report)
    t, top3 = add_top3(t, root, latest, report)
    t, nvars = ensure_vars(t)
    if os.path.exists(os.path.join(root, 'nutrition-%s.html' % latest)):
        t = t.replace('朝礼でそのまま読める8題・約10分。司会用の台本つき。', '朝礼でそのまま読める9題・約11分。司会用の台本つき。')
    if 'mk-reldate v1' not in t:
        t = t.replace('</body>', RELDATE_JS + '\n</body>', 1) if '</body>' in t else t + '\n' + RELDATE_JS
    # スマホの見やすさ（2026-10-16）：ナビと国の重要資料を1行に畳む・輪郭ボタン・「件 掲載」・今週の重要事項のタブを記憶
    if 'mk-mobile v1' not in t:
        t = t.replace('</body>', MOBILE_BLOCK + '\n</body>', 1) if '</body>' in t else t + '\n' + MOBILE_BLOCK
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)
    out.append('OK: ポータル検証（作成日 %s／締切表 %s／今日まず読む3件 %s／栄養の色変数 %s／日付は閲覧時に再計算）'
               % (base.isoformat(), ('30日以内 %d・全 %d 行' % (near, tot)) if tot is not None else '表なし', top3, '追加' if nvars else 'あり'))
    if report:
        for r in report:
            out.append('  検証: ' + r)
        out.append('  検証: 不整合 %d 件（上記）。重複は統合済み・日付の表示は閲覧時に直るが、作成側（毎朝のタスク）の修正対象として記録する' % len(report))
    else:
        out.append('  検証: 不整合なし')
    return out


if __name__ == '__main__':
    for line in run(sys.argv[1] if len(sys.argv) > 1 else '.'):
        print(line)
