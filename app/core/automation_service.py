import os
import sys
import subprocess
import webbrowser
import platform
import ctypes
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import psutil

from app.config import config
from app.database import get_db, DatabaseService

logger = logging.getLogger("AURA.Automation")


class AutomationService:
    """Secure, controlled Windows desktop automation engine."""

    ALLOWED_APPLICATIONS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "taskmgr": "taskmgr.exe",
    }

    ACTIONS = {
        "open_application": {
            "description": "Launch an approved Windows utility (notepad, calculator, explorer, paint, taskmgr)",
            "requires_confirmation": False,
        },
        "open_website": {
            "description": "Open a validated web URL (http/https) in the default browser",
            "requires_confirmation": False,
        },
        "create_note": {
            "description": "Save a structured text note inside AURA secure notes directory",
            "requires_confirmation": True,
        },
        "system_info": {
            "description": "Query live CPU, memory, storage, and platform telemetry",
            "requires_confirmation": False,
        },
        "find_files": {
            "description": "Search for files by pattern inside user documents directory",
            "requires_confirmation": False,
        },
        "lock_workstation": {
            "description": "Instantly lock the Windows workstation",
            "requires_confirmation": True,
        },
    }

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or get_db()
        self.is_emergency_stopped = False

    @property
    def is_enabled(self) -> bool:
        val = self.db.get_setting("automation_enabled", "true" if config.automation_enabled else "false")
        return val.lower() in ("true", "1", "yes")

    def set_enabled(self, enabled: bool):
        self.db.set_setting("automation_enabled", "true" if enabled else "false")

    def trigger_emergency_stop(self):
        """Immediately prevent any automation actions from executing."""
        self.is_emergency_stopped = True
        logger.warning("EMERGENCY STOP TRIGGERED: Desktop automation engine locked down.")
        self.db.log_audit_event(
            action_name="EMERGENCY_STOP",
            parameters={},
            status="executed",
            result="Emergency stop triggered by user. Engine locked."
        )

    def reset_emergency_stop(self):
        self.is_emergency_stopped = False
        logger.info("Emergency stop cleared by user.")

    def list_permitted_actions(self) -> Dict[str, Any]:
        return self.ACTIONS

    def execute_action(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        user_confirmed: bool = False
    ) -> Dict[str, Any]:
        """Validate and execute a strictly allowlisted automation action."""
        # 1. Check emergency stop
        if self.is_emergency_stopped:
            msg = "Action rejected: Emergency Stop is active. Reset the emergency stop to proceed."
            self.db.log_audit_event(action_name, parameters, "denied", error_message=msg)
            return {"success": False, "error": msg}

        # 2. Check global automation enable flag
        if not self.is_enabled:
            msg = "Action rejected: Desktop Automation is currently disabled in Settings."
            self.db.log_audit_event(action_name, parameters, "denied", error_message=msg)
            return {"success": False, "error": msg}

        # 3. Check action in allowlist
        if action_name not in self.ACTIONS:
            msg = f"Action rejected: '{action_name}' is not in the approved automation allowlist."
            self.db.log_audit_event(action_name, parameters, "denied", error_message=msg)
            return {"success": False, "error": msg}

        action_def = self.ACTIONS[action_name]

        # 4. Confirmation requirement check
        if action_def["requires_confirmation"] and not user_confirmed and config.automation_require_confirmation:
            return {
                "success": False,
                "needs_confirmation": True,
                "action_name": action_name,
                "parameters": parameters,
                "message": f"Action '{action_name}' requires explicit user confirmation before executing."
            }

        # 5. Dispatch execution to strict safe implementations
        try:
            if action_name == "open_application":
                result = self._exec_open_application(parameters)
            elif action_name == "open_website":
                result = self._exec_open_website(parameters)
            elif action_name == "create_note":
                result = self._exec_create_note(parameters)
            elif action_name == "system_info":
                result = self._exec_system_info(parameters)
            elif action_name == "find_files":
                result = self._exec_find_files(parameters)
            elif action_name == "lock_workstation":
                result = self._exec_lock_workstation(parameters)
            else:
                raise ValueError(f"Unimplemented action handler: {action_name}")

            self.db.log_audit_event(
                action_name=action_name,
                parameters=parameters,
                status="executed",
                result=str(result)
            )
            return {"success": True, "result": result}

        except Exception as e:
            err_msg = str(e)
            logger.error("Automation error for action %s: %s", action_name, err_msg)
            self.db.log_audit_event(
                action_name=action_name,
                parameters=parameters,
                status="failed",
                error_message=err_msg
            )
            return {"success": False, "error": err_msg}

    # -------------------------------------------------------------------------
    # Safe Action Implementations
    # -------------------------------------------------------------------------
    def _exec_open_application(self, params: Dict[str, Any]) -> str:
        app_key = str(params.get("app_name", "")).strip().lower()
        if app_key not in self.ALLOWED_APPLICATIONS:
            allowed_list = ", ".join(self.ALLOWED_APPLICATIONS.keys())
            raise ValueError(f"Application '{app_key}' not permitted. Allowed: {allowed_list}")

        exe_name = self.ALLOWED_APPLICATIONS[app_key]
        if sys.platform == "win32":
            subprocess.Popen([exe_name], shell=False)
            return f"Launched {exe_name} successfully."
        else:
            return f"Simulated launching {exe_name} (Windows only)."

    def _exec_open_website(self, params: Dict[str, Any]) -> str:
        url = str(params.get("url", "")).strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")

        webbrowser.open(url)
        return f"Opened website: {url}"

    def _exec_create_note(self, params: Dict[str, Any]) -> str:
        title = str(params.get("title", "AURA_Note")).strip()
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_title:
            safe_title = "AURA_Note"

        content = str(params.get("content", "")).strip()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        note_filename = f"{safe_title}_{timestamp_str}.txt"
        note_path = config.notes_dir / note_filename

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}\n")

        return f"Note created: {note_filename} in notes directory."

    def _exec_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if sys.platform == "win32" else "/")
        
        info = {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "processor": platform.processor() or "x86_64",
            "cpu_usage_percent": cpu_usage,
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_percent": disk.percent,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
        return info

    def _exec_find_files(self, params: Dict[str, Any]) -> List[str]:
        pattern = str(params.get("pattern", "*")).strip()
        search_root = Path.home() / "Documents"
        if not search_root.exists():
            search_root = Path.home()

        matches = []
        try:
            for p in search_root.rglob(pattern):
                if p.is_file():
                    matches.append(str(p))
                    if len(matches) >= 20:
                        break
        except Exception as e:
            logger.warning("Error searching files: %s", e)
        return matches

    def _exec_lock_workstation(self, params: Dict[str, Any]) -> str:
        if sys.platform == "win32":
            ctypes.windll.user32.LockWorkStation()
            return "Windows workstation locked."
        return "Workstation lock simulated (Windows only)."


automation_service = AutomationService()
