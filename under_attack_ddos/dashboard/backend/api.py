
import json
import os
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi import Request
from pydantic import BaseModel
import sys
# Ensure root path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from layer7.js_challenge import JSChallenge
from dashboard.backend.config_manager import ConfigManager

router = APIRouter()

STATE_FILE = os.path.join(os.path.dirname(__file__), "../../runtime/global_state.json")
LOCK_FILE = os.path.join(os.path.dirname(__file__), "../../runtime/OVERRIDE.lock")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/thresholds.yaml")
CAPTURES_DIR = os.path.join(os.path.dirname(__file__), "../../data/captures")

config_manager = ConfigManager(CONFIG_PATH)
js_challenge = JSChallenge(secret_key="production_secret_key") # Logic instance

class PanicRequest(BaseModel):
    confirm: bool

class ConfigUpdate(BaseModel):
    config: dict

@router.get("/config/thresholds")
async def get_thresholds():
    """Returns the current threshold configuration."""
    return config_manager.get_config()

@router.post("/config/thresholds")
async def update_thresholds(update: ConfigUpdate):
    """Updates the threshold configuration."""
    try:
        config_manager.update_config(update.config)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Returns the current system state."""
    if not os.path.exists(STATE_FILE):
        return {"mode": "UNKNOWN", "grs_score": 0, "status": "offline"}
    
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
        data["status"] = "online"
        return data
    except Exception as e:
        return {"mode": "ERROR", "error": str(e)}

@router.post("/panic")
async def trigger_panic(req: PanicRequest):
    """Activates panic mode."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    try:
        with open(LOCK_FILE, "w") as f:
            f.write("ESCALATED")
        return {"message": "Panic signal sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forensics/files")
async def list_captures():
    """Lists available PCAP captures."""
    if not os.path.exists(CAPTURES_DIR):
        return []
    
    files = []
    try:
        for f in os.listdir(CAPTURES_DIR):
            if f.endswith(".pcap"):
                path = os.path.join(CAPTURES_DIR, f)
                size = os.path.getsize(path) / 1024 / 1024 # MB
                files.append({
                    "filename": f,
                    "size_mb": round(size, 2),
                    "created": time.ctime(os.path.getctime(path))
                })
        return sorted(files, key=lambda x: x["created"], reverse=True)
    except Exception as e:
        return []

@router.get("/forensics/download/{filename}")
async def download_capture(filename: str):
    """Downloads a specific PCAP file."""
    if ".." in filename or "/" in filename: # Basic traversal check
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(CAPTURES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, media_type='application/vnd.tcpdump.pcap', filename=filename)

# --- Phase 26: L7 Challenge Endpoints ---

@router.get("/challenge")
async def get_challenge(request: Request):
    """Serves the JS Challenge HTML page."""
    client_ip = request.client.host
    html_content = js_challenge.generate_challenge(client_ip)
    return HTMLResponse(content=html_content, status_code=200)

class ChallengeResponse(BaseModel):
    token: str

@router.post("/challenge/verify")
async def verify_challenge(request: Request, response: ChallengeResponse):
    """Validates the challenge token."""
    client_ip = request.client.host
    if js_challenge.validate_token(client_ip, response.token):
        # In a real setup, we would set a 'Clearance Cookie' or update Nginx Allow List here.
        # For now, we return success so the JS on the page can reload/proceed.
        return JSONResponse(content={"status": "verified"}, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Challenge Failed")
