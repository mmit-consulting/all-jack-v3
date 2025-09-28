# How to Use

### 1. Export credentials once per session:

**Option 1: with profile**

```bash
export AWS_PROFILE=mwt-hoopla
```

**Option 2: with raw creds**

```bash
export AWS_ACCESS_KEY_ID=AKIAxxxx
export AWS_SECRET_ACCESS_KEY=yyyyyyyy
export AWS_SESSION_TOKEN=zzzzzzzz  
```

### 2. Run the script:

- Default 90 days:

```bash
./apply_log_retention.sh
```

- Custom retention (e.g., 120 days):

```bash
./apply_log_retention.sh 120
```

### 3. Check the generated CSV report:
Check (`retention_report_<profile>_timestamp.csv`) to see which groups were updated.