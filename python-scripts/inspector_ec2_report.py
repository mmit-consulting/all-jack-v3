#!/usr/bin/env python3
import argparse
import csv
import os
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import boto3
from botocore.config import Config

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNTRIAGED"]

def list_findings_for_instance(inspector2, instance_id: str, region: str) -> List[Dict]:
    """
    Retrieves ACTIVE Inspector V2 findings for a specific EC2 instance ID.
    """
    findings = []
    next_token = None
    while True:
        params = {
            "filterCriteria": {
                "resourceId": [{"comparison": "EQUALS", "value": instance_id}],
                "resourceType": [{"comparison": "EQUALS", "value": "EC2_INSTANCE"}],
                "findingStatus": [{"comparison": "EQUALS", "value": "ACTIVE"}],
            },
            "maxResults": 100,
        }
        if next_token:
            params["nextToken"] = next_token

        resp = inspector2.list_findings(**params)
        findings.extend(resp.get("findings", []))
        next_token = resp.get("nextToken")
        if not next_token:
            break
    return findings

def severity_summary(findings: List[Dict]) -> Counter:
    counter = Counter()
    for f in findings:
        counter[f.get("severity", "UNTRIAGED")] += 1
    # Ensure all keys exist (even if zero) for a predictable table
    for s in SEVERITY_ORDER:
        counter.setdefault(s, 0)
    return counter

def normalize_action_text(txt: str) -> str:
    """
    Try to normalize recommendation text so similar actions group together.
    This is intentionally conservative; you can enrich later (e.g., strip versions).
    """
    if not txt:
        return "No specific recommendation"
    return " ".join(txt.split())  # collapse spacing

def action_buckets(findings: List[Dict]) -> Dict[str, Counter]:
    """
    Group findings by the remediation recommendation text (i.e., the 'action'),
    counting severities per action.
    """
    buckets: Dict[str, Counter] = defaultdict(Counter)
    for f in findings:
        rec = (f.get("remediation") or {}).get("recommendation") or {}
        action = normalize_action_text(rec.get("text") or "")
        sev = f.get("severity", "UNTRIAGED")
        buckets[action][sev] += 1
    # ensure severity keys present
    for action in buckets:
        for s in SEVERITY_ORDER:
            buckets[action].setdefault(s, 0)
    return buckets

def extract_pkg_summary(f: Dict) -> Tuple[str, str, str]:
    """
    Pull a concise package summary (name, installed, fixedBy) when available.
    Many findings are package vulns; if multiple, take a readable aggregate.
    """
    pvd = f.get("packageVulnerabilityDetails") or {}
    vul_pkgs = pvd.get("vulnerablePackages") or []
    if not vul_pkgs:
        return ("", "", "")
    # Gather unique names and target versions
    names = sorted({p.get("name") or "" for p in vul_pkgs if p})
    fixed_bys = sorted({p.get("fixedInVersion") or "" for p in vul_pkgs if p and p.get("fixedInVersion")})
    installed = sorted({p.get("version") or "" for p in vul_pkgs if p})
    return (
        ";".join([n for n in names if n]),
        ";".join([v for v in installed if v]),
        ";".join([fv for fv in fixed_bys if fv]),
    )

def write_csv(findings: List[Dict], out_path: str):
    """
    Write a detailed CSV report of findings.
    """
    fieldnames = [
        "findingArn",
        "title",
        "severity",
        "inspectorScore",
        "fixAvailable",
        "recommendation",
        "recommendationUrl",
        "cveId",
        "packageNames",
        "installedVersions",
        "fixedInVersions",
        "resourceId",
        "resourceRegion",
        "firstObservedAt",
        "lastObservedAt",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for f in findings:
            rem = (f.get("remediation") or {}).get("recommendation") or {}
            pvd = f.get("packageVulnerabilityDetails") or {}
            cves = pvd.get("cvEs") or []  # list of dicts with id/refs
            cve_id = ";".join(sorted({c.get("id") for c in cves if c and c.get("id")})) if cves else ""
            pkg_names, installed, fixed = extract_pkg_summary(f)

            # Resources often includes the EC2 instance with id, region, etc.
            res = (f.get("resources") or [{}])[0]
            row = {
                "findingArn": f.get("findingArn", ""),
                "title": f.get("title", ""),
                "severity": f.get("severity", ""),
                "inspectorScore": f.get("inspectorScore", ""),
                "fixAvailable": (pvd.get("fixAvailable") or "UNKNOWN"),
                "recommendation": rem.get("text", ""),
                "recommendationUrl": rem.get("url", ""),
                "cveId": cve_id,
                "packageNames": pkg_names,
                "installedVersions": installed,
                "fixedInVersions": fixed,
                "resourceId": res.get("id", ""),
                "resourceRegion": res.get("region", ""),
                "firstObservedAt": f.get("firstObservedAt", ""),
                "lastObservedAt": f.get("lastObservedAt", ""),
            }
            w.writerow(row)

def print_severity_table(counter: Counter):
    print("\n== Severity summary ==")
    total = sum(counter.values())
    print(f"Total findings: {total}")
    for s in SEVERITY_ORDER:
        print(f"  {s:<13} {counter[s]}")

def print_actions_table(buckets: Dict[str, Counter], top_n: int = 25):
    print("\n== Top remediation actions (by total findings solved) ==")
    # rank actions by total findings they would address
    ranked = sorted(
        buckets.items(),
        key=lambda kv: sum(kv[1].values()),
        reverse=True,
    )
    if not ranked:
        print("No actionable recommendations found.")
        return
    for i, (action, sev_counts) in enumerate(ranked[:top_n], 1):
        total = sum(sev_counts.values())
        print(f"\nAction {i}: {action or 'No specific recommendation'}")
        print(f"  Resolves total: {total}")
        for s in SEVERITY_ORDER:
            print(f"    {s:<13} {sev_counts[s]}")

def main():
    parser = argparse.ArgumentParser(description="Generate Inspector v2 vulnerability report for an EC2 instance.")
    parser.add_argument("instance_id", help="EC2 instance ID (e.g., i-0123456789abcdef0)")
    parser.add_argument("--profile", default=os.getenv("AWS_PROFILE", "mwt-security"), help="AWS named profile to use")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
                        help="AWS region for Inspector (must match where the instance is scanned)")
    parser.add_argument("--out", default="inspector_report.csv", help="Path to write the CSV report")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    inspector2 = session.client("inspector2", config=Config(retries={"max_attempts": 10, "mode": "standard"}))

    print(f"Using profile '{args.profile}', region '{args.region}'")
    print(f"Fetching ACTIVE Inspector findings for instance: {args.instance_id} ...")

    findings = list_findings_for_instance(inspector2, args.instance_id, args.region)
    if not findings:
        print("No ACTIVE findings found for this instance.")
        return

    # --- Part 1: Severity summary
    sev_counts = severity_summary(findings)
    print_severity_table(sev_counts)

    # --- Part 2: Group by remediation action
    buckets = action_buckets(findings)
    print_actions_table(buckets, top_n=25)

    # --- CSV for deep-dive
    write_csv(findings, args.out)
    print(f"\nDetailed CSV written to: {args.out}")

if __name__ == "__main__":
    main()
