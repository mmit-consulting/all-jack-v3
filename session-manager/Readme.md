# 🧭 Internal Guide: How to Connect to EC2 via AWS SSM (Session Manager)

## 📦 What is SSM?

SSM (AWS Session Manager) lets you **connect to EC2 instances over HTTPS**, no bastion hosts, no SSH, no public IPs.

- ✅ Secure
- ✅ Logged
- ✅ Works via UI and CLI
- ✅ No need for VPN or inbound security group rules

## Requirements

### On EC2 Instnces

| Requirement                   | Status                                               |
| ----------------------------- | ---------------------------------------------------- |
| SSM Agent installed & running | Built-in on Amazin Linux, Ubuntu, Windows.           |
| IAM role attached to EC2      | Must include `AmazonSSMManagedInstanceCore`          |
| Network access to SSM         | Via internet or **VPC endpoints** (already in place) |

NOTE: **Most Amazon Linux, Ubuntu, and Windows AMIs already have it installed.**

If not, follow the official docs:

- Linux: https://docs.aws.amazon.com/systems-manager/latest/userguide/manually-install-ssm-agent-linux.html

- Windows: https://docs.aws.amazon.com/systems-manager/latest/userguide/manually-install-ssm-agent-windows.html

You can also install SSM into your Launch Template so it's baked in by default.

### On Your Local Machine for CLI access (User Requirements)

| Requirement                                  | Notes                                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| AWS CLI v2 installed                         | [Download Link](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| AWS CLI profile configured (`aws configure`) | Access Key, Region, Output format                                                              |
| IAM permissions for SSM access               | See below 👇                                                                                   |

## 🔐 Required IAM Permissions (per use case)

### 🧑‍💻 Basic SSM Connection (Session Manager Only)

These are the **minimum permissions** needed to open an interactive session:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:DescribeInstanceInformation",
        "ssm:GetConnectionStatus",
        "ssm:TerminateSession"
      ],
      "Resource": "*"
    }
  ]
}
```

Ideal for developers and analysts who just need terminal access to EC2

### 🧪 Advanced Usage (Optional)

To send non-interactive commands (like ethe example for DevOps team) (e.g., install software, run scripts, transfer files), add:

```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:SendCommand",
    "ssm:ListCommandInvocations",
    "ssm:GetCommandInvocation"
  ],
  "Resource": "*"
}
```

Add this only if needed. Useful for automations, scripts, file uploads, or remote shell commands.

### Advanced SSM Permissions Breakdown

These permissions relate to **running one-time shell commands** or scripts on EC2 instances via Systems Manager **Documents** (SSM Documents), particularly with:

```bash
aws ssm send-command
```

#### Permission: `ssm:SendCommand`

This is the main action that lets you run a command or script remotely on one or more EC2 instances.

Example Usage:

```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=instanceIds,Values=i-xxxxxxxxxxxx" \
  --parameters 'commands=["uptime"]'
```

Without it, You will get an error like:

```bash
An error occurred (AccessDeniedException) when calling the SendCommand operation
```

#### Permission: `ssm:ListCommandInvocations`

This lets you **list previous commands you've run**, along with their status (e.g., InProgress, Success, Failed).

Example usage:

```bash
aws ssm list-command-invocations --details
```

Without it, You will get an error like:

```bash
You won't be able to see which commands succeeded or failed or even if they ran at all.
```

#### Permission: `ssm:GetCommandInvocation`

This lets you **get the output (stdout/stderr)** of a previously run command on a specific instance.

Example usage:

```bash
aws ssm get-command-invocation \
  --command-id abc12345-xyz \
  --instance-id i-xxxxxxxxxxxxx
```

NOTE: You can retrieve the command-id value directly from the send-command response.

This shows you the command output, like this:

```json
{
  "StandardOutputContent": "Your command's output here",
  "StandardErrorContent": "",
  "Status": "Success"
}
```

Without it, You will get an error like:

```bash
You won't be able to retrieve results of a command after execution.
```

## How to Connect to EC2 Using SSM

### Option 1: AWS Console (Web UI)

Best for first-time users

1. Log in to AWS Console: Session Manager
2. Click Start Session
3. Select your EC2 instance (search by tag or instance ID)
4. Click Start session

### Option 2: AWS CLI (Terminal)

Great for scripting, CI/CD, DevOps workflows

Setup (if not done):

```bash
aws configure
```

Start a session

```bash
aws ssm start-session --target i-xxxxxxxxxxxxxxxxx
```

Replace i-xxxxxxxxxx with the EC2 Instance ID.

❌ Exit:

```bash
exit
```

## Troubleshooting

| ❌ Problem                          | ✅ Fix                                                           |
| ----------------------------------- | ---------------------------------------------------------------- |
| Instance not showing in UI/CLI      | Ensure IAM role has `AmazonSSMManagedInstanceCore`               |
| CLI fails: `AccessDenied`           | Add `ssm:StartSession` and related permissions                   |
| Timeout or stuck session            | EC2 lacks SSM endpoint access (check VPC endpoint or NAT config) |
| Private DNS error creating endpoint | Ensure VPC has `enableDnsSupport` & `enableDnsHostnames = true`  |
| Can't resolve `ssm.amazonaws.com`   | Check VPC DNS settings or endpoint routing                       |
