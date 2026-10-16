#!/usr/bin/env python3
"""MediKoto：日付行の「作成日時：YYYY年M月D日（曜）H:MM（日本時間）」を今（日本時間）に書き換える。

使い方: python3 tools/medikoto_stamp.py index.html news-2026-10-16.html ...
手で内容を直して同じURL／同じファイル名へ上書き公開するときは、公開の直前に必ずこれを通す
（portal-v3 スキル (g)：版が変われば作成日時も変わる。色・並びだけの修正でも同じ）。
置き換えるのは各ファイルの最初の1か所（日付行）だけ。search-data 内の他ページ本文は触らない。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from medikoto_portal_check import stamp_now  # noqa: E402


def main(paths):
    for p in paths:
        try:
            t = open(p, encoding='utf-8').read()
        except OSError as e:
            print('!!', p, e)
            continue
        t2, ok = stamp_now(t)
        if ok and t2 != t:
            open(p, 'w', encoding='utf-8').write(t2)
            print('OK 作成日時を更新:', p)
        elif ok:
            print('--', p, '作成日時はすでに今')
        else:
            print('--', p, '「作成日時」の日付行が無い（対象外）')


if __name__ == '__main__':
    main(sys.argv[1:] or ['index.html'])
