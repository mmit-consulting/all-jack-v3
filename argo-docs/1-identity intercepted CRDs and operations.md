# Identify intercepted CRDs & operations

Objectif: Map the API endpoints ==> the actual ArgoCD CRDs/resources they touch ==> the operations that should be validated

## Mapping Swagger endpoints ==> CRDs/operations

### Instance lifecycle

- `/instances/{trigram}-{code}` (POST, DELETE, PUT restart)
  - touches **Namespaces, ArgoCD Deployments/ConfigMaps/Secrets**
  - Operations: **provision, restart, decommission**

Intercept to ensure allowed teams, quotas, naming convention, cleanup.

### Cluster management

- `/clusters/add` POST, `/clusters/update/{cluster_alias}` PUT, `/clusters/{cluster_alias}` DELETE
  - touches **Secret** (cluster credentials) CRD in ArgoCD
  - Operations: **CREATE/UPDATE/DELETE cluster secrets**

Critical: must validate host allowlist, etc ...

### Tokens

- `/account/{account}/tokens` (POST/DELETE)
  - touches **ArgoCD Account tokens** (stored as secrets)

Enforce RBAC: who can mint/delete tokens, expiration, scope.

### Repository credentials

- `/resources/creds-template` (POST/PUT/DELETE)
  - touches **Secret** (repository credentials) in ArgoCD
  - Operations: **CREATE/UPDATE/DELETE repo secrets**

Must enforce only trusted GitHub orgs, forbid plaintext tokens, require SSH/TLS.

### Applications / Projects / AppSets

- `/resources/{resource}/format/file|url|names/{name}` (POST/PUT/DELETE)
  - touches ArgoCD CRDs: **Application, AppProject, ApplicationSet**
  - Operations: **CREATE/UPDATE/DELETE of apps & projects**

Validate repoURL, destination namespace, syncPolicy (prune/selfHeal), required labels, AppProject boundaries.

- `/applications/{app_name}/sync` POST
  - Touches Application sync operation

Could enforce sync-windows, forbid manual sync to prod without approval.

### Notifications

- `/notifications/credentials`, `/notifications/templates`
  - touches ArgoCD ConfigMaps/Secrets for notifications

Enforce only approved destinations (GitHub, Teams, Email), deny arbitrary webhooks.
