# GeoCadastral AI — Security & Threat Modeling Architecture

## 1. Security Overview
GeoCadastral AI is designed to meet government land department security criteria, strictly enforcing multi-tenant boundary isolation, input sanitization, and least-privilege access.

---

## 2. Threat Mitigations

### 2.1 Server-Side Request Forgery (SSRF) Protection
External GIS connections (WMS, WMTS, WFS) are validated through `SSRFGuard`:
* **Loopback blocking**: `localhost`, `127.0.0.1`, `::1` are rejected.
* **Private Network blocking**: All RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are blocked.
* **Cloud Metadata Defense**: Link-local address `169.254.169.254` (AWS/GCP/Azure instance metadata) is blocked.
* **Internal domain defense**: Domains ending in `.local`, `.internal`, or `.localhost` are blocked.

### 2.2 Path Traversal & File Upload Security
* Storage paths are normalized and resolved via `LocalStorageProvider._sanitize_path`.
* Any relative path attempting to escape the storage root (e.g. `../../windows/system32`) triggers an immediate `StorageSecurityException`.
* Allowed file extensions for uploads are strictly enforced (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.zip`).

### 2.3 API Key Management & Cryptography
* API keys are formatted with clear prefixes: `gc_live_{40_hex_chars}`.
* Raw keys are displayed only once upon creation.
* The backend stores only the SHA-256 hash (`hashed_secret`). Compromise of the database does not reveal usable API secrets.
* Scopes are validated on every endpoint (`projects:read`, `analysis:run`, etc.).

### 2.4 Multi-Tenant Data Isolation
* All database queries filter on `org_id`.
* The `RoleBasedAccessControl.enforce_tenant_isolation` method validates tenant ownership before accessing any scene, parcel, or report entity.
* Cross-tenant access attempts immediately raise `PermissionError`.

### 2.5 Legal & Decision-Support Compliance
* In compliance with government survey regulations, the platform never emits legal declarations (`illegal`, `legal ownership`, `encroachment`, `legal easement`, `landlocked`).
* Objective survey terminology is enforced across all APIs, UI modals, and PDF deliverables:
  * `Potential discrepancy` (instead of encroachment)
  * `Physical access concern` (instead of landlocked)
  * `AI-proposed boundary` (instead of legal boundary)
  * `Requires survey verification` (statutory requirement)
