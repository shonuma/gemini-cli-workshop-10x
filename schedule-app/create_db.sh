#!/bin/bash

# .env ファイルが存在すれば読み込む (コメント行と空行を除外)
if [ ! -f .env ]; then
  echo "Error: .env file not found."
  exit 1
fi

set -a; source .env; set +a

# 環境変数が設定されているかチェック
if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is not set in .env"
  exit 1
fi
if [ -z "$REGION" ]; then
  echo "Error: REGION is not set in .env"
  exit 1
fi

FIRESTORE_DB_ID="${FIRESTORE_DATABASE:-schedule-app}"

echo "Creating Firestore database: ${FIRESTORE_DB_ID} in project: ${PROJECT_ID} (location: ${REGION})"

gcloud firestore databases create \
    --database="${FIRESTORE_DB_ID}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --edition=enterprise \
    --enable-firestore-data-access \
    --no-enable-mongodb-compatible-data-access \
    --enable-realtime-updates

echo "Firestore database setup complete."
