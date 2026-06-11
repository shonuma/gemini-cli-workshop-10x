#!/bin/bash

# .env ファイルが存在すれば読み込む (コメント行と空行を除外)
if [ -f .env ]; then
  export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# 環境変数が設定されているかチェック
if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is not set in .env"
  exit 1
fi
if [ -z "$SERVICE_ACCOUNT_NAME" ]; then
  echo "Error: SERVICE_ACCOUNT_NAME is not set in .env"
  exit 1
fi

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウントの存在確認
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" --project="${PROJECT_ID}" > /dev/null 2>&1; then
  echo "Creating service account: ${SERVICE_ACCOUNT_NAME} for project: ${PROJECT_ID}"
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Scheduler App Service Account" \
    --project="${PROJECT_ID}"
else
  echo "Service account: ${SERVICE_ACCOUNT_NAME} already exists."
fi

echo "Granting 'Cloud Datastore User' role to service account: ${SERVICE_ACCOUNT_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/datastore.user" \
  --project="${PROJECT_ID}"

echo "Service account setup complete."
