# 変更履歴

| 日付 | バージョン・コミット | 種別 | 内容 | 関連Feature・ADR |
|---|---|---|---|---|
| 2026-08-01 | - | 初期作成 | 本プロジェクトのdocs記入例を作成（当時はexamples配下） | FEATURE-001 |
| 2026-08-03 | Pull Request #1でmainへ統合済み | 基盤整備 | スターターキットv0.2.0共通ルールを反映。プロジェクト固有文書をルート正本化。AGENTS.mdとCursor Rulesを同期。docs/06〜08を案件向けに調整。PRテンプレートと.env.exampleを追加。examples/quality-defect-rate-dashboardを削除 | FEATURE-001 / ADR-001 |
| 2026-08-03 | 未Commit | 名称変更 | 日本語正式名称を「仕入先品質トレンド」、英語表示名を「Supplier Quality Trend」、リポジトリ名を「supplier-quality-trend」、Python内部識別名を「supplier_quality_trend」に統一。サブタイトル、GitHub URL、ローカルパスも更新。業務仕様、MVP範囲、データ仕様、不良率定義は変更なし | FEATURE-001 |
| 2026-08-03 | 未Commit | MVP基本設計 | 現行不良率定義、単一仕入先・仕入先グループ、入力データ、最新13か月、前年同月比較、警告、Python静的生成、IIS配信、定期更新、Publicリポジトリのデータ取扱いを確定。未確定事項は明示して継続管理 | FEATURE-001 / ADR-001 / ADR-002 |
