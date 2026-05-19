#!/bin/bash

# 1. 依存コマンドの確認
for cmd in gcloud grep xargs; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# 2. .env から設定を読み込み (コメント行と空行を除外)
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please run ./setup_env.sh first."
    exit 1
fi

set -a; source .env; set +a

# 3. 必須変数のチェック
for var in PROJECT_ID REGION; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env"
        exit 1
    fi
done

REPO_NAME="app-repo"

# 4. Artifact Registry リポジトリの作成
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" > /dev/null 2>&1; then
  echo "Creating Artifact Registry repository: ${REPO_NAME} in ${REGION}..."
  gcloud artifacts repositories create "${REPO_NAME}" \
      --repository-format=docker \
      --location="${REGION}" \
      --description="Docker repository for Schedule App" \
      --project="${PROJECT_ID}"
else
  echo "Artifact Registry repository: ${REPO_NAME} already exists."
fi

# 5. ビルド用サービスアカウントへの権限付与
echo "Granting Artifact Registry Writer role to the default compute service account..."

# プロジェクト番号の取得
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")

# 権限の付与 (Artifact Registry への書き込み権限)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" \
    --condition=None

# 権限の付与 (Cloud Build がソースコードを読み取るための Storage 閲覧権限)
echo "Granting Storage Object Viewer role to the default compute service account..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectViewer" \
    --condition=None

echo "Repository and IAM setup complete."
