# 予定調整ツール

このプロジェクトは、PythonとFlask、Firestoreを使って構築されたシンプルな予定調整ツールです。

## セットアップと実行

### 1. 前提条件

- Python 3.8以上
- uv (Python service-installer/パッケージ管理ツール)
- Google Cloud CLI (`gcloud`コマンドラインツール)
- 課金が有効な Google Cloud プロジェクト。
    - 有効化されているかどうかの確認：[https://docs.cloud.google.com/billing/docs/how-to/verify-billing-enabled](https://docs.cloud.google.com/billing/docs/how-to/verify-billing-enabled)
    - 有効化の手順：[https://docs.cloud.google.com/billing/docs/how-to/modify-project](https://docs.cloud.google.com/billing/docs/how-to/modify-project)
- 従量課金を避けたい場合は、Gemini Code Assist のライセンスの購入が推奨されます。
    - 購入手順：[https://docs.cloud.google.com/gemini/docs/admin](https://docs.cloud.google.com/gemini/docs/admin)
- **環境に関する注意:** 本手順は Cloud Shell での実行を想定していますが、その他のターミナルで設定する場合は、`gcloud auth application-default login` を行って、認証情報を取得してください。

### 2. リポジトリのクローンとAPI有効化

#### 2-1. リポジトリのクローン
リポジトリをクローンし、プロジェクトディレクトリに移動します。
```bash
cd ~/ && git clone https://github.com/shonuma/gemini-cli-workshop-10x.git
cd ~/gemini-cli-workshop-10x/schedule-app
# スクリプトに実行権限を付与
chmod +x *.sh
```

#### 2-2. APIの有効化
Cloud Firestore および Cloud Run 関連の API を有効化します。 API の有効化には[`roles/servicemanagement.serviceConsumer` 権限](https://docs.cloud.google.com/endpoints/docs/openapi/enable-api) が必要です。

また、後の手順で **Cloud Firestore データベースを作成する際**には、[`roles/datastore.owner` 権限](https://firebase.google.com/docs/firestore/enterprise/security/iam#predefined_roles) が必要になります。権限が不足している場合は、あらかじめ管理者によって付与されていることを確認してください。

```bash
gcloud services enable \
    firestore.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
```

### 3. 環境構築

#### 3-1. 仮想環境の構築
仮想環境を構築します。
```bash
uv venv
```

#### 3-2. 仮想環境の有効化
仮想環境を有効化します。
```bash
source .venv/bin/activate
```

#### 3-3. ライブラリのインストール
必要なライブラリをインストールします。
```bash
uv pip install -r requirements.txt
```

### 4. 環境変数の設定

#### 4-1. 環境設定スクリプトの実行
`.env` ファイルを作成し、必要な環境変数を一括設定するためのスクリプトを実行します。
```bash
./setup_env.sh
```
スクリプトの実行中に以下の情報を入力してください：
- `Project ID`: Google Cloud のプロジェクトID
- `Region`: リージョン (例: `asia-northeast1`)
- `Service Name`: Cloud Run サービスの名称 (例: `scheduler-app`)
- `Service Account Name`: サービスアカウントの名称 (例: `scheduler-sa`)

※ `FLASK_SECRET_KEY` は `openssl` を使用して自動生成されます。

#### 4-2. 設定内容の確認
作成された `.env` ファイルの内容を確認します。
```bash
cat .env
```

#### 4-3. Firestoreデータベースの作成
以下のコマンドを実行し、Firestoreデータベースを作成します。
前の手順で作成した `.env` ファイルの設定が使用されます。
```bash
./create_db.sh
```

#### 4-4. 作成内容の確認
Firestore データベースが正しく作成されたか確認します。
```bash
gcloud firestore databases list
```

### 5. ターミナルを閉じてしまった場合の復旧方法
作業の途中でターミナルを閉じてしまった場合は、以下のコマンドを実行して作業を再開してください。

```bash
# ディレクトリの移動
cd ~/gemini-cli-workshop-10x/schedule-app

# 仮想環境の有効化
source .venv/bin/activate

# 環境変数の再読み込み
set -a; source .env; set +a
```

### 6. ローカル実行

#### 6-1. アプリケーションの起動
アプリケーションを起動します。
```bash
flask run
```

#### 6-2. ブラウザでのアクセス
Webブラウザで `http://127.0.0.1:5000` にアクセスします。

#### 6-3. サーバーの停止
サーバーを停止するには、ターミナルで `Ctrl+C` を押してください。
また、別のターミナルを開いて以下のコマンドを実行することでも停止可能です。
```bash
pkill flask
```

## デプロイ

### 1. サービスアカウント作成 (初回のみ)

Cloud RunがFirestoreにアクセスするためのサービスアカウントを作成し、必要な権限を付与します。
`.env` ファイルに設定した`PROJECT_ID`と`SERVICE_ACCOUNT_NAME`が使用されます。

**注意:** このスクリプト内で実行される IAM ポリシーの変更には、実行ユーザーに **「プロジェクト IAM 管理者 (`roles/resourcemanager.projectIamAdmin`)」** または **「オーナー (`roles/owner`)」** 権限が必要です。権限が不足している場合は、管理者へ作業を依頼してください。

#### 1-1. スクリプトの実行
スクリプトを実行します。
```bash
./create_sa.sh
```
このスクリプトは以下の処理を自動で行います：
- `gcloud iam service-accounts create`: Cloud Run 用のサービスアカウントを作成します。
- `gcloud projects add-iam-policy-binding`: 作成したサービスアカウントに Firestore へのアクセス権限（`roles/datastore.user`）を付与します。

#### 1-2. 作成内容の確認
サービスアカウントが正しく作成されたか確認します。（変数が読み込まれていない場合は、手順 5 を参考に環境変数を一括設定してください）
```bash
gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

### 2. GCP 権限・リポジトリ設定 (初回のみ)

デプロイを成功させるために、Artifact Registry の作成と適切な権限付与が必要です。

#### 2-1. リポジトリと権限の設定
以下のスクリプトを実行して、リポジトリの作成とビルド用サービスアカウントへの権限付認を一括で行います。

```bash
./setup_repo.sh
```
このスクリプトは以下の処理を自動で行います：
- `gcloud artifacts repositories create`: Docker イメージを保存するための Artifact Registry リポジトリを作成します。
- `gcloud projects add-iam-policy-binding`: Cloud Build がリポジトリにイメージをプッシュできるように、ビルド用サービスアカウントに権限（`roles/artifactregistry.writer`）を付与します。

### 3. Cloud Runへのデプロイ

このプロジェクトでは、**Dockerfile** を使用してコンテナイメージをビルドし、**Google Cloud Build** を経由して **Cloud Run** にデプロイします。

`.env` ファイルに設定した環境変数 (`PROJECT_ID`, `REGION`, `SERVICE_NAME`, `SERVICE_ACCOUNT_NAME`) を使用します。

#### 3-1. スクリプトの実行
スクリプトを実行します。
```bash
./deploy.sh
```
このスクリプトは以下の処理を自動で行います：
- `gcloud builds submit`: ソースコードを Cloud Build に送信し、`gcr.io` に Docker イメージをビルド・保存します。
- `gcloud run deploy`: ビルドされた最新のイメージを Cloud Run にデプロイします。

デプロイが完了すると以下のようなログが表示され、Cloud RunのサービスURLが表示されます。
```
Service [scheduler-app] revision [*****] has been deployed and is serving 100 percent of traffic.
Service URL: https://*****.asia-northeast1.run.app
Deployment complete.
```

Service URL をクリックすると、ブラウザが起動しウェブサイトへアクセスできます。