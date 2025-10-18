import os, json, boto3, datetime

sns = boto3.client("sns")
TOPIC_ARN = os.environ["TOPIC_ARN"]
SUBJECT_PREFIX = os.environ.get("SUBJECT_PREFIX", "[CWL Retention]")

def _extract(e):
    detail  = e.get("detail", {}) or {}
    account = e.get("account", "unknown")
    region  = e.get("region",  "unknown")
    rule    = detail.get("configRuleName", "unknown-rule")
    status  = (detail.get("newEvaluationResult", {}) or {}).get("complianceType", "UNKNOWN")

    resource = (
        detail.get("resourceId")
        or detail.get("configurationItemName")
        or (detail.get("newEvaluationResult", {}).get("evaluationResultIdentifier", {})
            .get("evaluationResultQualifier", {})
            .get("resourceId"))
        or "resource"
    )

    annotation = detail.get("annotation") or ""
    return account, region, rule, status, resource, annotation

def handler(event, context):
    account, region, rule, status, resource, annotation = _extract(event)
    subject = f"{SUBJECT_PREFIX} [{account}/{region}] {status} - {resource}"
    body = {
        "rule": rule,
        "status": status,
        "account": account,
        "region": region,
        "resource": resource,
        "annotation": annotation,
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "raw": event,  # useful for debugging; 
    }
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=subject,
        Message=json.dumps(body, indent=2, default=str),
    )
    return {"ok": True, "subject": subject}
