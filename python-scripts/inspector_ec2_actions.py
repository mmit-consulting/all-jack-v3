#!/usr/bin/env python3
import argparse
import csv
import os
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import boto3
from botocore.config import Config

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "UNTRIAGED"]

# ---------- Debug ----------

def _dbg(msg: str, verbose: bool):
    if verbose:
        print(msg, flush=True)

# ---------- Inspector fetching ----------

def list_findings_for_instance(inspector2, instance_id: str, verbose: bool = False) -> List[Dict]:
    """
    Retrieves ACTIVE Inspector V2 findings for a specific EC2 instance ID.
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
    page = 0
    _dbg(f"[single] Start listing findings for {instance_id}", verbose)
    while True:
        params = dict(base, **({"nextToken": next_token} if next_token else {}))
        page += 1
        _dbg(f"[single] Calling list_findings page {page} ...", verbose)
        resp = inspector2.list_findings(**params)
        got = len(resp.get("findings", []))
        findings.extend(resp.get("findings", []))
        _dbg(f"[single] Page {page} returned {got}, total so far {len(findings)}", verbose)
        next_token = resp.get("nextToken")
        if not next_token:
            break
    _dbg(f"[single] Completed. Total findings: {len(findings)}", verbose)
    return findings


def list_all_active_ec2_findings(inspector2, verbose: bool = False) -> List[Dict]:
    """
    Retrieves all ACTIVE Inspector V2 findings for EC2 instances across the
    account/organization the configured profile can see.
    """
    findings: List[Dict] = []
    next_token = None
    page = 0
    _dbg("[all] Start listing ACTIVE EC2 findings", verbose)
    while True:
        params = {
            "filterCriteria": {
                "resourceType": [{"comparison": "EQUALS", "value": "AWS_EC2_INSTANCE"}],
                "findingStatus": [{"comparison": "EQUALS", "value": "ACTIVE"}],
            },
            "maxResults": 100,
        }
        if next_token:
            params["nextToken"] = next_token

        page += 1
        _dbg(f"[all] Calling list_findings page {page} ...", verbose)
        resp = inspector2.list_findings(**params)
        got = len(resp.get("findings", []))
        findings.extend(resp.get("findings", []))
        _dbg(f"[all] Page {page} returned {got}, total so far {len(findings)}", verbose)
        next_token = resp.get("nextToken")
        if not next_token:
            break
    _dbg(f"[all] Completed listing. Total findings: {len(findings)}", verbose)
    return findings

# ---------- Aggregations ----------

def severity_summary(findings: List[Dict]) -> Counter:
    counter = Counter()
    for f in findings:
        counter[f.get("severity", "UNTRIAGED")] += 1
    for s in SEVERITY_ORDER:
        counter.setdefault(s, 0)
    return counter


def fix_available_summary(findings: List[Dict]) -> Counter:
    """
    Prefer packageVulnerabilityDetails.fixAvailable, otherwise infer:
    if ANY vulnerablePackages[].fixedInVersion exists -> YES, else UNKNOWN.
    """
    counts = Counter()
    for f in findings:
        pvd = f.get("packageVulnerabilityDetails") or {}
        flag = pvd.get("fixAvailable")
        if isinstance(flag, str) and flag:
            counts[flag.upper()] += 1
            continue

        vp = pvd.get("vulnerablePackages") or []
        has_fix = any((p or {}).get("fixedInVersion") for p in vp)
        counts["YES" if has_fix else "UNKNOWN"] += 1

    for k in ["YES", "NO", "PARTIAL", "UNKNOWN"]:
        counts.setdefault(k, 0)
    return counts


def normalize_action_text(txt: str) -> str:
    if not txt:
        return "No official remediation available (manual review)"
    return " ".join(txt.split())


def get_action_text(f: Dict) -> str:
    """
    Choose the best remediation text:
      1) finding.remediation.recommendation.text (unless 'None Provided')
      2) finding.packageVulnerabilityDetails.remediation
      3) any vulnerablePackages[].remediation
      4) synthesize from vulnerablePackages fixed versions
    """
    # 1) top-level recommendation
    rec_text = (((f.get("remediation") or {}).get("recommendation") or {}).get("text") or "").strip()
    if rec_text and rec_text.lower() not in {"none provided", "no recommendation provided"}:
        return rec_text

    # 2) package-level remediation
    pvd = f.get("packageVulnerabilityDetails") or {}
    pkg_level_rem = (pvd.get("remediation") or "").strip()
    if pkg_level_rem:
        return pkg_level_rem

    # 3) per-package remediation
    vp = pvd.get("vulnerablePackages") or []
    rems = set()
    for p in vp:
        rt = (p or {}).get("remediation")
        if rt:
            rems.add(" ".join(rt.split()))
    if rems:
        return sorted(rems)[0]  # usually identical; pick one

    # 4) synthesize from fixed versions
    names = sorted({(p or {}).get("name", "") for p in vp if p})
    fixed = sorted({(p or {}).get("fixedInVersion", "") for p in vp if p and p.get("fixedInVersion")})
    if names and fixed:
        return f"Update packages ({', '.join(n for n in names if n)}) to fixed versions ({', '.join(f for f in fixed if f)})."

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

# ---------- CSV exporters (detailed + per-instance summary) ----------

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


def infer_fix_available_flag(f: Dict) -> str:
    """
    Return the 'best effort' fixAvailable value (YES/NO/PARTIAL/UNKNOWN).
    """
    pvd = f.get("packageVulnerabilityDetails") or {}
    explicit = pvd.get("fixAvailable")
    if isinstance(explicit, str) and explicit:
        return explicit
    vp = pvd.get("vulnerablePackages") or []
    has_fix = any((p or {}).get("fixedInVersion") for p in vp)
    return "YES" if has_fix else "UNKNOWN"


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
    # ensure folder exists
    folder = os.path.dirname(os.path.abspath(out_path))
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for f in findings:
            pvd = f.get("packageVulnerabilityDetails") or {}
            fix_available = infer_fix_available_flag(f)
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


def build_instance_summary_rows(grouped: Dict[Tuple[str, str], List[Dict]]) -> List[Dict]:
    """
    Build one row per instance/account with severity counts and number of actions.
    Columns: account_id, instance_id, total_vulnerabilities, critical, high, medium, low, actions_detected
    """
    rows = []
    for (inst_id, account_id), inst_findings in grouped.items():
        sev = severity_summary(inst_findings)  # ensures keys exist for all severities
        buckets = action_buckets(inst_findings)
        rows.append({
            "account_id": account_id,
            "instance_id": inst_id,
            "total_vulnerabilities": sum(sev.values()),
            "critical": sev.get("CRITICAL", 0),
            "high": sev.get("HIGH", 0),
            "medium": sev.get("MEDIUM", 0),
            "low": sev.get("LOW", 0),
            "actions_detected": len(buckets),
        })
    return rows


def write_instance_summary_csv(rows: List[Dict], out_path: str):
    fieldnames = [
        "account_id",
        "instance_id",
        "total_vulnerabilities",
        "critical",
        "high",
        "medium",
        "low",
        "actions_detected",
    ]
    folder = os.path.dirname(os.path.abspath(out_path))
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---------- Printers ----------

def print_severity_table(counter: Counter):
    print("\n== Severity summary ==")
    total = sum(counter.values())
    print(f"Total findings: {total}")
    for s in SEVERITY_ORDER:
        print(f"  {s:<13} {counter[s]}")


def print_actions_table(buckets: Dict[str, Counter], top_n: int = 25, totals_only: bool = False):
    print("\n== Top remediation actions (by total findings solved) ==")
    ranked = sorted(buckets.items(), key=lambda kv: sum(kv[1].values()), reverse=True)
    if not ranked:
        print("No actionable recommendations found.")
        return
    limit = top_n if (isinstance(top_n, int) and top_n > 0) else len(ranked)
    for i, (action, sev_counts) in enumerate(ranked[:limit], 1):
        total = sum(sev_counts.values())
        print(f"\nAction {i}: {action or 'No specific recommendation'}")
        print(f"  Resolves total: {total}")
        if not totals_only:
            for s in SEVERITY_ORDER:
                print(f"    {s:<13} {sev_counts[s]}")

# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Generate Inspector v2 remediation actions per EC2 instance.")
    parser.add_argument("instance_id", nargs="?", help="EC2 instance ID. If omitted and --all is set, processes all instances.")
    parser.add_argument("--all", action="store_true", help="Process all EC2 instances with ACTIVE findings visible to this profile")
    parser.add_argument("--profile", default=os.getenv("AWS_PROFILE", "mwt-security"), help="AWS named profile to use")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
                        help="AWS region for Inspector (must match where the instance is scanned)")
    parser.add_argument("--csv-out", default=None, help="Optional path to write a detailed CSV of raw findings")
    parser.add_argument("--summary-csv", default=None, help="Optional path to write a per-instance summary CSV (counts & actions)")
    parser.add_argument("--top-n", type=int, default=25, help="Max actions to display per instance (by impact)")
    parser.add_argument("--include-severity", action="store_true", help="Also show per-severity counts for each action")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress while fetching and processing")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    inspector2 = session.client("inspector2", config=Config(retries={"max_attempts": 10, "mode": "standard"}))

    print(f"Using profile '{args.profile}', region '{args.region}'")

    if args.all:
        print("Fetching ACTIVE Inspector findings for ALL EC2 instances ...", flush=True)
        all_findings = list_all_active_ec2_findings(inspector2, verbose=args.verbose)
        if not all_findings:
            print("No ACTIVE EC2 findings found.")
            return

        # Group findings by (instance_id, account_id)
        grouped: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)
        for f in all_findings:
            resources = f.get("resources") or []
            inst_id = None
            for r in resources:
                rtype = (r.get("type") or "").upper()
                if rtype in {"EC2_INSTANCE", "AWS_EC2_INSTANCE"} and r.get("id"):
                    inst_id = r.get("id")
                    break
            if not inst_id and resources:
                inst_id = resources[0].get("id")
            if not inst_id:
                continue
            account_id = f.get("awsAccountId") or (resources[0].get("accountId") if resources else None) or "unknown-account"
            grouped[(inst_id, account_id)].append(f)

        # Print section per instance
        total_instances = len(grouped)
        _dbg(f"[all] Grouped into {total_instances} instances", args.verbose)
        for idx, (inst_id, account_id) in enumerate(sorted(grouped.keys(), key=lambda k: (k[1], k[0])), start=1):
            inst_findings = grouped[(inst_id, account_id)]
            print("\n" + "=" * 80)
            print(f"[{idx}/{total_instances}] Instance: {inst_id} | Account: {account_id} | Findings: {len(inst_findings)}", flush=True)
            buckets = action_buckets(inst_findings)
            print_actions_table(buckets, top_n=args.top_n, totals_only=(not args.include_severity))

        # Optional CSVs
        if args.csv_out:
            write_csv(all_findings, args.csv_out)
            print(f"\nDetailed CSV written to: {args.csv_out}")

        if args.summary_csv:
            summary_rows = build_instance_summary_rows(grouped)
            write_instance_summary_csv(summary_rows, args.summary_csv)
            print(f"Instance summary CSV written to: {args.summary_csv}")

    else:
        if not args.instance_id:
            parser.error("Provide an instance_id or use --all to process all instances")
        print(f"Fetching ACTIVE Inspector findings for instance: {args.instance_id} ...", flush=True)
        findings = list_findings_for_instance(inspector2, args.instance_id, verbose=args.verbose)
        if not findings:
            print("No ACTIVE findings found for this instance.")
            return

        # Print actions
        buckets = action_buckets(findings)
        print("\n" + "=" * 80)
        print(f"Instance: {args.instance_id} | Account: n/a (single-instance mode)")
        print_actions_table(buckets, top_n=args.top_n, totals_only=(not args.include_severity))

        # Optional CSVs
        if args.csv_out:
            write_csv(findings, args.csv_out)
            print(f"\nDetailed CSV written to: {args.csv_out}")

        if args.summary_csv:
            account_id = findings[0].get("awsAccountId") or \
                         ((findings[0].get("resources") or [{}])[0].get("accountId")) or \
                         "unknown-account"
            sev = severity_summary(findings)
            row = {
                "account_id": account_id,
                "instance_id": args.instance_id,
                "total_vulnerabilities": sum(sev.values()),
                "critical": sev.get("CRITICAL", 0),
                "high": sev.get("HIGH", 0),
                "medium": sev.get("MEDIUM", 0),
                "low": sev.get("LOW", 0),
                "actions_detected": len(buckets),
            }
            write_instance_summary_csv([row], args.summary_csv)
            print(f"Instance summary CSV written to: {args.summary_csv}")

if __name__ == "__main__":
    main()