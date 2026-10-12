#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ポータル（index.html）の日付行の下の2行の並びと色をそろえる（2026-10-13追加）。

2026-10-08 決定：
  ・「医療情報化推進方針」の行（p#hoshin）を、予算概算要求の行（p#yosan）の上に置く
  ・予算概算要求のボタンは推進方針と同じ金色（金茶）、ラベル文字の色も同じ
毎朝の作成タスクが前日のポータルを引き継ぐため、逆順のまま続いていた。何度実行しても同じ結果になる。

単独でも実行できる： python3 tools/medikoto_header_rows.py index.html
"""
import re, sys

GOLD_ID = 'yosan-gold-css'
GOLD_CSS = ('<style id="%s">/* 予算概算要求のボタンも推進方針と同じ金色（2026-10-08決定・2026-10-13反映） */\n'
            '.yosan a{color:#FFFFFF;background:#A85A14;border-color:#94500F;}\n'
            '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .yosan a{color:#10181E;background:#E89A55;border-color:#D78A46;}}\n'
            ':root[data-theme="dark"] .yosan a{color:#10181E;background:#E89A55;border-color:#D78A46;}\n'
            '</style>' % GOLD_ID)

ROW = r'<p class="%s" id="%s">.*?</p>'


def fix(h):
    """(新しいHTML, 変えた点のリスト) を返す。"""
    msgs = []
    y = re.search(ROW % ('yosan', 'yosan'), h, re.S)
    k = re.search(ROW % ('hoshin', 'hoshin'), h, re.S)
    if y and k and y.start() < k.start():
        ys, ks = y.group(0), k.group(0)
        if h[y.end():k.start()].strip() == '':          # 隣り合っている（ふつうの形）
            h = h[:y.start()] + ks + ys + h[k.end():]
        else:                                            # 離れているときは推進方針を予算の前へ移す
            h = h[:k.start()] + h[k.end():]
            h = h.replace(ys, ks + ys, 1)
        msgs.append('ポータル：医療情報化推進方針の行を予算概算要求の行の上へ移した')
    if y and GOLD_ID not in h:
        m = re.search(r'<style id="yosan-css">.*?</style>', h, re.S)
        if m:
            h = h[:m.end()] + '\n' + GOLD_CSS + h[m.end():]
        else:
            h = h.replace('</body>', GOLD_CSS + '\n</body>', 1) if '</body>' in h else h + '\n' + GOLD_CSS
        msgs.append('ポータル：予算概算要求のボタンを金色にした')
    return h, msgs


def run(path):
    h = open(path, encoding='utf-8').read()
    n, msgs = fix(h)
    if n != h:
        open(path, 'w', encoding='utf-8').write(n)
    return msgs


if __name__ == '__main__':
    for m in run(sys.argv[1] if len(sys.argv) > 1 else 'index.html') or ['変更なし']:
        print(m)
