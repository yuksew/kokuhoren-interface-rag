#!/usr/bin/env bash
# 質問画面を Cloud Run に載せ、IAP で社内（Google Workspace のドメイン）の人だけが開けるようにする。
#
# 前提（README の「社内で試す（Cloud Run）」）:
#   - gcloud CLI を入れて `gcloud auth login` 済み。課金を有効にしたプロジェクトがある
#   - 手元で build_db.py → build_rules.py → build_index.py を済ませ、db/ に DB とベクトルがある
#
# usage: PROJECT=my-project DOMAIN=example.co.jp bash deploy/deploy.sh [setup|secret|build|deploy|iap|all]
#   setup   API を有効にし、イメージ置き場（Artifact Registry）を作る（初回だけ）
#   secret  .env の ANTHROPIC_API_KEY を Secret Manager に入れる（キーは画面に出さない）
#   build   Cloud Build でイメージを作る（20分ほど）
#   deploy  Cloud Run に載せる（IAP つき、外から直接は開けない）
#   iap     IAP の通り道と、ドメインの人の閲覧を許可する
#   all     上を順に全部
set -euo pipefail

: "${PROJECT:?PROJECT（Google Cloud のプロジェクト ID）を指定してください}"
: "${DOMAIN:?DOMAIN（社内の Google Workspace のドメイン。例: example.co.jp）を指定してください}"
REGION="${REGION:-asia-northeast1}"
SERVICE="${SERVICE:-kokuhoren-rag}"
REPO="${REPO:-kokuhoren-rag}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:latest"
MAX_USD_PER_DAY="${MAX_USD_PER_DAY:-5}"
cd "$(dirname "$0")/.."

setup() {
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
    secretmanager.googleapis.com iap.googleapis.com --project "$PROJECT"
  gcloud artifacts repositories describe "$REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1 ||
    gcloud artifacts repositories create "$REPO" --repository-format docker --location "$REGION" --project "$PROJECT"
  # Cloud Run の実行用サービスアカウント（既定の Compute のもの）に、シークレットを読む権限を付ける
  local num; num="$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')"
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member "serviceAccount:${num}-compute@developer.gserviceaccount.com" \
    --role roles/secretmanager.secretAccessor --condition None >/dev/null
}

secret() {
  local key; key="$(grep -E '^ANTHROPIC_API_KEY=' .env | head -1 | cut -d= -f2- | tr -d '\r\n"'"'"'')"
  [ -n "$key" ] || { echo ".env に ANTHROPIC_API_KEY がありません" >&2; exit 1; }
  if gcloud secrets describe anthropic-api-key --project "$PROJECT" >/dev/null 2>&1; then
    printf '%s' "$key" | gcloud secrets versions add anthropic-api-key --data-file=- --project "$PROJECT"
  else
    printf '%s' "$key" | gcloud secrets create anthropic-api-key --data-file=- --replication-policy automatic --project "$PROJECT"
  fi
}

build() {
  for f in db/interface_spec.sqlite db/vectors.ruri-v3-310m.npy; do
    [ -f "$f" ] || { echo "$f がありません（build_db.py → build_rules.py → build_examples.py → build_daysettings.py → build_index.py を先に）" >&2; exit 1; }
  done
  gcloud builds submit --project "$PROJECT" --region "$REGION" --tag "$IMAGE" --timeout 40m --machine-type e2-highcpu-8 .
}

deploy() {
  gcloud run deploy "$SERVICE" --project "$PROJECT" --region "$REGION" --image "$IMAGE" \
    --memory 4Gi --cpu 2 --cpu-boost --timeout 300 --concurrency 8 --min-instances 0 --max-instances 1 \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest --set-env-vars "MAX_USD_PER_DAY=${MAX_USD_PER_DAY}" \
    --no-allow-unauthenticated --iap
}

iap() {
  local num; num="$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')"
  gcloud run services add-iam-policy-binding "$SERVICE" --project "$PROJECT" --region "$REGION" \
    --member "serviceAccount:service-${num}@gcp-sa-iap.iam.gserviceaccount.com" --role roles/run.invoker
  gcloud iap web add-iam-policy-binding --project "$PROJECT" --region "$REGION" \
    --resource-type cloud-run --service "$SERVICE" \
    --member "domain:${DOMAIN}" --role roles/iap.httpsResourceAccessor
  gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format 'value(status.url)'
}

case "${1:-all}" in
  setup) setup ;; secret) secret ;; build) build ;; deploy) deploy ;; iap) iap ;;
  all) setup; secret; build; deploy; iap ;;
  *) echo "usage: PROJECT=... DOMAIN=... bash deploy/deploy.sh [setup|secret|build|deploy|iap|all]" >&2; exit 2 ;;
esac
