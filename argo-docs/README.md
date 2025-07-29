# How to Use ArgoCD Notification API

## Overview

The ArgoCD Notification API allows users to configure GitHub notifications for their ArgoCD instances using a secure and templated approach. This enables teams to receive feedback on sync events (success or failure) directly in GitHub through pull request comments or statuses.

> **Note:** As of now, only GitHub notifications are supported. Email and Microsoft Teams will be available in future versions.

Notifications are scoped by ArgoCD instance using a combination of:

- `trigram`: A short identifier of the instance (e.g., `jmf`)
- `code`: An internal reference or application code (e.g., `a1975`)

---

## Why Use Notification Templates Over Manual GitHub Hooks?

### Advantages:

- **Security:** GitHub Apps offer scoped permissions and short-lived tokens.
- **Central Management:** Credentials and templates can be updated or revoked centrally.
- **User Independence:** Actions are performed by the app, not tied to a user account.
- **Auditability:** All automated events are traceable.
- **Reusability:** Templates can be reused across different applications in the same instance.

---

## Credential Management

### 1. Create or Update Notification Credentials

**Endpoint:**

```
POST /instances/{trigram}-{code}/notifications/credentials
```

**Supported service types:**

- `github` _(currently only this one is supported)_

**Request Body Example:**

```json
{
  "github": {
    "app_id": "123456",
    "installation_id": "654321",
    "private_key": "-----BEGIN PRIVATE KEY-----\n..."
  }
}
```

- Credentials are created **or updated** if they already exist.
- These are required before using any GitHub notification templates.

### 2. Delete Notification Credentials

**Endpoint:**

```
DELETE /instances/{trigram}-{code}/notifications/credentials?notification_credential_service_type={service}
```

**Query Parameter:**

- `notification_credential_service_type` = `github`, `email`, `teams`, or `all`

Use this to revoke a specific service’s credentials or all of them.

---

## Notification Templates

Templates define how the notification message is rendered and to which GitHub feature it will be sent (e.g., PR comment, status).

### ⚠️ Prerequisite

Notification credentials **must be created first**, otherwise a `403 Forbidden` or `500 Internal Server Error` may occur.

### 1. Create or Update Notification Templates

**Endpoint:**

```
POST /instances/{trigram}-{code}/notifications/templates
```

**Supported Template Types:**

- `app-sync-succeeded`
- `app-sync-failed`

**Request Body Example:**

```json
{
  "app-sync-failed": {
    "github": {
      "pullRequestComment": {
        "content": "Application APP_NAME sync failed.\nSee more here: ARGOCD_URL/applications/APP_NAME?operation=true"
      },
      "status": {
        "label": "argo-cd/APP_NAME"
      }
    },
    "message": "Application APP_NAME sync failed."
  }
}
```

**Field Rules:**

- `message` is **required**.
- At least one of the two GitHub sections must be provided:

  - `pullRequestComment.content`
  - `status.label`

- Other fields like `state` and `targetURL` are **auto-generated**:

  - `state`: `success` or `failure`
  - `targetURL`: Link to the ArgoCD app view

**Dynamic Variables:**

- `APP_NAME` → auto-replaced with application name
- `ARGOCD_URL` → replaced with the ArgoCD base URL

### 2. Get Notification Templates

**Endpoint:**

```
GET /instances/{trigram}-{code}/notifications/templates
```

**Returns:**

- 200: JSON list of templates
- 403: Credentials missing or access denied
- 500: Internal error

### 3. Delete a Notification Template

**Endpoint:**

```
DELETE /instances/{trigram}-{code}/notifications/templates?notification_template_type={type}
```

**Query Parameter:**

- `notification_template_type` = `app-sync-succeeded` or `app-sync-failed`

**Response:**

- 200: Deleted successfully
- 400: Invalid or missing type

---

## Example Workflow

1. ✅ Create GitHub credentials:

```bash
POST /instances/jmf-a1975/notifications/credentials
```

2. ✅ Create `app-sync-succeeded` template

```bash
POST /instances/jmf-a1975/notifications/templates
```

3. 👁️ View templates:

```bash
GET /instances/jmf-a1975/notifications/templates
```

4. 🗑️ Delete `app-sync-failed` template:

```bash
DELETE /instances/jmf-a1975/notifications/templates?notification_template_type=app-sync-failed
```

5. 🗑️ Delete GitHub credentials:

```bash
DELETE /instances/jmf-a1975/notifications/credentials?notification_credential_service_type=github
```

---

## Roadmap (Upcoming Features)

- Support for **email** and **Microsoft Teams**
- Template validation with improved UI
- Extended GitHub features (e.g., check-runs, deployment statuses)

---

For any support or integration questions, please contact the SYD team via the internal support portal.

> **Last updated:** July 2025
