#!/bin/bash

# 1. 依存コマンドの確認
for cmd in gcloud openssl sed; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# 2. .env.example の存在確認
if [ ! -f .env.example ]; then
    echo "Error: .env.example not found."
    exit 1
fi

# 3. 既存の .env の確認
if [ -f .env ]; then
    read -p ".env file already exists. Overwrite? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    # バックアップを作成
    cp .env .env.bak
    echo "Backup of existing .env created as .env.bak"
fi

# .env を作成
cp .env.example .env

# 4. プロジェクトIDの取得
current_project_id=$(gcloud config list project --format="value(core.project)" 2>/dev/null)

# 5. ユーザー入力の取得
read -p "Enter your Google Cloud Project ID [${current_project_id}]: " project_id
project_id=${project_id:-$current_project_id}

if [ -z "$project_id" ]; then
    echo "Error: Project ID is required."
    exit 1
fi

read -p "Enter your Region [asia-northeast1]: " region
region=${region:-asia-northeast1}

read -p "Enter your Cloud Run Service Name [scheduler-app]: " service_name
service_name=${service_name:-scheduler-app}

read -p "Enter your Service Account Name [scheduler-sa]: " sa_name
sa_name=${sa_name:-scheduler-sa}

read -p "Enter your Firestore Database ID [schedule-app]: " firestore_db
firestore_db=${firestore_db:-schedule-app}

# 6. 安全な書き換え関数の定義 (sed の差異を吸収)
update_env() {
    local key=$1
    local value=$2
    # 一時ファイルを使用して書き換え (macOS/Linux 両対応)
    sed "s|^${key}=.*|${key}=${value}|" .env > .env.tmp && mv .env.tmp .env
}

# 7. 書き換えの実行
update_env "PROJECT_ID" "${project_id}"
update_env "REGION" "${region}"
update_env "SERVICE_NAME" "${service_name}"
update_env "SERVICE_ACCOUNT_NAME" "${sa_name}"
update_env "FIRESTORE_DATABASE" "${firestore_db}"

# FLASK_SECRET_KEY の生成と設定
secret_key=$(openssl rand -base64 32)
update_env "FLASK_SECRET_KEY" "${secret_key}"

echo ".env file has been created and configured successfully."
