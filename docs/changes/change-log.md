# 変更履歴

| 日付 | バージョン・コミット | 種別 | 内容 | 関連Feature・ADR |
|---|---|---|---|---|
| 2026-08-01 | - | 初期作成 | 本プロジェクトのdocs記入例を作成（当時はexamples配下） | FEATURE-001 |
| 2026-08-03 | Pull Request #1でmainへ統合済み | 基盤整備 | スターターキットv0.2.0共通ルールを反映。プロジェクト固有文書をルート正本化。AGENTS.mdとCursor Rulesを同期。docs/06〜08を案件向けに調整。PRテンプレートと.env.exampleを追加。examples/quality-defect-rate-dashboardを削除 | FEATURE-001 / ADR-001 |
| 2026-08-03 | 未Commit | 名称変更 | 日本語正式名称を「仕入先品質トレンド」、英語表示名を「Supplier Quality Trend」、リポジトリ名を「supplier-quality-trend」、Python内部識別名を「supplier_quality_trend」に統一。サブタイトル、GitHub URL、ローカルパスも更新。業務仕様、MVP範囲、データ仕様、不良率定義は変更なし | FEATURE-001 |
| 2026-08-03 | 未Commit | MVP基本設計 | 現行不良率定義、単一仕入先・仕入先グループ、入力データ、最新13か月、前年同月比較、警告、Python静的生成、IIS配信、定期更新、Publicリポジトリのデータ取扱いを確定。未確定事項は明示して継続管理 | FEATURE-001 / ADR-001 / ADR-002 |
| 2026-08-04 | 未Commit | MVP実装 | Python標準ライブラリによるCSV・マスタ・エイリアス読込、検証、単一仕入先・グループ集計、原子的JSON生成、静的UI、Apache ECharts 6.1.0、run.bat、二重起動防止、匿名自動テストを実装 | FEATURE-001 / ADR-002 |
| 2026-08-04 | 未Commit | 入力検証仕様 | 数量不正行を集計対象外とし警告詳細を保持。有効行0件時の更新失敗、出荷数0の算出不可表示、`DEFECTIVE_RATE`照合の絶対許容差`1E-12`を実装 | FEATURE-001 |
| 2026-08-04 | 未Commit | 数量整数仕様 | 実データ調査を踏まえ、`HENPIN_SU`・`SYUKKA_SU`を数値として非負整数に限定。整数相当の小数表記は許可し、非整数は警告付きで行除外する仕様とテストを追加 | FEATURE-001 |
| 2026-08-05 | 未Commit | 当月空CSV | 実行日（JST）の当月CSVがヘッダーのみの場合は`EMPTY_CURRENT_MONTH_FILE`警告で継続。最新データ月は有効レコードの最新月。過去月の空／有効行0件と当月不正行のみ0件は従来どおり失敗 | FEATURE-001 |
| 2026-08-05 | 未Commit | UI表示圧縮 | 注意書きを初期折りたたみにし、ヘッダー・フィルター・KPI余白を圧縮。グラフ高さを320px固定して縦スクロール負担を軽減 | FEATURE-001 |
| 2026-08-05 | 未Commit | 仕入先ID並び | 単一仕入先を数値ID昇順で並べ、非数字IDは数値の後ろに文字列順。国内／海外は混ぜたまま。生成JSONと画面候補の両方で適用 | FEATURE-001 |
