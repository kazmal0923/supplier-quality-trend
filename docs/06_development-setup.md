# 開発環境構築

## 1. この文書の目的

本書は、仕入先品質トレンドを新しいPCへCloneした際に、同じ開発環境を再現するための手順を記録する。

開発に必要なソフトウェア、バージョン、環境変数、起動方法、テスト方法、ビルド方法を一元管理する。

---

## 2. 使用PC

本プロジェクトは、複数のPCで作業する可能性がある。

ローカルのクローン先はPCごとに異なる。Git管理対象ファイルには実ユーザー名や実パスを記載せず、次のプレースホルダー形式のみ使用する。

```text
C:\Users\<ユーザー名>\Desktop\Projects\supplier-quality-trend
```

実際のパスは、Git管理対象外の`.env`またはローカルメモで管理する。

PCごとにローカルの保存先は異なるが、GitHub上のリポジトリ構成は同一に保つ。

---

## 3. パス運用ルール

- ソースコードでは、原則としてリポジトリ直下からの相対パスを使用する
- PC固有の絶対パスをコードや設計文書へ直接記述しない
- PC固有の設定は、環境変数またはGit管理対象外のローカル設定ファイルで管理する
- 実値を含む`.env`はGitHubへPushしない
- 共有する環境変数名は`.env.example`へ記載する

良い例：

```text
docs/03_data-specification.md
data/samples/sample.csv
src/app/
./config/settings.json
```

避ける例：

```text
実際のユーザー名を含む絶対パス
会社PC・個人PC固有の実パス
```

---

## 4. リポジトリの取得

```powershell
cd C:\Users\<ユーザー名>\Desktop\Projects
git clone https://github.com/kazmal0923/supplier-quality-trend.git
cd supplier-quality-trend
```

Clone後に、以下を確認する。

```powershell
git status
git remote -v
git branch --show-current
```

---

## 5. 必要なソフトウェア

現時点では実行可能なアプリコードが存在しない。採用技術確定後に更新する。

| ソフトウェア | バージョン | 用途 | 状態 |
|---|---:|---|---|
| Git | 要記入 | バージョン管理 | 必要 |
| Cursor | 最新安定版 | 実装・コード確認 | 必要 |
| Node.js | 未定 | Webアプリ開発（採用時） | 未確定 |
| Python | 未定 | データ処理（採用時） | 未確定 |

使用しない項目は、採用技術確定時に削除する。

---

## 6. 初期セットアップ

現時点：該当なし（アプリコード未存在）

採用技術の決定後に、実際のコマンドへ置き換える。

### Node.jsを採用した場合の例

```powershell
npm install
```

### Pythonを採用した場合の例

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 7. 環境変数

現時点では必須の環境変数はない。

実際の値は`.env`へ設定し、GitHubへPushしない。

共有する環境変数名と用途は`.env.example`へ記載する。

`.env`の作成例：

```powershell
Copy-Item .env.example .env
```

将来、入力・出力ディレクトリが必要になった場合の候補：

```text
# INPUT_DATA_DIR=
# OUTPUT_DATA_DIR=
```

---

## 8. 開発サーバーの起動

現時点：該当なし（実行可能なアプリコードが存在しない）

採用技術の決定後に、実際のコマンドへ置き換える。

---

## 9. テスト

現時点：該当なし（テストコマンド未整備）

理由：実行可能なアプリコードが存在しないため。

現時点の確認相当：

- Markdownの表示
- リンク切れがないこと
- ファイル構成
- 文書間の矛盾がないこと
- `git diff --check`
- Git差分
- 機密情報・実データ・実絶対パスの混入がないこと

採用技術決定後の例：

```powershell
npm test
```

または

```powershell
pytest
```

---

## 10. 型チェック・Lint

現時点：該当なし

理由：実行可能なアプリコードおよび関連コマンドが存在しないため。

---

## 11. ビルド

現時点：該当なし

理由：実行可能なアプリコードが存在しないため。

---

## 12. データファイルの置き場所

| 用途 | 置き場所 | Git管理 |
|---|---|---|
| 匿名化または架空サンプル | `data/samples/`（作成時） | 可（機密を含まないこと） |
| 現行Excel原本・実CSV | `data/raw/` または `data/private/` | 不可 |
| 本番データ | `data/private/` または社内保管場所 | 不可 |

ExcelやCSVを拡張子単位で一律除外しない。保存場所単位で管理する。

---

## 13. 複数PCでの作業

### 作業開始時

```powershell
git status
git branch --show-current
git pull --ff-only
```

未コミットの変更がある場合は、内容を確認してから`git pull`する。

### 作業終了時

```powershell
git status
git diff
git add .
git commit -m "<COMMIT_MESSAGE>"
git push
```

別のPCで作業を継続する場合は、現在のPCでCommit・Pushを完了してから作業を終了する。

同じブランチを2台のPCで同時に編集しない。

---

## 14. よく使用する確認コマンド

### 現在の状態

```powershell
git status
```

### 現在のブランチ

```powershell
git branch --show-current
```

### GitHubの接続先

```powershell
git remote -v
```

### 最近のコミット

```powershell
git log --oneline --decorate -5
```

### 未ステージの差分

```powershell
git diff
```

### ステージ済みの差分

```powershell
git diff --cached
```

### 空白・衝突マーカー確認

```powershell
git diff --check
```

---

## 15. 更新ルール

以下を変更した場合は、本書も同時に更新する。

- 必要なソフトウェア
- ソフトウェアのバージョン
- 環境変数
- 初期セットアップ手順
- 起動コマンド
- テストコマンド
- 型チェック・Lintコマンド
- ビルドコマンド
- ディレクトリ構成
- データ保存先
