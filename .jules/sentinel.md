## 2024-10-26 - Insecure Default Bind in Security Tools
**Vulnerability:** The SOC Dashboard backend (`soc_dashboard_backend.py`) bound to `0.0.0.0` by default via `socketserver.TCPServer(("", port), ...)`. This exposed sensitive operational metrics (blocked IPs, traffic stats) to the entire network without any authentication mechanism.
**Learning:** Even within a security-focused codebase (`python_antiddos_soc_suite`), "developer convenience" patterns often persist. The use of empty string `""` for binding is a common idiom in tutorials but is insecure for production tools, especially those displaying sensitive data. It highlights that security tools themselves are not immune to basic configuration vulnerabilities.
**Prevention:** Enforce a "Secure by Default" policy for all network listeners. Class initializers should default to `127.0.0.1` or `localhost`. Binding to external interfaces (`0.0.0.0`) must be an explicit, conscious configuration choice by the user (e.g., via a CLI flag or config file), never the default.

## 2024-05-22 - Config Injection via File Generation
**Vulnerability:** Unvalidated user input (IP address) was written directly to an Nginx configuration file, allowing for arbitrary directive injection.
**Learning:** File generation from user input is a high-risk sink. Even seemingly safe data types like "IP Address" can be vectors for injection if not strictly typed.
**Prevention:** Use strict type validation (e.g., `ipaddress` module) for all inputs before writing them to configuration files or system commands. Do not rely on string formatting alone.
