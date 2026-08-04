# 仕入先品質トレンド

**Supplier Quality Trend**

仕入先・グループ別 現行不良率推移ダッシュボード

Excel Power Queryで運用している品質管理ダッシュボードを、静的Webアプリとして再構築するプロジェクトです。
単一仕入先または仕入先グループの月別現行不良率推移を、正しい現行集計条件に基づいてブラウザから確認できるようにします。

> ChatGPTは記憶型の設計者  
> Cursorは再読型の実装者  
> GitHubは両者をつなぐ共有外部記憶

---

## 目的

- 単一仕入先・仕入先グループ別の月別現行不良率推移をWeb上で確認できるようにする
- Excelファイルや参照パスへの依存を減らす
- 複数人で同じ最新状態を確認しやすくする
- 現行指標の制約、警告、集計途中を利用者へ明示する

---

## 現状

- フェーズ：MVP基本設計確定 / 実装前
- 実行可能なアプリコードはまだ存在しない
- MVPの業務仕様、データ仕様、受入条件、技術構成を設計文書へ反映済み
- 0除算表示、照合許容差、異常入力等は未確定事項として管理
- ルートの`docs/`を正式な正本として管理する

詳細は`docs/05_current-status.md`を参照してください。

---

## MVPの範囲

### 含める

- 月次不良率CSV・仕入先マスタのファイル読込
- 単一仕入先・仕入先グループの選択、検索、絞り込み
- 月別・期間全体現行不良率の計算
- 最新13か月の推移と前年同月比較
- 目標1％、異常値、欠損月、集計途中、警告を含むグラフ・詳細表示
- Pythonバッチによる静的JSON生成と週次更新
- IISによる静的Web配信
- Excelとの集計結果比較

### 含めない

- 基幹システムやBoxからの元ファイル自動取得
- LINE WORKS通知
- 外部通知を伴う不良率アラート
- 商品別・カテゴリ別分析
- 詳細な権限管理

詳細は`docs/00_project-overview.md`および`docs/features/FEATURE-001_initial-mvp.md`を参照してください。

---

## データの概要

現行はExcelのPower Queryで月次データを読み込み、仕入先ID単位・月単位の現行不良率を表示しています。

```text
月別現行不良率 = HENPIN_SUの月別合計 ÷ SYUKKA_SUの月別合計
期間全体現行不良率 = 対象期間のHENPIN_SU合計 ÷ 対象期間のSYUKKA_SU合計
```

月別不良率の単純平均は使用しません。`SYUKKA_SU`には返品が発生したSKUの出荷数だけが含まれるため、本指標は仕入先全体の正式な不良率ではなく、現行集計条件に基づく傾向確認用指標です。100％を超える値も補正せず、警告付きで表示します。

詳細は`docs/03_data-specification.md`を参照してください。

本リポジトリはPublicであることを前提とします。実データ、現行Excel原本、本番CSV、仕入先マスタ原本、実設定、生成された本番JSON、ログはGit管理しません。匿名化または架空のサンプルのみ扱います。

---

## 文書一覧

| 文書 | 内容 |
|---|---|
| `docs/00_project-overview.md` | プロジェクト概要 |
| `docs/01_current-state-analysis.md` | 現状分析（AS-IS） |
| `docs/02_requirements.md` | 要件定義（TO-BE） |
| `docs/03_data-specification.md` | データ仕様 |
| `docs/04_acceptance-criteria.md` | 受入条件 |
| `docs/05_current-status.md` | 現在の開発状況 |
| [`docs/06_development-setup.md`](docs/06_development-setup.md) | 開発環境構築・複数PC運用 |
| [`docs/07_architecture.md`](docs/07_architecture.md) | アーキテクチャ |
| [`docs/08_security-and-data-handling.md`](docs/08_security-and-data-handling.md) | セキュリティとデータ取扱い |
| `docs/features/` | 機能仕様 |
| `docs/decisions/` | 設計判断（ADR） |
| `docs/testing/` | テスト記録 |
| `docs/changes/change-log.md` | 変更履歴 |

---

## 開発フロー

1. ChatGPTと現行Excel・CSV・業務資料を解析する
2. 現状仕様・推測事項・未確定事項を分離する
3. 人間が業務ルールを確定する
4. `docs`を更新する
5. Cursorが`AGENTS.md`と`docs`を再読する
6. Cursorが実装計画を提示する
7. 人間が計画を確認する
8. Cursorが実装・テスト・ビルドを行う
9. 成功条件を満たした場合のみdocsを更新し、Commit・Pushする
10. Pull Requestで確認後にmainへ統合する

---

## GitHub運用

- Publicリポジトリを前提とし、公開可能と確認できた情報だけを保存します
- ローカル環境：作業中の記憶
- featureブランチ：実装済み・確認待ちの共有記憶
- mainブランチ：正式に確定した共有記憶
- Pushは、検証済みのコード・仕様・判断・進捗を共有記憶として確定する操作です

---

## 複数PC運用

複数のPCで開発する場合があります。

- PCごとにローカル保存先は異なっても、GitHub上の構成は同一に保つ
- 同じブランチを複数PCで同時に編集しない
- 別PCで続ける場合は、現在のPCでCommit・Pushを完了してから終了する
- コードや文書では、特定PCの実絶対パスを使わない
- 相対パス、環境変数、Git管理対象外のローカル設定を使う

クローン先の説明には、次のプレースホルダーのみ使用します。

```text
C:\Users\<ユーザー名>\Desktop\Projects\supplier-quality-trend
```

詳細は[`docs/06_development-setup.md`](docs/06_development-setup.md)を参照してください。

---

## Pull Request運用

機能ブランチの変更は、原則としてPull Requestを通してmainへ統合します。

確認項目の詳細は`.github/pull_request_template.md`を使用します。

主な確認観点：

- 変更内容と変更理由
- 既存機能・集計定義への影響
- テスト、型チェック、Lint、ビルド（存在しない場合は該当なしと理由）
- 受入条件
- ドキュメント更新
- 機密情報・実データ・実絶対パスの混入
- 複数PCへの影響
- 未解決事項

現時点では実行可能なアプリコードがないため、テスト・型チェック・Lint・ビルドは「該当なし」とし、Markdown、リンク、ファイル構成、Git差分、機密情報混入を確認します。

---

## ディレクトリ構成

```text
.
├─ .cursor/rules/
├─ .github/pull_request_template.md
├─ docs/
│  ├─ 00_project-overview.md
│  ├─ 01_current-state-analysis.md
│  ├─ 02_requirements.md
│  ├─ 03_data-specification.md
│  ├─ 04_acceptance-criteria.md
│  ├─ 05_current-status.md
│  ├─ 06_development-setup.md
│  ├─ 07_architecture.md
│  ├─ 08_security-and-data-handling.md
│  ├─ features/
│  ├─ decisions/
│  ├─ testing/
│  └─ changes/
├─ templates/
├─ .env.example
├─ .gitignore
├─ AGENTS.md
└─ README.md
```

---

## 環境変数

現時点では必須の環境変数はありません。

本番の入力パス等は、実装時にGit管理外の`config/settings.json`で管理します。公開用の設定例にはプレースホルダーだけを記載し、実際の社内IPアドレス、Windowsアカウント名、本番データパスは含めません。

---

## Cursorへの初期指示例

```text
AGENTS.mdとdocs配下の設計文書をすべて読んでください。
既存コードと仕様を確認し、MVPの実装計画を作成してください。
この段階ではコードを変更しないでください。
```
