## 2026-02-04 - Isolate Logging Configuration
**Problem:** Multiple low-level modules (`MitigationExecutor`, `AlertingNotificationEngine`) called `logging.basicConfig()` in their `__init__` methods.
**Decision:** Removed `logging.basicConfig()` from library classes. It now resides only in the application entry point (`AntiDDOSMasterController`) or `if __name__ == "__main__":` blocks for standalone testing.
**Outcome:** Prevents libraries from hijacking the global logging configuration of the consuming application. Improves testability and modularity.
**Rule:** Library classes must never configure global environment settings (like `logging.basicConfig`). Dependencies must point inward.
