#!/usr/bin/env bash
# Pulls the btc-agent's API keys from AWS Systems Manager Parameter Store and writes them to a
# root-owned, group-readable env file that systemd loads via EnvironmentFile=. Runs on every boot
# (see btc-agent-secrets.service), so a replacement instance re-fetches the current keys on its
# own as long as the instance role is attached -- nothing is ever typed into the box by hand.
#
# Requires: the AWS CLI, and an instance role allowed to ssm:GetParametersByPath on /btc-agent/*
# and kms:Decrypt via the ssm service (see iam-policy.json).

set -euo pipefail

SSM_PATH="/btc-agent"
ENV_FILE="/etc/btc-agent/env"
ENV_GROUP="btc-agent" # Matches the system user the service runs as (see btc-agent.service)
REGION="${AWS_REGION:-$(curl -s http://169.254.169.254/latest/meta-data/placement/region)}"

mkdir -p "$(dirname "$ENV_FILE")"
umask 077 # Belt-and-braces: anything created from here on starts out root-only

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

aws ssm get-parameters-by-path \
    --path "$SSM_PATH" \
    --with-decryption \
    --recursive \
    --region "$REGION" \
    --query "Parameters[].{Name:Name,Value:Value}" \
    --output text |
while IFS=$'\t' read -r name value; do
    key="${name#"${SSM_PATH}"/}"
    printf '%s=%s\n' "$key" "$value"
done > "$TMP_FILE"

if [ ! -s "$TMP_FILE" ]; then
    echo "No parameters found under ${SSM_PATH}/ in region ${REGION} -- check the path and the instance role." >&2
    exit 1
fi

mv "$TMP_FILE" "$ENV_FILE"
chown "root:${ENV_GROUP}" "$ENV_FILE"
chmod 640 "$ENV_FILE"
echo "Wrote $(wc -l < "$ENV_FILE") secret(s) to $ENV_FILE"
