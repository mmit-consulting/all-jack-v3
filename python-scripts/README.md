# Multi-Profile Public EC2 Detection Script — Explanation

## **Purpose**
This script scans **all AWS CLI profiles** configured on the local machine and checks **only in `us-east-1`** for EC2 instances that are **truly public** — meaning they:
1. Have a **public IPv4 address**.
2. Are in a subnet whose route table has a **default route (0.0.0.0/0)** to an **Internet Gateway (igw-...)**.

It then writes the results to a **CSV file** in the `outputs/` directory.

---

## **Step-by-Step Process**

### **1. Load AWS CLI Profiles**
- **Function:** `list_profiles()`
- Reads `~/.aws/config` to collect all configured profiles.
- Allows the script to loop through **multiple AWS accounts** without manually switching credentials.

---

### **2. Validate AWS Session**
- **Function:** `valid_session(profile)`
- Creates a session using `boto3.Session(profile_name=...)`.
- Calls `sts.get_caller_identity()` to:
  - Confirm credentials work.
  - Retrieve **Account ID** and **ARN**.
- If validation fails (invalid/missing credentials), the profile is skipped.

---

### **3. Fixed Region Scan**
- Inside `scan_profile()`:
  ```python
  regions = ["us-east-1"]
The script only scans us-east-1, instead of looping through all regions.

### **4. Gather Route Table Information**
- Function: build_rtb_maps(ec2_client)
- Retrieves all route tables for the region.
- Creates two mappings:
  - subnet_to_rtb → Route table explicitly associated with a subnet.
  - vpc_to_main_rtb → Main/default route table for each VPC.
 ### **5. Check for Public Access Route**
 - Function: rtb_has_public_default_route(rtb)
 - Looks for:
    - IPv4 route 0.0.0.0/0 → igw-...
    - IPv6 route ::/0 → igw-... (optional)
- If no such route exists, the instance is not considered public.
### **6. List and Filter Instances**
- Function: gather_public_instances_for_region(ec2, region)
- Retrieves all EC2 instances.
- Skips:
  - Terminated/shutting-down instances.
  - Instances without a public IPv4.
- Determines the route table that applies to the subnet.
- Confirms if the route table allows public internet access.
### **7. Save Results to CSV**
- Function: write_csv(rows)
- Creates outputs/public_ec2_instances_YYYY-MM-DD.csv.
- Each row = one public EC2 instance.

