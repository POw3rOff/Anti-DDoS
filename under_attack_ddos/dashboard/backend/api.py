
import json
import os
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dashboard.backend.config_manager import ConfigManager

router = APIRouter()

STATE_FILE = os.path.join(os.path.dirname(__file__), "../../runtime/global_state.json")
LOCK_FILE = os.path.join(os.path.dirname(__file__), "../../runtime/OVERRIDE.lock")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/thresholds.yaml")
CAPTURES_DIR = os.path.join(os.path.dirname(__file__), "../../data/captures")

config_manager = ConfigManager(CONFIG_PATH)

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
