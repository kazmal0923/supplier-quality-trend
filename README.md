# アプリ開発スターターキット v0.1

## 目的

既存のExcel・CSV・業務資料などをChatGPTで分析し、標準化された設計文書へ変換し、Cursorで実装するための共通開発基盤です。

> ChatGPTは記憶型の設計者  
> Cursorは再読型の実装者  
> GitHubは両者をつなぐ共有外部記憶

## 基本フロー

1. ChatGPTと現行資産を解析する
2. 現状仕様・推測事項・未確定事項を分離する
3. 人間が業務ルールを確定する
4. ChatGPTが `docs` 一式を生成・更新する
5. Cursorが `AGENTS.md` と `docs` を再読する
6. Cursorが実装計画を提示する
7. 人間が計画を確認する
8. Cursorが実装・テスト・ビルドを行う
9. 成功条件を満たした場合のみdocsを更新し、Commit・Pushする
10. ChatGPTがGitHub上の最新版を再読して次の設計を行う

## GitHub運用

- 個人GitHubアカウント配下のPrivateリポジトリを前提とします。
- ローカル環境は「作業中の記憶」です。
- featureブランチは「実装済み・確認待ちの共有記憶」です。
- mainブランチは「正式に確定した共有記憶」です。
- Pushはコード保存ではなく、検証済みのコード・仕様・判断・進捗を共有記憶として確定する操作です。

## 使い方

1. このフォルダを新規アプリ用リポジトリへ複製します。
2. `docs/00_project-overview.md` から順に記入します。
3. 既存Excelなどがある場合は、最初に `docs/01_current-state-analysis.md` を作成します。
4. MVPを `docs/features/FEATURE-001_initial-mvp.md` に定義します。
5. Cursorへ次のように指示します。

```text
AGENTS.mdとdocs配下の設計文書をすべて読んでください。
既存コードと仕様を確認し、MVPの実装計画を作成してください。
この段階ではコードを変更しないでください。
```

## ディレクトリ構成

```text
.
├─ AGENTS.md
├─ README.md
├─ .gitignore
├─ .cursor/
│  └─ rules/
│     └─ development-workflow.mdc
├─ docs/
│  ├─ 00_project-overview.md
│  ├─ 01_current-state-analysis.md
│  ├─ 02_requirements.md
│  ├─ 03_data-specification.md
│  ├─ 04_acceptance-criteria.md
│  ├─ 05_current-status.md
│  ├─ features/
│  ├─ decisions/
│  ├─ testing/
│  └─ changes/
├─ templates/
└─ examples/
   └─ quality-defect-rate-dashboard/
```

## テンプレートの育て方

このスターターキット自体もMVPとして扱います。実案件で不足が見つかった場合は、テンプレートを修正してv0.2以降へ更新してください。
