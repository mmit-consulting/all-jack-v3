#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status (-e),
# treat unset variables as an error (-u),
# and make pipelines fail if any command fails (-o pipefail).
set -euo pipefail

# The retention days can be passed as the first argument when running the script.
# If not provided, it defaults to 90 days.
RETENTION_DAYS="${1:-90}"

# We only work in us-east-1
REGION="us-east-1"

# Check if AWS credentials are available.
# If AWS_PROFILE is not exported and raw creds are missing, abort.
if [[ -z "${AWS_PROFILE:-}" && -z "${AWS_ACCESS_KEY_ID:-}" ]]; then
  echo "ERROR: Please export AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY before running."
  exit 1
fi

# Just for clarity in output, show which profile/account we’re running against.
echo "==> Using AWS_PROFILE: ${AWS_PROFILE:-<env-creds>}"
echo "==> Region:            ${REGION}"
echo "==> Retention:         ${RETENTION_DAYS} days"

# Create a CSV report filename that includes the profile (if set) and UTC timestamp.
REPORT="retention_report_${AWS_PROFILE:-env}_$(date -u +%Y%m%dT%H%M%SZ).csv"

# Add CSV header row.
echo "account,region,action,logGroupName,details" > "$REPORT"

# Query all CloudWatch log groups in the region that do NOT have a retention policy.
# `retentionInDays==null` means no retention is set (infinite retention).
# Output is just the logGroupName(s) as plain text.
LOG_GROUPS=$(aws logs describe-log-groups \
  --region "$REGION" \
  --query 'logGroups[?retentionInDays==null].logGroupName' \
  --output text)

# If nothing comes back, it means all log groups already have retention set.
if [[ -z "$LOG_GROUPS" ]]; then
  echo "No log groups missing retention in $REGION"
  echo "${AWS_PROFILE:-env},${REGION},noop,,none_missing" >> "$REPORT"
  exit 0
fi

# Loop through each log group name returned above.
for LG in $LOG_GROUPS; do
  echo "Setting ${RETENTION_DAYS} days on: ${LG}"

  # Apply the retention policy using AWS CLI.
  aws logs put-retention-policy \
    --region "$REGION" \
    --log-group-name "$LG" \
    --retention-in-days "$RETENTION_DAYS"

  # Record the action in the CSV report.
  echo "${AWS_PROFILE:-env},${REGION},set,${LG},retention=${RETENTION_DAYS}" >> "$REPORT"
done

echo
echo "==> Done. Report written to $REPORT"
