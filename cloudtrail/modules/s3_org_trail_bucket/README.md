# S3 Organizational Cloud Trail Bucket

**Purpose**: Create the **central S3 bucket** in mwt-log with:

- Object Ownership = **BucketOwnerEnforced** (ACLs disabled)
- Block Public Access ON
- Default encryption (SSE-S3 by default)
- Lifecycle (30d => INTELLIGENT_TIERING, expire 1095d)
- **Bucket policy** that allows writes from the **org trail** to both path layouts:
  - `AWSLogs/<mgmt-account-id>/*`
  - `o-<OrgId>/AWSLogs/* and AWSLogs/o-<OrgId>/*`
  - constrained by `aws:SourceArn` to your trail
