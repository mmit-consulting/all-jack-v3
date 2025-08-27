export AWS_PROFILE=mwt-security

# 2) Run the script (you can also pass --profile explicitly)

python3 inspector_ec2_report.py i-0123456789abcdef0 --region us-east-2 --out inspector_report.csv
