#!/usr/bin/env python3
import argparse
import csv
import os
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import boto3
from botocore.config import Config

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNTRIAGED"]

# ---------- Inspector fetching ----------

def list_findings_for_instance(inspector2, instance_id: str) -> List[Dict]:
    """
    Retrieves ACTIVE Inspector V2 findings for a specific EC2 instance ID.
    Uses the proper resourceType and paginates.
    """
    findings = []
    next_token = None
    base = {
        "filterCriteria": {
            "resourceId": [{"comparison": "EQUALS", "value": instance_id}],
            "resourceType": [{"comparison": "EQUALS", "value": "AWS_EC2_INSTANCE"}],
            "findingStatus": [{"comparison": "EQUALS", "value": "ACTIVE"}],
        },
        "maxResults": 100,
    }
    while True:
        params = dict(base, **({"nextToken": next_token} if next_token else {}))
        resp = inspector2.list_findings(**params)
        findings.extend(resp.get("findings", []))
        next_token = resp.get("nextToken")
        if not next_token:
            break
    return findings

# ---------- Summaries & helpers ----------

def severity_summary(findings: List[Dict]) -> Counter:
    counter = Counter()
    for f in findings:
        counter[f.get("severity", "UNTRIAGED")] += 1
    for s in SEVERITY_ORDER:
        counter.setdefault(s, 0)
    return counter

def print_severity_table(counter: Counter):
    print("\n== Severity summary ==")
    total = sum(counter.values())
    print(f"Total findings: {total}")
    for s in SEVERITY_ORDER:
        print(f"  {s:<13} {counter[s]}")

def fix_available_summary(findings: List[Dict]) -> Counter:
    counts = Counter()
    for f in findings:
        pvd = f.get("packageVulnerabilityDetails") or {}
        val = (pvd.get("fixAvailable") or "UNKNOWN").upper()
        counts[val] += 1
    for k in ["YES", "NO", "PARTIAL", "UNKNOWN"]:
        counts.setdefault(k, 0)
    return counts

def print_fix_available_table(counts: Counter):
    print("\n== Fix availability ==")
    total = sum(counts.values())
    print(f"Total findings: {total}")
    print(f"  YES:      {counts['YES']}")
    print(f"  NO:       {counts['NO']}")
    print(f"  PARTIAL:  {counts['PARTIAL']}")
    print(f"  UNKNOWN:  {counts['UNKNOWN']}")

def normalize_action_text(txt: str) -> str:
    if not txt:
        return "No official remediation available (manual review)"
    return " ".join(txt.split())  # collapse whitespace

def get_action_text(f: Dict) -> str:
    """
    Prefer top-level remediation.recommendation.text.
    If missing/None Provided, fall back to packageVulnerabilityDetails.remediation.
    """
    rec_text = (((f.get("remediation") or {}).get("recommendation") or {}).get("text") or "").strip()
    if rec_text and rec_text.lower() not in {"none provided", "no recommendation provided"}:
        return rec_text

    pvd = f.get("packageVulnerabilityDetails") or {}
    pkg_rem = (pvd.get("remediation") or "").strip()
    if pkg_rem:
        return pkg_rem

    return "No official remediation available (manual review)"

def action_buckets(findings: List[Dict]) -> Dict[str, Counter]:
    buckets: Dict[str, Counter] = defaultdict(Counter)
    for f in findings:
        action = normalize_action_text(get_action_text(f))
        sev = f.get("severity", "UNTRIAGED")
        buckets[action][sev] += 1
    for action in buckets:
        for s in SEVERITY_ORDER:
            buckets[action].setdefault(s, 0)
    return buckets

def print_actions_table(buckets: Dict[str, Counter], top_n: int = 25):
    print("\n== Top remediation actions (by total findings solved) ==")
    ranked = sorted(buckets.items(), key=lambda kv: sum(kv[1].values()), reverse=True)
    if not ranked:
        print("No actionable recommendations found.")
        return
    for i, (action, sev_counts) in enumerate(ranked[:top_n], 1):
        total = sum(sev_counts.values())
        print(f"\nAction {i}: {action}")
        print(f"  Resolves total: {total}")
        for s in SEVERITY_ORDER:
            print(f"    {s:<13} {sev_counts[s]}")

def extract_pkg_summary(f: Dict) -> Tuple[str, str, str]:
    pvd = f.get("packageVulnerabilityDetails") or {}
    vul_pkgs = pvd.get("vulnerablePackages") or []
    if not vul_pkgs:
        return ("", "", "")
    names = sorted({p.get("name") or "" for p in vul_pkgs if p})
    installed = sorted({p.get("version") or "" for p in vul_pkgs if p})
    fixed_bys = sorted({p.get("fixedInVersion") or "" for p in vul_pkgs if p and p.get("fixedInVersion")})
    return (
        ";".join([n for n in names if n]),
        ";".join([v for v in installed if v]),
        ";".join([fv for fv in fixed_bys if fv]),
    )

# ---------- CSV exporter ----------

def write_csv(findings: List[Dict], out_path: str):
    fieldnames = [
        "findingArn",
        "title",
        "severity",
        "inspectorScore",
        "fixAvailable",
        "actionText",
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
            pvd = f.get("packageVulnerabilityDetails") or {}
            fix_available = (pvd.get("fixAvailable") or "UNKNOWN")
            action_text = get_action_text(f)
            rec_url = (((f.get("remediation") or {}).get("recommendation") or {}).get("url") or "")
            cves = (pvd.get("cvEs") or [])
            cve_id = ";".join(sorted({c.get("id") for c in cves if c and c.get("id")})) if cves else ""
            pkg_names, installed, fixed = extract_pkg_summary(f)
            res = (f.get("resources") or [{}])[0]

            row = {
                "findingArn": f.get("findingArn", ""),
                "title": f.get("title", ""),
                "severity": f.get("severity", ""),
                "inspectorScore": f.get("inspectorScore", ""),
                "fixAvailable": fix_available,
                "actionText": action_text,
                "recommendationUrl": rec_url,
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

# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Generate Inspector v2 vulnerability report for an EC2 instance.")
    parser.add_argument("instance_id", help="EC2 instance ID (e.g., i-0123456789abcdef0)")
    parser.add_argument("--profile", default=os.getenv("AWS_PROFILE", "mwt-security"),
                        help="AWS named profile to use (default: mwt-security)")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
                        help="AWS region (must match where findings exist)")
    parser.add_argument("--out", default="inspector_report.csv", help="CSV output path")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    inspector2 = session.client("inspector2", config=Config(retries={"max_attempts": 10, "mode": "standard"}))

    print(f"Using profile '{args.profile}', region '{args.region}'")
    print(f"Fetching ACTIVE Inspector findings for instance: {args.instance_id} ...")

    findings = list_findings_for_instance(inspector2, args.instance_id)
    if not findings:
        print("No ACTIVE findings found for this instance.")
        return

    # Severity table
    sev_counts = severity_summary(findings)
    print_severity_table(sev_counts)

    # Fix availability table
    fa_counts = fix_available_summary(findings)
    print_fix_available_table(fa_counts)

    # Actions table (with fallback logic)
    buckets = action_buckets(findings)
    print_actions_table(buckets, top_n=25)

    # CSV
    write_csv(findings, args.out)
    print(f"\nDetailed CSV written to: {args.out}")

if __name__ == "__main__":
    main()
