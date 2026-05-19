#!/bin/bash

# 1. 依存コマンドの確認
for cmd in gcloud grep xargs openssl; do
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
for var in PROJECT_ID REGION SERVICE_NAME SERVICE_ACCOUNT_NAME FLASK_SECRET_KEY; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env"
        exit 1
    fi
done

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO_NAME="app-repo"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

# 4. Artifact Registry リポジトリの準備
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" > /dev/null 2>&1; then
  echo "Creating Artifact Registry repository: ${REPO_NAME} in ${REGION}..."
  gcloud artifacts repositories create "${REPO_NAME}" \
      --repository-format=docker \
      --location="${REGION}" \
      --description="Docker repository for Schedule App" \
      --project="${PROJECT_ID}"
fi

# 5. ビルド
echo "Building ${SERVICE_NAME} image using Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}"

# 6. デプロイ
echo "Deploying ${SERVICE_NAME} to Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --region "${REGION}" \
  --project="${PROJECT_ID}" \
  --service-account="${SERVICE_ACCOUNT_EMAIL}" \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},REGION=${REGION},FLASK_SECRET_KEY=${FLASK_SECRET_KEY},FIRESTORE_DATABASE=${FIRESTORE_DATABASE:-schedule-app}" \
  --allow-unauthenticated \
  --platform managed

echo "Deployment complete."
