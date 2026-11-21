# 7. Security, Safety, and Privacy

## 7.1 Security posture
FORKED can capture sensitive prompts, customer data, source code, API responses, credentials, and internal system state. The default posture must minimize capture and prevent replay from causing external changes.

## 7.2 Threat model
Assets:
- execution artifacts;
- prompts and model outputs;
- tool inputs/outputs;
- environment metadata;
- credentials and tokens;
- user/customer data;
- integrity manifests.

Threats:
- secret leakage into logs;
- malicious or malformed event payloads;
- archive path traversal during import;
- tampered manifests or artifacts;
- replay triggering duplicate writes;
- unsafe adapter behavior;
- dependency compromise;
- untrusted code execution in branches;
- cross-tenant data leakage in any future hosted product.

## 7.3 Required controls
1. Secret redaction before persistence.
2. Data minimization and configurable field allowlists.
3. Default-deny for external writes and unknown effects.
4. Replay uses recorded observations; it does not call external APIs by default.
5. Disposable sandbox for code execution.
6. Archive extraction must prevent path traversal and symlink escapes.
7. Verify hashes before parsing imported artifacts.
8. Limit artifact size and event count.
9. No credentials in test fixtures.
10. Clear warnings for incomplete capture.
11. Explicit user approval for any future effectful operation.
12. Audit logs for policy decisions.

## 7.4 Privacy
- Local-first by default.
- No telemetry by default in MVP.
- No upload of traces to a hosted service without explicit opt-in.
- Redaction configuration is visible and testable.
- Retention and deletion behavior documented.
- Sensitive payloads can be omitted and represented by hashes/references where feasible.
- Avoid storing full model reasoning or hidden chain-of-thought. Capture only the application-visible inputs, outputs, tool calls, and metadata necessary for the experiment.

## 7.5 Secure replay policy
Default matrix:

| Operation | Default |
|---|---|
| Read recorded result | Replay stored result |
| Pure local computation | Allow in sandbox if declared |
| Local file write | Disposable branch workspace only |
| External read | Use recorded response |
| External write | Deny |
| Unknown operation | Deny |
| Missing recorded response | Fail closed |

## 7.6 Security testing
- secret-redaction tests;
- archive traversal tests;
- malformed schema tests;
- tampered hash tests;
- replay external-write denial tests;
- unknown-effect denial tests;
- branch isolation tests;
- oversized payload tests;
- dependency and static analysis in CI.

## 7.7 Responsible disclosure
Publish a `SECURITY.md` with a private reporting channel before accepting production use. Do not promise a response SLA until maintainers can meet it.
