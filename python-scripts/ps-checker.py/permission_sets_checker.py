#!/usr/bin/env python3
"""
Scan AWS Identity Center (SSO) permission sets' inline policies and report any
statements that contain actions 's3:*' or 'iam:*'.

Outputs CSV rows:
permission_set, action, effect, resources

Usage examples:
  python scan_ic_permission_sets.py \
    --profile mwt-master \
    --region us-east-1 \
    --out permission_set_wildcards.csv
"""

import argparse
import csv
import json
from typing import Iterable, List, Tuple, Union

import boto3
from botocore.exceptions import ClientError


def to_list(x: Union[str, List[str], None]) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def normalize_statements(policy_doc: dict) -> List[dict]:
    stmt = policy_doc.get("Statement", [])
    if isinstance(stmt, list):
        return stmt
    elif isinstance(stmt, dict):
        return [stmt]
    return []


def extract_resources(stmt: dict) -> List[str]:
    # Prefer Resource; if absent, fall back to NotResource (less common).
    resources = to_list(stmt.get("Resource"))
    if not resources:
        resources = to_list(stmt.get("NotResource"))
    if not resources:
        resources = ["*"]
    return resources


def matching_actions(stmt_actions: Iterable[str]) -> List[str]:
    """
    Return which of the target wildcards ('s3:*', 'iam:*') are present
    in the statement's Action list. Case-insensitive comparison.
    """
    targets = {"s3:*", "iam:*"}
    found = set()
    for a in stmt_actions:
        a_norm = str(a).strip().lower()
        if a_norm in targets:
            found.add(a_norm)
    return sorted(found)


def scan_permission_sets(profile: str, region: str) -> List[Tuple[str, str, str, List[str]]]:
    """
    Returns a list of rows: (permission_set_name, matched_action, effect, resources)
    """
    session = boto3.Session(profile_name=profile, region_name=region)
    sso_admin = session.client("sso-admin")

    # Get Identity Center instance ARN
    try:
        instances = sso_admin.list_instances()["Instances"]
    except ClientError as e:
        raise SystemExit(f"Failed to list Identity Center instances in {region}: {e}")

    if not instances:
        raise SystemExit(f"No Identity Center instances found in region {region}. "
                         f"Double-check the region where your Identity Center is deployed.")

    instance_arn = instances[0]["InstanceArn"]

    # Paginate permission sets
    psets: List[str] = []
    token = None
    while True:
        kwargs = {"InstanceArn": instance_arn}
        if token:
            kwargs["NextToken"] = token
        resp = sso_admin.list_permission_sets(**kwargs)
        psets.extend(resp.get("PermissionSets", []))
        token = resp.get("NextToken")
        if not token:
            break

    rows: List[Tuple[str, str, str, List[str]]] = []

    for ps_arn in psets:
        # Resolve permission set name
        try:
            desc = sso_admin.describe_permission_set(InstanceArn=instance_arn, PermissionSetArn=ps_arn)
            ps_name = desc["PermissionSet"]["Name"]
        except ClientError as e:
            # If we can't get the name, fall back to ARN tail
            ps_name = ps_arn.split("/")[-1]
            print(f"Warning: failed to describe permission set {ps_arn}: {e}")

        # Get inline policy (stringified JSON). If none, skip.
        try:
            getp = sso_admin.get_inline_policy_for_permission_set(
                InstanceArn=instance_arn, PermissionSetArn=ps_arn
            )
        except sso_admin.exceptions.ResourceNotFoundException:
            # Some orgs see this when there is no inline policy at all.
            continue
        except ClientError as e:
            print(f"Warning: failed to get inline policy for {ps_name}: {e}")
            continue

        policy_str = getp.get("InlinePolicy")
        if not policy_str:
            continue

        try:
            policy_doc = json.loads(policy_str)
        except json.JSONDecodeError as e:
            print(f"Warning: {ps_name} has invalid inline policy JSON: {e}")
            continue

        statements = normalize_statements(policy_doc)
        for stmt in statements:
            effect = str(stmt.get("Effect", "Allow"))
            # Only consider explicit Action; ignore NotAction for this report.
            actions = to_list(stmt.get("Action"))
            if not actions:
                continue

            # Determine if this statement has s3:* or iam:*
            hits = matching_actions(actions)
            if not hits:
                continue

            res_list = extract_resources(stmt)

            # If both s3:* and iam:* appear, emit a row for each
            for hit in hits:
                # Keep action as originally requested form (service in lower is standard)
                rows.append((ps_name, hit, effect, res_list))

    return rows


def main():
    parser = argparse.ArgumentParser(description="Report s3:* and iam:* in Identity Center permission set inline policies.")
    parser.add_argument("--profile", default="mwt-master", help="AWS profile to use (default: mwt-master)")
    parser.add_argument("--region", required=True, help="Region where AWS Identity Center is set up (e.g., us-east-1)")
    parser.add_argument("--out", default="permission_set_wildcards.csv", help="Output CSV file path")
    args = parser.parse_args()

    rows = scan_permission_sets(profile=args.profile, region=args.region)

    # Write CSV
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["permission_set", "action", "effect", "resources"])
        for ps_name, action, effect, resources in rows:
            writer.writerow([ps_name, action, effect, ";".join(resources)])

    print(f"Wrote {len(rows)} row(s) to {args.out}")


if __name__ == "__main__":
    main()
