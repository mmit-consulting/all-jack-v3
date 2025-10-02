import json, boto3, datetime
logs = boto3.client("logs")
config = boto3.client("config")

def _has_retention(name: str) -> bool:
    # Check a single group by prefix; safe for exact names too
    resp = logs.describe_log_groups(logGroupNamePrefix=name, limit=1)
    groups = resp.get("logGroups", [])
    if not groups:          # deleted between event and evaluation
        return True
    return groups[0].get("retentionInDays") is not None

def _put_eval(res_id: str, compliant: bool, token: str):
    config.put_evaluations(
        Evaluations=[{
            "ComplianceResourceType": "AWS::Logs::LogGroup",
            "ComplianceResourceId":   res_id,
            "ComplianceType":         "COMPLIANT" if compliant else "NON_COMPLIANT",
            "Annotation":             "Retention is set." if compliant else "Retention is NOT set.",
            "OrderingTimestamp":      datetime.datetime.now(datetime.timezone.utc)
        }],
        ResultToken=token
    )

def handler(event, context):
    inv = json.loads(event["invokingEvent"])
    token = event["resultToken"]
    msg   = inv["messageType"]

    if msg == "ConfigurationItemChangeNotification":
        item = inv["configurationItem"]
        if item.get("resourceType") != "AWS::Logs::LogGroup":
            config.put_evaluations(Evaluations=[], ResultToken=token)
            return
        name = item["resourceId"]
        _put_eval(name, _has_retention(name), token)

    elif msg == "ScheduledNotification":
        paginator = logs.get_paginator("describe_log_groups")
        batch = []
        for page in paginator.paginate():
            for g in page.get("logGroups", []):
                name = g["logGroupName"]
                ok   = g.get("retentionInDays") is not None
                batch.append({
                    "ComplianceResourceType": "AWS::Logs::LogGroup",
                    "ComplianceResourceId":   name,
                    "ComplianceType":         "COMPLIANT" if ok else "NON_COMPLIANT",
                    "Annotation":             "Retention is set." if ok else "Retention is NOT set.",
                    "OrderingTimestamp":      datetime.datetime.now(datetime.timezone.utc)
                })
                if len(batch) == 100:
                    config.put_evaluations(Evaluations=batch, ResultToken=token)
                    batch = []
        if batch:
            config.put_evaluations(Evaluations=batch, ResultToken=token)

    else:
        config.put_evaluations(Evaluations=[], ResultToken=token)
