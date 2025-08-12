#!/usr/bin/env python3
import boto3
import botocore
import csv
import os
import sys
import configparser
from datetime import datetime
from botocore.config import Config

OUTDIR = "outputs"
OUTFILE = f"public_ec2_instances_{datetime.today().strftime('%Y-%m-%d')}.csv"

# ---------- Profiles ----------
def list_profiles():
    """
    Discover profiles from ~/.aws/config.
    """
    cfg_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(cfg_path)

    profiles = set()
    # Include the default profile if usable
    for section in config.sections():
        if section.startswith("profile "):
            profiles.add(section.split("profile ", 1)[1])
    return sorted(p for p in profiles if p)

def valid_session(profile):
    """
    Build a session & quickly validate by calling STS GetCallerIdentity.
    Return (session, account_id, arn) or (None, None, None) on failure.
    """
    try:
        session = boto3.Session(profile_name=profile)
        sts = session.client("sts")
        ident = sts.get_caller_identity()
        return session, ident.get("Account"), ident.get("Arn")
    except botocore.exceptions.PartialCredentialsError:
        print(f"[!] Incomplete credentials for profile: {profile}")
    except botocore.exceptions.NoCredentialsError:
        print(f"[!] No credentials found for profile: {profile}")
    except botocore.exceptions.ClientError as e:
        print(f"[!] ClientError validating {profile}: {e}")
    except Exception as e:
        print(f"[!] Unexpected error validating {profile}: {e}")
    return None, None, None

# ---------- EC2 Helpers ----------
def list_regions(session):
    ec2 = session.client("ec2")
    resp = ec2.describe_regions(AllRegions=False)
    return [r["RegionName"] for r in resp["Regions"]]

def build_rtb_maps(ec2_client):
    """
    Return:
      - subnet_to_rtb: map SubnetId -> RouteTable (object)
      - vpc_to_main_rtb: map VpcId -> main RouteTable (object)
    """
    subnet_to_rtb = {}
    vpc_to_main_rtb = {}

    paginator = ec2_client.get_paginator("describe_route_tables")
    for page in paginator.paginate():
        for rtb in page["RouteTables"]:
            # Associations tell us if this RTB is main or subnet-specific
            for assoc in rtb.get("Associations", []):
                if assoc.get("Main"):
                    vpc_to_main_rtb[rtb["VpcId"]] = rtb
                if "SubnetId" in assoc:
                    subnet_to_rtb[assoc["SubnetId"]] = rtb
    return subnet_to_rtb, vpc_to_main_rtb

def rtb_has_public_default_route(rtb):
    """
    True if RTB has 0.0.0.0/0 -> igw-... (IPv4).
    Also consider IPv6 ::/0 -> igw-... (optional).
    """
    if not rtb:
        return False
    for route in rtb.get("Routes", []):
        if route.get("DestinationCidrBlock") == "0.0.0.0/0" and str(route.get("GatewayId", "")).startswith("igw-"):
            return True
        if route.get("DestinationIpv6CidrBlock") == "::/0" and str(route.get("GatewayId", "")).startswith("igw-"):
            return True
    return False

def gather_public_instances_for_region(ec2, region):
    """
    Return rows for this region (list of dicts).
    """
    rows = []
    subnet_to_rtb, vpc_to_main_rtb = build_rtb_maps(ec2)

    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for res in page.get("Reservations", []):
            for inst in res.get("Instances", []):
                state = (inst.get("State") or {}).get("Name")
                if state in ("shutting-down", "terminated"):
                    continue

                public_ip = inst.get("PublicIpAddress")
                if not public_ip:
                    continue  # must have a public IPv4

                vpc_id = inst.get("VpcId", "")
                subnet_id = inst.get("SubnetId", "")
                # effective RTB
                rtb = subnet_to_rtb.get(subnet_id) or vpc_to_main_rtb.get(vpc_id)

                if not rtb_has_public_default_route(rtb):
                    continue  # not internet-routable

                # tags
                name = ""
                for t in inst.get("Tags", []) or []:
                    if t.get("Key") == "Name":
                        name = t.get("Value", "")
                        break

                rows.append({
                    "Region": region,
                    "InstanceId": inst["InstanceId"],
                    "Name": name,
                    "State": state or "",
                    "VPC": vpc_id,
                    "Subnet": subnet_id,
                    "PrivateIp": inst.get("PrivateIpAddress", ""),
                    "PublicIp": public_ip,
                    "PublicDns": inst.get("PublicDnsName", ""),
                    "SecurityGroups": ",".join([sg.get("GroupName","") for sg in inst.get("SecurityGroups", [])]),
                    "IamInstanceProfile": (inst.get("IamInstanceProfile") or {}).get("Arn", "")
                })
    return rows

# ---------- Orchestration ----------
def scan_profile(profile):
    print(f"\n[*] Profile: {profile}")
    session, account_id, arn = valid_session(profile)
    if not session:
        print(f"[!] Skipping profile {profile}")
        return []

    print(f"[+] Authenticated as {arn} (Account {account_id})")
    results = []

    try:
        regions = list_regions(session)
    except Exception as e:
        print(f"[!] Could not list regions for {profile}: {e}")
        return results

    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region, config=Config(retries={"max_attempts": 10, "mode": "standard"}))
            rows = gather_public_instances_for_region(ec2, region)
            # add account/profile metadata
            for r in rows:
                r["Profile"] = profile
                r["AccountId"] = account_id
            if rows:
                print(f"    [+] {region}: {len(rows)} public instance(s)")
            results.extend(rows)
        except botocore.exceptions.ClientError as e:
            print(f"    [!] {region}: ClientError: {e}")
        except Exception as e:
            print(f"    [!] {region}: Unexpected error: {e}")

    return results

def write_csv(rows):
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, OUTFILE)
    fields = [
        "Profile","AccountId","Region","InstanceId","Name","State",
        "VPC","Subnet","PrivateIp","PublicIp","PublicDns","SecurityGroups","IamInstanceProfile"
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"\n[+] Wrote {len(rows)} rows → {path}")

def main():
    print("[*] Scanning all local AWS profiles for PUBLIC EC2 instances...")
    profiles = list_profiles()
    if not profiles:
        print("[!] No profiles found in ~/.aws/config")
        sys.exit(1)

    all_rows = []
    for profile in profiles:
        all_rows.extend(scan_profile(profile))

    if all_rows:
        write_csv(all_rows)
    else:
        print("[+] No public EC2 instances found across scanned profiles.")

if __name__ == "__main__":
    main()
