
import uvicorn
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting War Room Dashboard on http://localhost:8000")
    print("Press Ctrl+C to stop.")
    uvicorn.run("dashboard.backend.main:app", host="0.0.0.0", port=8000, reload=True)
