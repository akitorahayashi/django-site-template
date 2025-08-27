# Gist Summarizer

このプロジェクトは、指定されたウェブページの内容を要約し、問い合わせに応答するDjangoアプリケーションです。
近代的な開発プラクティスを導入しており、Docker、Makefile, GitHub ActionsによるCI/CDパイプラインが整備されています。

## ✅ 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください。

- **Docker**: 最新版を推奨
- **Docker Compose**: Dockerに同梱
- **Make**: `make` コマンドが利用可能であること
- **Python**: 3.12 (推奨, `.python-version` ファイル参照)
- **Poetry**: 1.8.3 (推奨)

## 🚀 はじめに (Getting Started)

開発を始めるには、まずリポジトリをクローンし、以下のコマンドで **ホストマシンに** Poetryの仮想環境をセットアップし、依存関係をインストールします。

```bash
make setup
```

## 🐳 コンテナのビルドと実行

アプリケーションはDockerコンテナ上で実行されます。以下のコマンドでコンテナをビルドし、バックグラウンドで起動します。

```bash
make up
```

コンテナが起動したら、`http://localhost:8000`でアプリケーションにアクセスできます。

> **📝 Linuxユーザー向けの注意**
> 開発環境では、コンテナからホストマシン上のサービス（例：モックサーバー）にアクセスするために `host.docker.internal` を使用します。この設定は `docker-compose.override.yml` 内の `extra_hosts` で自動的に行われます。もし `host.docker.internal` が解決できない古いDockerバージョンを使用している場合は、Dockerを最新版に更新してください。

コンテナを停止・削除するには、以下のコマンドを実行します。

```bash
make down
```

### 本番環境を模した実行 (Production-like Execution)

本番環境をシミュレートするためのコマンドが用意されています。これにより、`docker-compose.override.yml` を使用せず、本番に近い設定でコンテナを起動できます。

コンテナをビルドして起動するには、以下のコマンドを実行します。

```bash
make up-prod
```

> **⚠️ 重要**
> `make up-prod` を実行する前に、`.env.example` をコピーして `.env.prod` ファイルを作成し、本番用の環境変数を設定する必要があります。`.env.prod` ファイルは `.gitignore` によりバージョン管理から除外されています。

本番環境用のコンテナを停止・削除するには、以下のコマンドを実行します。

```bash
make down-prod
```

## ✅ テストとコード品質

プロジェクトには、コードの品質を維持するためのテスト、リンター、フォーマッターが用意されています。

### テストの実行

ローカルでテストを実行するには、いくつかの方法があります。

1.  **Makeコマンドを使用する方法 (ホストのPoetry環境を利用):**
    ```bash
    make test ENV=dev
    ```

2.  **Dockerコンテナ内で直接実行する方法:**
    コンテナが起動している(`make up`実行後)ことを確認し、以下のコマンドを実行します。
    ```bash
    docker compose exec web poetry run pytest
    ```

### コードのフォーマット

`black`と`ruff`を使ってコードを自動整形します。
```bash
make format
```

### リンターとフォーマットのチェック

CIでも実行されるチェックです。コードに問題がないかを確認します。
```bash
make lint-check
make format-check
```

## 🛠 Makefileコマンド一覧

プロジェクトで利用可能なすべてのコマンドは、`make help`で確認できます。以下は主なコマンドの概要です。

| コマンド              | 説明                                                                 |
| --------------------- | -------------------------------------------------------------------- |
| `make setup`          | `.env.dev` と `.env.prod` ファイルを `.env.example` から作成します。   |
| `make up`             | 開発環境のDockerコンテナをビルドして起動します。                     |
| `make down`           | 開発環境のDockerコンテナを停止・削除します。                         |
| `make rebuild`        | 開発コンテナをキャッシュなしで再ビルドし、再起動します。             |
| `make logs`           | 開発コンテナのログを表示します。                                     |
| `make shell`          | 開発用の`web`コンテナ内でシェルを起動します。                        |
| `make up-prod`        | 本番環境用のDockerコンテナをビルドして起動します。                   |
| `make down-prod`      | 本番環境用のDockerコンテナを停止・削除します。                       |
| `make migrate`        | 開発環境でデータベースのマイグレーションを実行します。               |
| `make makemigrations` | 新しいマイグレーションファイルを作成します。                         |
| `make superuser`      | 開発環境でDjangoのスーパーユーザーを作成します。                     |
| `make migrate-prod`   | 本番環境でデータベースのマイグレーションを実行します。               |
| `make superuser-prod` | 本番環境でDjangoのスーパーユーザーを作成します。                     |
| `make test`           | `web`コンテナ内でテストスイートを実行します。                        |
| `make format`         | `black` と `ruff` を使ってコードをフォーマットします。               |
| `make lint`           | `ruff` を使ってコードをリントします。                                |
| `make lint-check`     | `ruff` でリントエラーがないかチェックします。                        |
| `make clean`          | すべてのコンテナを停止し、生成されたファイルをクリーンアップします。 |
| `make help`           | 利用可能なすべてのコマンドのリストと説明を表示します。               |
