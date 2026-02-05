## 2024-10-26 - Insecure Default Bind in Security Tools
**Vulnerability:** The SOC Dashboard backend (`soc_dashboard_backend.py`) bound to `0.0.0.0` by default via `socketserver.TCPServer(("", port), ...)`. This exposed sensitive operational metrics (blocked IPs, traffic stats) to the entire network without any authentication mechanism.
**Learning:** Even within a security-focused codebase (`python_antiddos_soc_suite`), "developer convenience" patterns often persist. The use of empty string `""` for binding is a common idiom in tutorials but is insecure for production tools, especially those displaying sensitive data. It highlights that security tools themselves are not immune to basic configuration vulnerabilities.
**Prevention:** Enforce a "Secure by Default" policy for all network listeners. Class initializers should default to `127.0.0.1` or `localhost`. Binding to external interfaces (`0.0.0.0`) must be an explicit, conscious configuration choice by the user (e.g., via a CLI flag or config file), never the default.

## 2025-05-23 - Hardcoded Secrets in Distributed Scripts
**Vulnerability:** Found `auth_token` hardcoded in `hardening.yaml` and used as a default in multiple independent scripts (`orchestrator`, `spoofing_detector`, `game_detector`).
**Learning:** Independent CLI scripts often duplicate config loading logic, leading to scattered security defaults that are hard to update centrally.
**Prevention:** Centralize config loading in a shared module that enforces environment variable overrides for secrets. Use distinct variable names (e.g., `UAD_AUTH_TOKEN`) to avoid collisions.
