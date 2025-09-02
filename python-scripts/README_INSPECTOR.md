Inspector EC2 Report — Usage Guide

Overview
- Purpose: Summarize AWS Inspector v2 EC2 findings into actionable remediation steps. It prints a per-instance section with the list of remediation actions and how many findings each action would resolve.
- Scope: Works for a single EC2 instance or across all EC2 instances visible to the configured profile (e.g., an aggregated security account like `mwt-security`).

Prerequisites
- Python 3.8+
- boto3 installed
- AWS credentials with Inspector2 permissions (at least `inspector2:ListFindings`) for the target accounts/regions

Setup
- Optional (recommended): create a virtualenv and install dependencies
  - `python3 -m venv venv && source venv/bin/activate`
  - `pip install boto3`
- Set your AWS profile (defaults to `mwt-security` if not provided)
  - `export AWS_PROFILE=mwt-security`

Script Location
- `python-scripts/inspector_ec2_report.py`

Basic Usage
1) Single instance (totals-only actions for the given instance)
- `python3 python-scripts/inspector_ec2_report.py i-0123456789abcdef0 --region us-east-1`

2) All instances (totals-only actions per instance)
- `python3 python-scripts/inspector_ec2_report.py --all --region us-east-1`

Helpful Flags
- `--profile`: AWS named profile to use (default: `mwt-security`)
- `--region`: Inspector v2 region to query (default: `us-east-1`)
- `--top-n`: Limit the number of actions printed per instance (default: 25). Use `--top-n 0` to show all actions.
- `--csv-out`: Write a detailed CSV of raw findings for further analysis. In `--all` mode, writes all findings; in single-instance mode, only that instance’s findings.

Examples
- All instances, show top 25 actions per instance:
  - `python3 python-scripts/inspector_ec2_report.py --all --profile mwt-security --region us-east-1`
- All instances, show all actions and write a CSV:
  - `python3 python-scripts/inspector_ec2_report.py --all --top-n 0 --csv-out inspector_all.csv`
- Single instance, show all actions and write a CSV:
  - `python3 python-scripts/inspector_ec2_report.py i-0abc123def4567890 --top-n 0 --csv-out inspector_single.csv`

What The Output Looks Like
- For each instance, the script prints a separator line and a header that includes the instance ID and the AWS account ID. Below that, it lists remediation actions with the number of findings each would resolve.

Example (truncated):
================================================================================
Instance: i-0abc123def4567890 | Account: 123456789012 | Findings: 84

== Top remediation actions (by total findings solved) ==

Action 1: Update OpenSSL to a fixed version
  Resolves total: 31

Action 2: Apply security updates via OS package manager
  Resolves total: 22

Action 3: Upgrade curl to >= 7.88.0
  Resolves total: 9

Notes & Limitations
- Aggregated accounts: If running from a security/aggregator account (e.g., `mwt-security`), findings from multiple member accounts are grouped per instance and labeled with the member AWS account ID.
- Region: Inspector v2 findings are regional. Run the script per region that has scans enabled.
- Status filter: Only ACTIVE findings are included.
- Output focus: Console output is action totals only. Use `--csv-out` if you need all fields (CVE IDs, packages, versions, URLs, timestamps, etc.).

Troubleshooting
- No findings returned:
  - Ensure Inspector v2 is enabled in the region and scanning EC2 instances.
  - Verify the instance is covered by Inspector and has ACTIVE findings.
  - Confirm the selected profile has permissions and access to the account/member accounts.
- Throttling or intermittent errors:
  - The client uses standard retry configuration, but you can rerun or scope with single-instance mode.
