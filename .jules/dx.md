## 2024-05-22 - Ambiguous Project Entry Points
**Problem:** The project is highly modular with many directories ("Suites"), but lacks a clear map or "Quick Start" guide. Users are forced to explore directory structures to find the correct script to run, leading to confusion about which script is the main entry point (e.g., `Menu-2.sh` vs `new_anti_ddos.sh`).
**Fix:** Added a "Guia Rápido" (Quick Start) table to the main `README.md` mapping high-level user goals to specific, copy-pasteable commands.
**Lesson:** Modular architectures scale code but confuse users. Always provide a "Map" or "Happy Path" in the root documentation to bridge the gap between intent ("I want to stop DDoS") and action ("Run this script").

## 2024-05-22 - Missing Dependencies File
**Problem:** `README.md` instructed users to install dependencies from `requirements.txt`, but the file did not exist, causing immediate failure during setup.
**Fix:** Created `under_attack_ddos/requirements.txt` with identified dependencies (`pyyaml`, `scapy`, `textual`).
**Lesson:** Documentation must be validated against the actual codebase state; broken setup instructions are the highest friction point for new users.
