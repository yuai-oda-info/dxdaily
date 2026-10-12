#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ポータル（index.html）の日付行の下の2行の並びをそろえる（2026-10-13追加）。

2026-10-08 決定：
  ・「医療情報化推進方針」の行（p#hoshin）を、予算概算要求の行（p#yosan）の上に置く
  ・ボタンの色は2行で変える（予算概算要求＝元の青系、推進方針＝金色。2026-10-13「色が両方同じになってる」）
毎朝の作成タスクが前日のポータルを引き継ぐため、逆順のまま続いていた。何度実行しても同じ結果になる。

単独でも実行できる： python3 tools/medikoto_header_rows.py index.html
"""
import re, sys

GOLD_ID = 'yosan-gold-css'   # 2026-10-13に一度入れて取り消した金色の上書き（残っていたら外す）

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
    # 2026-10-13 予算概算要求のボタンを金色にしたが「色が両方同じになってる」で取り消し（色は元の青系のまま）
    g = re.search(r'\n?<style id="%s">.*?</style>' % GOLD_ID, h, re.S)
    if g:
        h = h[:g.start()] + h[g.end():]
        msgs.append('ポータル：予算概算要求のボタンの色を元に戻した')
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
