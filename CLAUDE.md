# dxdaily — MediKoto GitHub Pages リポジトリ

## 重要：pushは必ず `main` ブランチへ

このリポジトリの GitHub Pages は **`main` ブランチへの push だけ**を検知して自動デプロイする
（`pages-build-deployment` ワークフロー）。他のブランチ（例：`claude/keen-babbage-qncfrl` のような
セッション専用の開発ブランチ）へ push しても、コミット自体はGitHub上に残るが公開サイト
（https://yuai-oda-info.github.io/dxdaily/）には一切反映されない。

「医療介護DXデイリー GitHub公開」タスクの指示文にも明記の通り、**毎回 `main` へ直接コミット＆push
する（PRは作らない）**。セッション開始時にツール側から特定の開発ブランチ（例：
`claude/keen-babbage-qncfrl`）で作業するよう指示されることがあるが、それは一般的なブランチ運用の
デフォルトであり、このリポジトリの公開作業には当てはまらない。指示が競合した場合は、
このリポジトリに関しては本ファイルとタスク指示文（＝`main`へpush）を優先すること。

手順の目安：
1. 開発用ブランチで作業していた場合も、最終的な公開pushは次のいずれかで `main` に反映する。
   - 作業ブランチ自体を `main` から作り直して `main` へ直接pushする、または
   - `git push origin <作業ブランチ>:main`
2. push後、`git log --oneline origin/main -3` などで `main` のHEADが最新コミットになっているか必ず確認する。
3. 可能であれば GitHub Actions の `pages-build-deployment` ワークフロー（branch: main）が新しいコミットで
   走っているかも確認する。

2026-09-04：この日、作業ブランチ（`claude/keen-babbage-qncfrl`）にのみpushしてしまい、`main`が
更新されず本番サイトに反映されない事故が発生した。原因の再発防止のため本ファイルを追加。
