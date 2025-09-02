# Intercepting Argo CD Actions — Two Approaches

# 1. Fluent Bit / Log Collector Approach

## How it works:

- Enable **audit logging** in `argocd-server`.
- Deploy **Fluent Bit** in each Argo CD namespace.
- Fluent Bit tails `argocd-server` logs, parses JSON, filters for Application CRUD, then ships events to a DB/Elastic/etc.

## What it captures:

- **Only actions that pass through** `argocd-server` (UI, CLI, Argo CD API).
- Shows **who did what** (username, token, method).
- **Does NOT see direct Kubernetes API writes** (e.g. kubectl apply app.yaml).

## Benefits

- Simple to deploy (no Kubernetes admission machinery).
- No impact on users (passive observation).
- Good for auditing & monitoring (build dashboards, alerts, history).

## Limitations

- **Audit-only**: can’t block unwanted actions.
- Misses changes made **outside Argo CD API** (kubectl direct CRDs).
- Delay: logs are collected after the action already happened.
- Enforcement requires **manual follow-up** (alert → human → rollback).

# 2. Admission Webhook Approach

## How it works:

- Deploy a **Kubernetes Validating/Mutating Admission Webhook**.
- The webhook intercepts all API server requests for Argo CD CRDs (Applications, AppProjects, etc.).
- You can **validate** or **reject** requests before they’re persisted.

## What it captures:

- All CRUD requests to Kubernetes API for targeted resources:

  - Applications (argoproj.io/v1alpha1)
  - AppProjects, ApplicationSets
  - Cluster/Repo Secrets, ConfigMaps

- Independent of whether the request comes from Argo CD UI, CLI, API, or kubectl.

## Benefits

- **Enforcement**: can block disallowed actions before they reach etcd.
- Uniform coverage (any client, any path).
- Flexible policies: enforce labels, repo allowlists, destination namespaces, sync policies.
- Good for **guardrails & compliance**.

## Limitations

- More complex to implement (TLS, caBundle, admission logic).
- On the critical path of API server → latency, risk if webhook crashes (use failurePolicy=Ignore in audit-only mode first).
- Needs careful scoping (namespaceSelector, rules) to avoid cluster-wide impact.
- Harder to integrate with existing log/alerting pipelines.

# Side-by-Side Summary

| Aspect              | Fluent Bit (Logs)                      | Admission Webhook                           |
| ------------------- | -------------------------------------- | ------------------------------------------- |
| **Scope**           | Only via `argocd-server` (UI/CLI/API)  | All CRUD via Kubernetes API (CRDs, secrets) |
| **Type**            | Audit (observe only)                   | Enforcement (block/allow)                   |
| **Covers kubectl?** | No                                     | Yes                                         |
| **Impact**          | None (passive)                         | On API path (adds latency, risk if broken)  |
| **Complexity**      | Low (log collector config)             | Medium/High (webhook infra, TLS, policies)  |
| **Best for**        | Visibility, monitoring, dashboards     | Compliance, governance, guardrails          |
| **Limitations**     | Misses direct CRD changes; can’t block | Needs maintenance; critical-path component  |

## What to choose

- If the goal is **audit / visibility / learning who did what** => start with **Fluent Bit**.
- If the goal is **compliance / preventing risky actions** => need Admission Webhook.

- Many orgs combine both:
  - Fluent Bit => SIEM/DB for full history & dashboards.
  - Admission Webhook => enforce guardrails on high-risk fields (e.g., disallow auto-prune in prod).
