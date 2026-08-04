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

実際の入力データパスは、Git管理対象外の`config/settings.json`で管理する。

PCごとにローカルの保存先は異なるが、GitHub上のリポジトリ構成は同一に保つ。

---

## 3. パス運用ルール

- ソースコードでは、原則としてリポジトリ直下からの相対パスを使用する
- PC固有の絶対パスをコードや設計文書へ直接記述しない
- PC固有の設定は、Git管理対象外の`config/settings.json`で管理する
- 実際の社内IPアドレス、Windowsアカウント名、本番データパスをGitへ記録しない
- 公開用の設定例にはプレースホルダーだけを記載する

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

MVPの実行可能なアプリコードとテストコードを実装済みである。

| ソフトウェア | バージョン | 用途 | 状態 |
|---|---:|---|---|
| Git | 要記入 | バージョン管理 | 必要 |
| Cursor | 最新安定版 | 実装・コード確認 | 必要 |
| Python | 3.14 | データ読込・検証・集計・静的JSON生成 | 採用 |
| Apache ECharts | 6.1.0 | グラフ表示 | 採用 |
| IIS | 移植先環境で確認 | `web/`の静的配信 | 採用 |

Node.js、データベース、常駐Pythonサーバーは使用しない。

---

## 6. 初期セットアップ

公開用設定例をローカル設定へコピーし、実際の入力パスとエイリアスを設定する。

```powershell
Copy-Item config/settings.example.json config/settings.json
Copy-Item config/supplier-name-aliases.example.csv config/supplier-name-aliases.csv
python main.py
```

仮想環境は使用しない。Python標準ライブラリを優先する。

---

## 7. 環境変数

現時点では必須の環境変数はない。入力データ等の本番パスは、Git管理外の`config/settings.json`で管理する。

文書や公開用の設定例では、実パスを記載せずプレースホルダーを使用する。

```text
月次CSVフォルダー: <月次CSVフォルダー>
仕入先マスタ: <仕入先マスタファイル>
```

ユーザーホームは`Path.home()`で取得し、そこからの相対パスを`settings.json`で管理する。アプリディレクトリは`main.py`の配置場所を基準に取得し、Windowsアカウント名をコードや設定例へ固定しない。

---

## 8. 実行・公開方法

`python main.py`または`run.bat`で表示用JSONを生成する。常駐Pythonサーバーは起動せず、静的な`web/`をIISで配信する。

開発時の匿名サンプル画面は、次のコマンドとURLで確認する。

```powershell
python -m http.server 8000 --directory web
```

`http://localhost:8000/?example=1`

- 予定配置先：`C:\var\supplier-quality-trend`
- IISサイト物理パス：`C:\var\supplier-quality-trend\web`
- URL例：`http://<社内IISサーバー>/`
- 既定ドキュメント：`index.html`

実際のURL、IIS設定、アクセス権は移植時に確認する。

### タスクスケジューラ

移植時の予定設定：

- 毎週月曜日、午前8時
- プログラム：`run.bat`
- 引数：`scheduled`
- 開始フォルダー：アプリディレクトリ
- 開始時刻を逃した場合は可能になり次第実行
- 失敗時は10分間隔で最大3回再試行
- 二重起動しない
- 最大実行時間30分

手動実行の`run.bat`は成功時に自動終了し、失敗時だけ`logs/error.log`の場所を表示して一時停止する。`run.bat scheduled`は一時停止せず、成功時0、失敗時1を返す。

---

## 9. テスト

```powershell
python -m unittest discover -s tests -v
python -m compileall main.py supplier_quality_trend tests
```

加えて、匿名サンプル画面のHTTP応答、フィルター、KPI、詳細表、グラフ、空状態を対象ブラウザで確認する。

---

## 10. 型チェック・Lint

Python構文は`compileall`、JavaScript構文は利用可能な場合に`node --check`、IDE診断はCursorの診断機能で確認する。専用の静的型チェッカーとLintツールは導入していない。

---

## 11. ビルド

該当なし。Pythonバッチと静的HTML／CSS／JavaScriptで構成し、ビルド工程を持たないため。

---

## 12. データファイルの置き場所

| 用途 | 置き場所 | Git管理 |
|---|---|---|
| 匿名化または架空サンプル | `tests/fixtures/`、`web/data/*.example.json` | 可（機密を含まないこと） |
| 本番月次CSV・仕入先マスタ原本 | `settings.json`で指定するGit外の場所 | 不可 |
| 実設定 | `config/settings.json` | 不可 |
| 実エイリアス | `config/supplier-name-aliases.csv` | 不可 |
| 生成された本番JSON | `web/data/` | 不可 |
| ログ | `logs/` | 不可 |

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
