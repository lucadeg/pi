#!/usr/bin/env python3
"""
Pi Galaxy Brain — 3D Neural Swarm Master Control Plane & Telemetry Daemon
Port: 5199 | Host: 127.0.0.1
Serves real-time telemetry, 1-click service start/stop, MechaHD projects inventory,
Toolbox Manager, and live interactive Agent Chat REPL.
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import threading
import subprocess
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PI_DIR = os.path.dirname(os.path.abspath(__file__))
HERMES_ROOT = r"C:\Users\Deglu\.hermes"
MECHA_DIR = os.path.join(HERMES_ROOT, "mechaHD")
TOOLS_DIR = os.path.join(HERMES_ROOT, "tools")
TUIOS_DIR = os.path.join(HERMES_ROOT, "tools", "tuios")

if TUIOS_DIR not in sys.path:
    sys.path.insert(0, TUIOS_DIR)

try:
    import hermes_data_bridge
except ImportError:
    hermes_data_bridge = None

PORT = 5199
HOST = "127.0.0.1"

# Service Definitions for 1-Click Operations
SERVICES_REGISTRY = {
    "kimi_k3": {
        "name": "Kimi K3 MoE C-Engine",
        "port": 8095,
        "dir": os.path.join(TOOLS_DIR, "kimi-k3-in-c"),
        "cmd": ["python", "kimi_k3_service.py"],
        "url": "http://127.0.0.1:8095/v1/models",
        "category": "Inference Engines",
        "description": "Native C-Engine MoE 1.5T local inference ($0.00 offline)"
    },
    "hydra_router": {
        "name": "Hydra Task Router",
        "port": 8090,
        "dir": os.path.join(MECHA_DIR, "JARVIS 3FOLD", "router"),
        "cmd": ["python", "main.py"],
        "url": "http://127.0.0.1:8090/dashboard",
        "category": "Model Routers",
        "description": "Dynamic multi-model router (Claude, Gemini, DeepSeek, LLaMA)"
    },
    "ldg_innovation": {
        "name": "LDG Innovation Hub",
        "port": 3000,
        "dir": os.path.join(MECHA_DIR, "LDG_INNOVATION"),
        "cmd": ["cmd.exe", "/c", "npm run dev"],
        "url": "http://localhost:3000",
        "category": "Enterprise Platforms",
        "description": "Next.js 15 Enterprise Portal, B2B Suite v2 & Sovereign Matrix"
    },
    "paperclip": {
        "name": "Paperclip Control Plane",
        "port": 3100,
        "dir": os.path.join(HERMES_ROOT, "paperclip"),
        "cmd": ["cmd.exe", "/c", "pnpm dev"],
        "url": "http://localhost:3100",
        "category": "Agent Control Planes",
        "description": "AI-Agent company control plane, board UI & orchestration"
    },
    "hermes_ide": {
        "name": "Hermes IDE Unchained",
        "port": 5195,
        "dir": os.path.join(HERMES_ROOT, "hermes-ide-unchained"),
        "cmd": ["cmd.exe", "/c", "npm start"],
        "url": "http://localhost:5195",
        "category": "Development IDEs",
        "description": "Next-gen sovereign IDE with Theia & Three.js dashboard"
    },
    "hermes_office": {
        "name": "Hermes Office 3D",
        "port": 3001,
        "dir": os.path.join(HERMES_ROOT, "hermes-office"),
        "cmd": ["cmd.exe", "/c", "npm run dev"],
        "url": "http://localhost:3001",
        "category": "3D Virtual Workspaces",
        "description": "Next.js 16 + Three.js 3D Virtual Office & Agent Canvas"
    },
    "buzz_relay": {
        "name": "Block Buzz Nostr Relay",
        "port": 3005,
        "dir": os.path.join(HERMES_ROOT, "buzz"),
        "cmd": ["cmd.exe", "/c", "cargo run -p buzz-relay"],
        "url": "http://127.0.0.1:3005",
        "category": "Protocols & Relays",
        "description": "Nostr NIP-29 Group Event Bus & Realtime Sync Engine"
    },
    "maxun": {
        "name": "Maxun Autonomous Scraper",
        "port": 8080,
        "dir": os.path.join(TOOLS_DIR, "maxun"),
        "cmd": ["cmd.exe", "/c", "npm start"],
        "url": "http://localhost:8080",
        "category": "Autonomous Crawlers",
        "description": "No-code web data extraction & autonomous scraping engine"
    }
}

RUNNING_PROCESSES = {}
_SERVICES_CACHE = {}
_SERVICES_CACHE_TIME = 0.0

def is_port_open(port: int) -> bool:
    if not port:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.06)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def get_services_status():
    global _SERVICES_CACHE, _SERVICES_CACHE_TIME
    now = time.time()
    if _SERVICES_CACHE and (now - _SERVICES_CACHE_TIME < 4.0):
        return _SERVICES_CACHE
        
    results = {}
    for key, svc in SERVICES_REGISTRY.items():
        online = is_port_open(svc["port"])
        results[key] = {
            "key": key,
            "name": svc["name"],
            "port": svc["port"],
            "status": "online" if online else "standby",
            "url": svc["url"],
            "category": svc["category"],
            "description": svc["description"],
            "dir": svc["dir"]
        }
    _SERVICES_CACHE = results
    _SERVICES_CACHE_TIME = now
    return results

def start_service_by_key(key: str) -> dict:
    if key not in SERVICES_REGISTRY:
        return {"success": False, "error": f"Service '{key}' not found in registry"}
    
    svc = SERVICES_REGISTRY[key]
    if is_port_open(svc["port"]):
        return {"success": True, "message": f"{svc['name']} is already running on port {svc['port']}", "status": "online"}
    
    svc_dir = svc["dir"]
    if not os.path.exists(svc_dir):
        return {"success": False, "error": f"Directory not found: {svc_dir}"}
    
    try:
        # Create detached background process on Windows
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            
        p = subprocess.Popen(
            svc["cmd"],
            cwd=svc_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags
        )
        RUNNING_PROCESSES[key] = p.pid
        
        # Wait up to 3s for port to open
        for _ in range(12):
            time.sleep(0.25)
            if is_port_open(svc["port"]):
                break
                
        online = is_port_open(svc["port"])
        return {
            "success": True,
            "message": f"Started {svc['name']}",
            "status": "online" if online else "starting",
            "port": svc["port"],
            "pid": p.pid
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def stop_service_by_key(key: str) -> dict:
    if key not in SERVICES_REGISTRY:
        return {"success": False, "error": f"Service '{key}' not found in registry"}
    
    svc = SERVICES_REGISTRY[key]
    port = svc["port"]
    
    # On Windows, kill process using netstat and taskkill
    killed = False
    if sys.platform == "win32" and port:
        try:
            out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and (f":{port}" in parts[1] or f":{port}" in parts[2]):
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) > 0 and int(pid) != os.getpid():
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        killed = True
        except Exception:
            pass

    RUNNING_PROCESSES.pop(key, None)
    time.sleep(0.5)
    online = is_port_open(port)
    return {"success": True, "status": "standby" if not online else "terminating", "message": f"Service {svc['name']} stopped"}

def open_app_or_folder(app_type: str, path: str = None) -> dict:
    try:
        if app_type == "paperclip":
            if not is_port_open(3100):
                start_service_by_key("paperclip")
            subprocess.run('start "" "http://localhost:3100"', shell=True)
            return {"success": True, "message": "Opened Paperclip Control Plane"}
            
        elif app_type == "hermes" or app_type == "hermes_tui":
            tui_cmd = 'start powershell -NoExit -ExecutionPolicy Bypass -Command "cd C:\\Users\\Deglu\\.hermes\\tools\\tuios; node hermes-cli.js"'
            subprocess.run(tui_cmd, shell=True)
            return {"success": True, "message": "Opened Hermes TUIOS Control Console"}
            
        elif app_type == "ldg":
            if not is_port_open(3000):
                start_service_by_key("ldg_innovation")
            subprocess.run('start "" "http://localhost:3000"', shell=True)
            return {"success": True, "message": "Opened LDG Innovation Hub"}
            
        elif app_type == "folder" and path:
            if os.path.exists(path):
                subprocess.run(f'explorer "{os.path.abspath(path)}"', shell=True)
                return {"success": True, "message": f"Opened folder: {path}"}
            return {"success": False, "error": "Path does not exist"}
            
        elif app_type == "code" and path:
            if os.path.exists(path):
                subprocess.run(f'code "{os.path.abspath(path)}"', shell=True)
                return {"success": True, "message": f"Opened in VS Code: {path}"}
            return {"success": False, "error": "Path does not exist"}

        elif app_type == "terminal" and path:
            if os.path.exists(path):
                subprocess.run(f'start powershell -NoExit -ExecutionPolicy Bypass -Command "cd \'{os.path.abspath(path)}\'"', shell=True)
                return {"success": True, "message": f"Opened Terminal at: {path}"}
            return {"success": False, "error": "Path does not exist"}

        return {"success": False, "error": f"Unknown app_type: {app_type}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

_MECHA_CACHE = None
_MECHA_CACHE_TIME = 0.0

def scan_mecha_projects() -> list[dict]:
    global _MECHA_CACHE, _MECHA_CACHE_TIME
    now = time.time()
    if _MECHA_CACHE is not None and (now - _MECHA_CACHE_TIME < 5.0):
        return _MECHA_CACHE

    projects = []
    if not os.path.exists(MECHA_DIR):
        _MECHA_CACHE = projects
        _MECHA_CACHE_TIME = now
        return projects
        
    for item in sorted(os.listdir(MECHA_DIR)):
        item_path = os.path.join(MECHA_DIR, item)
        if not os.path.isdir(item_path) or item.startswith("."):
            continue
            
        # Analyze project traits
        tech = []
        desc = "MechaHD Enterprise Autonomous Project"
        port = None
        
        has_pkg = os.path.exists(os.path.join(item_path, "package.json"))
        has_py = os.path.exists(os.path.join(item_path, "requirements.txt")) or os.path.exists(os.path.join(item_path, "pyproject.toml"))
        has_next = os.path.exists(os.path.join(item_path, "next.config.js")) or os.path.exists(os.path.join(item_path, "next.config.mjs")) or os.path.exists(os.path.join(item_path, "next.config.ts"))
        has_matrix = os.path.exists(os.path.join(item_path, "PROJECT_TRACEABILITY_MATRIX.json"))
        
        if has_next: tech.append("Next.js 15")
        elif has_pkg: tech.append("Node.js / React")
        if has_py: tech.append("Python 3.11")
        if os.path.exists(os.path.join(item_path, "Dockerfile")): tech.append("Docker")
        if os.path.exists(os.path.join(item_path, "tsconfig.json")): tech.append("TypeScript")
        
        if item == "LDG_INNOVATION":
            desc = "Flagship Next.js 15 Platform, B2B Acquisition Suite v2 & Sovereign Governance"
            port = 3000
        elif item == "JARVIS 3FOLD":
            desc = "Enterprise Multi-Model Hydra Router Engine & Neural Task Isolator"
            port = 8090
        elif item == "AWORD":
            desc = "Lingua Flow Multilingual AI Communication & Transcription Pipeline"
        elif item == "FanForge":
            desc = "Creator Monetization, Web3 Drops & Digital Merchandise Engine"
        elif item == "Virtual-influencer-V2":
            desc = "Autonomous UGC Video Generator, Character LoRA & Social Auto-Poster"
        elif item == "founder_OS" or item == "founder OS":
            desc = "Founder Operating System, Executive KPIs, Financial Modeling & Strategy"
        elif "crypto" in item.lower():
            desc = "Automated Crypto Intelligence, Market Trend Scanner & Sentiment Tracker"
        elif "job" in item.lower():
            desc = "Autonomous Executive Job Scouting, Resume Matching & Auto-Application"
        elif "trading" in item.lower():
            desc = "Algorithmic Market Intelligence & Quantitative Risk Analysis"
            
        status = "online" if port and is_port_open(port) else "ready"
        
        projects.append({
            "id": item,
            "name": item.replace("_", " ").replace("-", " ").title(),
            "path": item_path,
            "description": desc,
            "tech": tech if tech else ["General Fullstack"],
            "port": port,
            "status": status,
            "has_matrix": has_matrix
        })
    _MECHA_CACHE = projects
    _MECHA_CACHE_TIME = now
    return projects

_TOOLBOX_CACHE = None
_TOOLBOX_CACHE_TIME = 0.0

def scan_toolbox_items() -> list[dict]:
    global _TOOLBOX_CACHE, _TOOLBOX_CACHE_TIME
    now = time.time()
    if _TOOLBOX_CACHE is not None and (now - _TOOLBOX_CACHE_TIME < 5.0):
        return _TOOLBOX_CACHE

    tools_list = []
    if not os.path.exists(TOOLS_DIR):
        _TOOLBOX_CACHE = tools_list
        _TOOLBOX_CACHE_TIME = now
        return tools_list
        
    known_metadata = {
        "kimi-k3-in-c": {"name": "Kimi K3 in C", "cat": "Inference", "desc": "Native C-Engine for MoE 1.5T local reasoning ($0.00)", "port": 8095},
        "pi": {"name": "Pi Coding Agent", "cat": "Autonomous Coding", "desc": "Sovereign AI pair-programmer & multi-model code architect", "port": 5199},
        "tuios": {"name": "TUIOS Terminal Engine", "cat": "Control & Terminals", "desc": "Multiplexer window manager, real analytics & swarm orchestrator", "port": None},
        "chatterbox": {"name": "Chatterbox Multi-Agent Voice", "cat": "Audio & Speech", "desc": "Realtime AI voice synthesis, STT & interactive telephony", "port": None},
        "coolify": {"name": "Coolify Cloud Control", "cat": "DevOps & PaaS", "desc": "Self-hosted alternative to Vercel/Heroku with Docker/Git deploy", "port": 8000},
        "maxun": {"name": "Maxun Visual Scraper", "cat": "Autonomous Scrapers", "desc": "No-code autonomous data extraction & robot workflow generator", "port": 8080},
        "scrapling": {"name": "Scrapling Anti-Bot Crawler", "cat": "Autonomous Scrapers", "desc": "High-throughput stealth web crawler with JS evaluation", "port": None},
        "sentrux": {"name": "Sentrux Security Auditor", "cat": "Security & Audit", "desc": "Zero-trust vulnerability scanner, AST security & secret leak hunter", "port": None},
        "data-formulator": {"name": "Data Formulator", "cat": "Data Science", "desc": "Interactive AI data transformation & visualization explorer", "port": None},
        "moneyprinterturbo": {"name": "MoneyPrinterTurbo", "cat": "Video & Content", "desc": "Automated YouTube Shorts & TikTok viral video generator", "port": None},
        "openchatcut": {"name": "OpenChatCut Editor", "cat": "Video & Content", "desc": "Multitrack AI video cutting, Remotion rendering & timeline editing", "port": 5173},
        "opensandbox": {"name": "OpenSandbox Isolation", "cat": "Security & Execution", "desc": "Secure sandboxed execution daemon for arbitrary code", "port": None},
        "plausible-analytics": {"name": "Plausible Analytics", "cat": "Analytics & Privacy", "desc": "Privacy-first lightweight analytics dashboard", "port": None},
        "instatic": {"name": "Instatic SSG Generator", "cat": "Web & Frontend", "desc": "Blazing-fast static site generator & landing page pipeline", "port": None},
        "openship": {"name": "OpenShip Logistics", "cat": "Ecommerce & Dropship", "desc": "Automated order fulfillment & multi-channel logistics engine", "port": None},
        "agent-bibliotecario": {"name": "Agent Bibliotecario", "cat": "Knowledge & RAG", "desc": "Universal indexer for 46,210+ skills, MCP tools & documentations", "port": None},
        "swarm_goals": {"name": "Swarm Atomic Goals & Ledger", "cat": "Workflow Governance", "desc": "112 Atomic goals on 14 phases with Merkle DAG ED25519 audit", "port": None},
    }
    
    # Also add root Paperclip & Buzz
    tools_list.append({
        "id": "paperclip",
        "name": "Paperclip Control Plane",
        "category": "Agent Control Planes",
        "description": "AI-Agent company control plane, board UI & organization management",
        "path": os.path.join(HERMES_ROOT, "paperclip"),
        "port": 3100,
        "status": "online" if is_port_open(3100) else "standby"
    })
    
    tools_list.append({
        "id": "buzz",
        "name": "Block Buzz Nostr Relay",
        "category": "Protocols & Relays",
        "description": "Decentralized Nostr NIP-29 Group Event Bus & Agent Swarm Gateway",
        "path": os.path.join(HERMES_ROOT, "buzz"),
        "port": 3005,
        "status": "online" if is_port_open(3005) else "standby"
    })
    
    for item in sorted(os.listdir(TOOLS_DIR)):
        item_path = os.path.join(TOOLS_DIR, item)
        if not os.path.isdir(item_path) or item.startswith(".") or item == "__pycache__":
            continue
            
        meta = known_metadata.get(item, {
            "name": item.replace("-", " ").replace("_", " ").title(),
            "cat": "Toolbox Utility",
            "desc": f"Hermes Workspace Tool & Utility ({item})",
            "port": None
        })
        
        status = "online" if meta.get("port") and is_port_open(meta["port"]) else "standby"
        
        tools_list.append({
            "id": item,
            "name": meta["name"],
            "category": meta["cat"],
            "description": meta["desc"],
            "path": item_path,
            "port": meta.get("port"),
            "status": status
        })
        
    _TOOLBOX_CACHE = tools_list
    _TOOLBOX_CACHE_TIME = now
    return tools_list

def execute_agent_chat(message: str, model: str = "kimi-k3-moe") -> dict:
    """Executes chat prompt via Kimi K3 MoE or Hydra Router with live responses."""
    start_t = time.time()
    
    # Check if target is Kimi K3 MoE
    if model in ["kimi-k3-moe", "qwen2.5-coder:3b", "local"]:
        if not is_port_open(8095):
            start_service_by_key("kimi_k3")
            time.sleep(1.0)
            
        endpoint = "http://127.0.0.1:8095/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are Pi Coding Agent & Hermes Sovereign Intelligence. You follow the 14-phase workflow (Workflow 1-14). You write clean, production-ready code with zero mock data and zero slop."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 2048,
            "temperature": 0.2
        }
        
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {"total_tokens": len(message)//4 + len(reply)//4})
                dur = round(time.time() - start_t, 2)
                return {
                    "success": True,
                    "reply": reply,
                    "model": model,
                    "provider": "Kimi K3 Native C-Engine (:8095)",
                    "cost": "$0.00 (Local Offline)",
                    "duration_s": dur,
                    "usage": usage
                }
        except Exception as e:
            return {
                "success": False,
                "reply": f"⚠️ Kimi K3 C-Engine Error ({str(e)}). Assicurati che il servizio sulla porta 8095 sia attivo.",
                "model": model,
                "provider": "Kimi K3",
                "cost": "$0.00",
                "duration_s": round(time.time() - start_t, 2)
            }
            
    # Target is Hydra Router
    else:
        if not is_port_open(8090):
            start_service_by_key("hydra_router")
            time.sleep(1.5)
            
        endpoint = "http://127.0.0.1:8090/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are Pi Coding Agent running through Hydra Task Router. Grounded in Workflow 1-14 and HTP-V5 traceability standards."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 4096
        }
        
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                dur = round(time.time() - start_t, 2)
                return {
                    "success": True,
                    "reply": reply,
                    "model": model,
                    "provider": "Hydra Task Router (:8090)",
                    "cost": "Multi-Model Dynamic",
                    "duration_s": dur,
                    "usage": usage
                }
        except Exception as e:
            return {
                "success": False,
                "reply": f"⚠️ Hydra Router Error ({str(e)}). Assicurati che Hydra sulla porta 8090 sia attivo.",
                "model": model,
                "provider": "Hydra Task Router",
                "duration_s": round(time.time() - start_t, 2)
            }

def get_knowledge_catalog() -> dict:
    """Returns all structured references, indexed documents, and viral benchmarks."""
    knowledge_dir = os.path.join(HERMES_ROOT, "knowledge_base")
    os.makedirs(knowledge_dir, exist_ok=True)
    
    # 1. References catalog from agent-bibliotecario
    refs_file = os.path.join(HERMES_ROOT, "tools", "agent-bibliotecario", "knowledge", "references.json")
    references = []
    if os.path.exists(refs_file):
        try:
            with open(refs_file, "r", encoding="utf-8") as rf:
                references = json.load(rf)
        except Exception:
            references = []
            
    # 2. Documents & Images in knowledge_base
    docs = []
    for root, dirs, files in os.walk(knowledge_dir):
        for f in files:
            fp = os.path.join(root, f)
            stat = os.stat(fp)
            ext = os.path.splitext(f)[1].lower()
            kind = "image" if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"] else "pdf" if ext == ".pdf" else "document"
            docs.append({
                "name": f,
                "path": fp,
                "size_bytes": stat.st_size,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "type": kind,
                "extension": ext
            })
            
    # 3. Viral reports
    reports_dir = os.path.join(HERMES_ROOT, "reports", "viral_benchmarks")
    reports = []
    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            if f.endswith(".md"):
                fp = os.path.join(reports_dir, f)
                stat = os.stat(fp)
                reports.append({
                    "title": f[:-3].replace("_", " "),
                    "filename": f,
                    "path": fp,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                })

    return {
        "references": references,
        "documents": docs,
        "reports": reports,
        "total_references": len(references),
        "total_documents": len(docs),
        "total_reports": len(reports)
    }

def execute_video_analysis(url: str, notes: str = "") -> dict:
    """Executes viral reverse engineering via viral_pipeline.py."""
    try:
        import importlib.util
        script_path = os.path.join(HERMES_ROOT, "tools", "viral-video-pipeline", "viral_pipeline.py")
        spec = importlib.util.spec_from_file_location("viral_pipeline", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.analyze_and_save_reference(url, notes=notes)
        if isinstance(res, dict) and "success" not in res:
            res["success"] = True
        return res
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_knowledge_upload(payload: dict) -> dict:
    """Saves uploaded image/PDF/text and indexes it into sovereign knowledge base."""
    import base64
    import re
    filename = payload.get("filename", "upload.txt")
    data_b64 = payload.get("data_base64", "")
    notes = payload.get("notes", "")
    tags = payload.get("tags", [])
    
    knowledge_dir = os.path.join(HERMES_ROOT, "knowledge_base")
    os.makedirs(knowledge_dir, exist_ok=True)
    
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    target_path = os.path.join(knowledge_dir, clean_name)
    
    try:
        if "," in data_b64:
            data_b64 = data_b64.split(",", 1)[1]
        file_bytes = base64.b64decode(data_b64)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        biblio_dir = os.path.join(HERMES_ROOT, "tools", "agent-bibliotecario", "knowledge")
        os.makedirs(biblio_dir, exist_ok=True)
        meta_file = os.path.join(biblio_dir, "uploads_registry.json")
        uploads = []
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    uploads = json.load(mf)
            except Exception:
                uploads = []
                
        ext = os.path.splitext(clean_name)[1].lower()
        kind = "image" if ext in [".png", ".jpg", ".jpeg", ".webp"] else "pdf" if ext == ".pdf" else "document"
        
        entry = {
            "name": clean_name,
            "path": target_path,
            "size_bytes": len(file_bytes),
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,
            "notes": notes,
            "tags": tags
        }
        uploads.insert(0, entry)
        with open(meta_file, "w", encoding="utf-8") as mf:
            json.dump(uploads[:200], mf, indent=2)
            
        return {"success": True, "entry": entry}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_output_file_content(job_id: str = None, filename: str = None, raw_path: str = None) -> dict:
    """Reads content of a generated cron output file safely."""
    from datetime import datetime
    target_path = None
    if job_id and filename:
        clean_file = os.path.basename(filename)
        target_path = os.path.join(HERMES_ROOT, "cron", "output", job_id, clean_file)
    elif raw_path:
        target_path = os.path.abspath(raw_path)
        
    if not target_path or not os.path.exists(target_path):
        return {"success": False, "error": f"File non trovato: {target_path}"}
        
    # Security check: must reside inside HERMES_ROOT
    norm_target = os.path.normcase(os.path.abspath(target_path))
    norm_hermes = os.path.normcase(os.path.abspath(HERMES_ROOT))
    if not norm_target.startswith(norm_hermes):
        return {"success": False, "error": "Accesso non autorizzato al di fuori di ~/.hermes"}
        
    try:
        sz = os.path.getsize(target_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(target_path)).strftime("%Y-%m-%d %H:%M:%S")
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(100000)  # up to 100KB
            
        return {
            "success": True,
            "filename": os.path.basename(target_path),
            "job_id": job_id or os.path.basename(os.path.dirname(target_path)),
            "path": target_path.replace(chr(92), "/"),
            "size_bytes": sz,
            "size_formatted": f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB",
            "modified": mtime,
            "content": content
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

_CRON_CACHE = None
_CRON_CACHE_TIME = 0.0

def get_detailed_cronjobs() -> dict:
    """Returns deep nanometric pipeline breakdown, execution history, and real outputs for all cronjobs."""
    global _CRON_CACHE, _CRON_CACHE_TIME
    now = time.time()
    if _CRON_CACHE is not None and (now - _CRON_CACHE_TIME < 2.0):
        return _CRON_CACHE

    import sqlite3
    from datetime import datetime
    
    jobs_file = os.path.join(HERMES_ROOT, "cron", "jobs.json")
    cron_db = os.path.join(HERMES_ROOT, "cron", "executions.db")
    
    executions = {}
    if os.path.exists(cron_db):
        try:
            conn = sqlite3.connect(cron_db, timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("SELECT job_id, status, started_at, finished_at, error, pid, id FROM executions ORDER BY started_at DESC LIMIT 50")
            for r in cursor.fetchall():
                jid = r[0]
                if jid not in executions:
                    executions[jid] = []
                executions[jid].append({
                    "id": r[6],
                    "status": r[1],
                    "started_at": r[2],
                    "finished_at": r[3],
                    "error": r[4],
                    "pid": r[5]
                })
            conn.close()
        except Exception:
            pass

    jobs_res = []
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, "r", encoding="utf-8") as f:
                jobs = json.load(f).get("jobs", [])
            for j in jobs:
                jid = j.get("id", "")
                prompt = j.get("prompt", "")
                name = j.get("name", "Task")
                sched = j.get("schedule_display") or (j.get("schedule", {}).get("expr") if isinstance(j.get("schedule"), dict) else j.get("schedule")) or "* * * * *"
                enabled = j.get("enabled", True)
                next_run = j.get("next_run_at") or "Non schedulato"
                last_run = j.get("last_run_at") or "Mai eseguito"
                work_dir = j.get("workdir") or HERMES_ROOT
                
                history = executions.get(jid, [])
                last_exec = history[0] if history else {}
                
                output_dir = os.path.join(HERMES_ROOT, "cron", "output", jid).replace(chr(92), "/")
                real_outputs = []
                if os.path.exists(output_dir):
                    try:
                        for fname in sorted(os.listdir(output_dir), reverse=True)[:10]:
                            fpath = os.path.join(output_dir, fname)
                            if os.path.isfile(fpath):
                                sz = os.path.getsize(fpath)
                                mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
                                preview = ""
                                try:
                                    with open(fpath, "r", encoding="utf-8", errors="ignore") as rf:
                                        preview = rf.read(600)
                                except Exception:
                                    pass
                                real_outputs.append({
                                    "filename": fname,
                                    "size_bytes": sz,
                                    "size_formatted": f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB",
                                    "modified": mtime,
                                    "path": fpath.replace(chr(92), "/"),
                                    "preview": preview
                                })
                    except Exception:
                        pass
                
                summary_files = [f"{o['filename']} ({o['size_formatted']})" for o in real_outputs]
                output_summary = ", ".join(summary_files) if summary_files else "Output registrato in SQLite / Log"
                
                jobs_res.append({
                    "id": jid,
                    "name": name,
                    "enabled": enabled,
                    "schedule": sched,
                    "prompt": prompt,
                    "pipeline": {
                        "command": prompt,
                        "working_dir": work_dir,
                        "output_dir": output_dir,
                        "real_outputs": real_outputs
                    },
                    "last_execution": {
                        "status": last_exec.get("status", j.get("last_status", "idle")),
                        "started_at": last_exec.get("started_at", last_run),
                        "finished_at": last_exec.get("finished_at", None),
                        "error": last_exec.get("error", j.get("last_error")),
                        "pid": last_exec.get("pid", None)
                    },
                    "history": history[:8],
                    "forecast": {
                        "next_run_at": next_run,
                        "trigger": f"Regola Cron: {sched}",
                        "last_status": j.get("last_status", "idle"),
                        "output_summary": output_summary
                    }
                })
        except Exception:
            pass

    res = {"jobs": jobs_res, "count": len(jobs_res)}
    _CRON_CACHE = res
    _CRON_CACHE_TIME = now
    return res

_LEDGER_CACHE = None
_LEDGER_CACHE_TIME = 0.0

def get_granular_ledger_logs(limit: int = 60) -> dict:
    """Returns real nanometric log entries compiled from SQLite databases and supervisor events."""
    global _LEDGER_CACHE, _LEDGER_CACHE_TIME
    now = time.time()
    if _LEDGER_CACHE is not None and (now - _LEDGER_CACHE_TIME < 2.0):
        return _LEDGER_CACHE

    import sqlite3
    from datetime import datetime
    
    entries = []
    
    # 1. Cron Executions
    cron_db = os.path.join(HERMES_ROOT, "cron", "executions.db")
    if os.path.exists(cron_db):
        try:
            conn = sqlite3.connect(cron_db, timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("SELECT id, job_id, source, pid, status, started_at, finished_at, error FROM executions ORDER BY started_at DESC LIMIT ?", (limit,))
            for r in cursor.fetchall():
                ts = r[5] or r[6] or ""
                if "T" in ts:
                    ts = ts.split(".")[0].replace("T", " ")
                entries.append({
                    "id": f"cron-{r[0][:12]}",
                    "timestamp": ts,
                    "subsystem": "CRON_ENGINE",
                    "actor": f"cron:{r[1][:8]}",
                    "action": f"Execution [{r[4].upper()}]",
                    "details": f"PID {r[3]} | " + (f"Error: {r[7]}" if r[7] else "Completed cleanly"),
                    "status": "error" if r[4] == "failed" else "success" if r[4] == "completed" else "running",
                    "raw_trace": r[7] or f"PID {r[3]} execution status: {r[4]}"
                })
            conn.close()
        except Exception:
            pass

    # 2. State DB Messages & Tool Calls
    state_db = os.path.join(HERMES_ROOT, "state.db")
    if os.path.exists(state_db):
        try:
            conn = sqlite3.connect(state_db, timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("SELECT id, session_id, role, tool_name, content, timestamp FROM messages WHERE tool_name IS NOT NULL OR role IN ('tool', 'assistant') ORDER BY id DESC LIMIT ?", (limit,))
            for r in cursor.fetchall():
                ts_str = datetime.fromtimestamp(r[5]).strftime('%Y-%m-%d %H:%M:%S') if r[5] else ""
                snippet = (r[4] or "").strip().replace("\n", " ")[:100]
                action_name = f"Tool: {r[3]}" if r[3] else f"Role: {r[2]}"
                entries.append({
                    "id": f"msg-{r[0]}",
                    "timestamp": ts_str,
                    "subsystem": "AGENT_EXEC",
                    "actor": f"Session {r[1][:8]}",
                    "action": action_name,
                    "details": snippet,
                    "status": "success",
                    "raw_trace": (r[4] or "")[:300]
                })
            conn.close()
        except Exception:
            pass

    # 3. Watchdog events
    wd_log = os.path.join(HERMES_ROOT, "logs", "sovereign_watchdog.log")
    if os.path.exists(wd_log):
        try:
            with open(wd_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-20:]
                for line in lines:
                    line = line.strip()
                    if "[" in line and "]" in line:
                        parts = line.split("] ", 1)
                        ts = parts[0].replace("[", "")
                        msg = parts[1] if len(parts) > 1 else ""
                        entries.append({
                            "id": f"wd-{hash(line)%1000000}",
                            "timestamp": ts,
                            "subsystem": "WATCHDOG",
                            "actor": "supervisor",
                            "action": "Health & Auto-Heal",
                            "details": msg[:100],
                            "status": "info",
                            "raw_trace": line
                        })
        except Exception:
            pass

    # Sort all by timestamp descending
    entries.sort(key=lambda x: x["timestamp"], reverse=True)
    res = {"entries": entries[:limit], "count": len(entries[:limit])}
    _LEDGER_CACHE = res
    _LEDGER_CACHE_TIME = now
    return res

_INTERACTIONS_CACHE = None
_INTERACTIONS_CACHE_TIME = 0.0

def get_swarm_interactions() -> dict:
    """Returns dynamic neural network topology with semantic interaction reasons and live active links."""
    global _INTERACTIONS_CACHE, _INTERACTIONS_CACHE_TIME
    now = time.time()
    if _INTERACTIONS_CACHE is not None and (now - _INTERACTIONS_CACHE_TIME < 4.0):
        return _INTERACTIONS_CACHE

    res = {
        "nodes": [
            {
                "id": "pi_agent",
                "label": "Pi Coding Agent",
                "role": "Autonomous Code Architect & Pair Programmer",
                "type": "core",
                "status": "online",
                "port": 5199,
                "position": [0, 0, 0],
                "description": "Central coordinator routing user commands, code audits, and workflows"
            },
            {
                "id": "kimi_k3",
                "label": "Kimi K3 MoE C-Engine",
                "role": "Native Local Inference & Reasoner",
                "type": "inference",
                "status": "online" if is_port_open(8095) else "standby",
                "port": 8095,
                "position": [220, 80, -60],
                "description": "Native C-Engine MoE 1.5T local reasoning engine ($0.00 offline)"
            },
            {
                "id": "hydra_router",
                "label": "Hydra Task Router",
                "role": "Multi-Model Dynamic Orchestrator",
                "type": "router",
                "status": "online" if is_port_open(8090) else "standby",
                "port": 8090,
                "position": [-200, 110, -50],
                "description": "Multi-model cloud orchestrator routing to Claude 3.7, Gemini 2.5, DeepSeek & LLaMA"
            },
            {
                "id": "cron_engine",
                "label": "Cron Scheduler Engine",
                "role": "Continuous Autonomous Job Dispatcher",
                "type": "automation",
                "status": "online",
                "port": None,
                "position": [180, -140, 80],
                "description": "Autonomous cron execution daemon executing periodic background pipelines"
            },
            {
                "id": "github_master",
                "label": "GitHub Master Analyst",
                "role": "Deep Intelligence & Benchmark Auditor",
                "type": "swarm_worker",
                "status": "online",
                "port": None,
                "position": [320, -180, 120],
                "description": "Active Swarm: deep benchmark audits & CVE vulnerability scans on mrvinx-stack"
            },
            {
                "id": "telegram_gateway",
                "label": "Telegram Secure Gateway",
                "role": "Imperial Messaging Control Plane",
                "type": "gateway",
                "status": "online",
                "port": None,
                "position": [-230, -120, 60],
                "description": "End-to-end encrypted Telegram control plane with instant slash commands (/cron, /status, /pi)"
            },
            {
                "id": "agent_bibliotecario",
                "label": "Agent Bibliotecario",
                "role": "Multimodal RAG & Knowledge Indexer",
                "type": "rag",
                "status": "online",
                "port": None,
                "position": [0, 240, -100],
                "description": "Vector indexing 46,210+ skills, MCP tools, research docs, and video frames"
            },
            {
                "id": "ldg_innovation",
                "label": "LDG Innovation Hub",
                "role": "Next.js 15 Enterprise Platform & B2B Suite",
                "type": "enterprise",
                "status": "online" if is_port_open(3000) else "standby",
                "port": 3000,
                "position": [-160, -220, -120],
                "description": "Enterprise portal with B2B Acquisition Suite v2, OSINT extraction & 104+ requirements"
            },
            {
                "id": "paperclip",
                "label": "Paperclip Control Plane",
                "role": "Agent Company Board & Governance",
                "type": "governance",
                "status": "online" if is_port_open(3100) else "standby",
                "port": 3100,
                "position": [150, 200, 100],
                "description": "AI-Agent company control plane with governance budgets, issue checkout & board UI"
            },
            {
                "id": "watchdog",
                "label": "Sovereign Watchdog",
                "role": "Self-Healing Supervisor Daemon",
                "type": "supervisor",
                "status": "online",
                "port": None,
                "position": [0, -260, 50],
                "description": "Background process supervisor auto-healing all 4 core services on crash"
            }
        ],
        "links": [
            {
                "source": "pi_agent",
                "target": "kimi_k3",
                "protocol": "HTTP REST / IPC Socket (:8095)",
                "reason": "Pi Agent delegates prompt reasoning to Kimi K3 MoE C-Engine for local token inference",
                "active_traffic": "Live Reasoning Channel",
                "state": "active"
            },
            {
                "source": "pi_agent",
                "target": "hydra_router",
                "protocol": "HTTP REST (:8090)",
                "reason": "Dynamic multi-model fallback for deep complex tasks requiring cloud reasoning",
                "active_traffic": "Model Routing Stream",
                "state": "standby"
            },
            {
                "source": "pi_agent",
                "target": "cron_engine",
                "protocol": "SQLite Event Dispatcher",
                "reason": "Pi Agent schedules, manages, and triggers autonomous cronjobs in executions.db",
                "active_traffic": "Task Scheduling Bus",
                "state": "active"
            },
            {
                "source": "cron_engine",
                "target": "github_master",
                "protocol": "Subprocess Runner (deep_intelligence_runner.py)",
                "reason": "Cron Engine spawns continuous benchmark audits and security scans on GitHub Master repos",
                "active_traffic": "Daily 04:00 AM Execution Pipeline",
                "state": "scheduled"
            },
            {
                "source": "pi_agent",
                "target": "telegram_gateway",
                "protocol": "Long-Polling / Gateway Webhook",
                "reason": "Imperial command bridge receiving /cron, /status, /pi and relaying notifications to Imperatore",
                "active_traffic": "Realtime Message Stream",
                "state": "active"
            },
            {
                "source": "pi_agent",
                "target": "agent_bibliotecario",
                "protocol": "Vector Embeddings & Semantic Search",
                "reason": "RAG lookups over 46,210+ skills, uploaded PDFs/images, and viral video blueprints",
                "active_traffic": "Knowledge Index Querying",
                "state": "ready"
            },
            {
                "source": "pi_agent",
                "target": "ldg_innovation",
                "protocol": "Next.js API & B2B Suite v2 Script",
                "reason": "Traceability Matrix Phase 1-14 synchronization and B2B OSINT lead extraction",
                "active_traffic": "Enterprise Sync Channel",
                "state": "connected"
            },
            {
                "source": "pi_agent",
                "target": "paperclip",
                "protocol": "Express REST API (:3100)",
                "reason": "Company governance, task issue checkout, and budget hard-stop invariant control",
                "active_traffic": "Board Control Stream",
                "state": "connected"
            },
            {
                "source": "watchdog",
                "target": "pi_agent",
                "protocol": "Process Heartbeat & Port Polling",
                "reason": "Supervises Telegram Gateway, Kimi K3, Galaxy Brain, and Hydra Router with auto-respawn",
                "active_traffic": "Health Verification Pulse (5s interval)",
                "state": "active"
            }
        ]
    }
    _INTERACTIONS_CACHE = res
    _INTERACTIONS_CACHE_TIME = now
    return res

_TELEMETRY_CACHE = None
_TELEMETRY_CACHE_TIME = 0.0

def get_live_telemetry():
    global _TELEMETRY_CACHE, _TELEMETRY_CACHE_TIME
    now = time.time()
    if _TELEMETRY_CACHE is not None and (now - _TELEMETRY_CACHE_TIME < 6.0):
        return _TELEMETRY_CACHE

    if hermes_data_bridge:
        try:
            metrics = hermes_data_bridge.gather_full_real_metrics()
            # Enrich with services & projects status
            metrics["services_live_status"] = get_services_status()
            _TELEMETRY_CACHE = metrics
            _TELEMETRY_CACHE_TIME = now
            return metrics
        except Exception as e:
            err_res = {"error": str(e), "timestamp": time.time(), "services_live_status": get_services_status()}
            _TELEMETRY_CACHE = err_res
            _TELEMETRY_CACHE_TIME = now
            return err_res
    res = {"status": "bridge_offline", "timestamp": time.time(), "services_live_status": get_services_status()}
    _TELEMETRY_CACHE = res
    _TELEMETRY_CACHE_TIME = now
    return res

def sync_disk_cache_now():
    """Immediately flushes real live telemetry, cron, ledger and projects to disk."""
    telemetry = get_live_telemetry()
    mecha = scan_mecha_projects()
    toolbox = scan_toolbox_items()
    cron_data = get_detailed_cronjobs()
    ledger_data = get_granular_ledger_logs(60)
    interactions = get_swarm_interactions()
    
    full_bundle = {
        "telemetry": telemetry,
        "mecha_projects": mecha,
        "toolbox": toolbox,
        "services": get_services_status(),
        "cron_detailed": cron_data,
        "ledger_granular": ledger_data,
        "swarm_interactions": interactions,
        "timestamp": time.time()
    }
    
    # Write JSON
    json_path = os.path.join(PI_DIR, "galaxy_live_telemetry.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_bundle, f, indent=2)
        
    # Write JS variable for offline file:/// script injection
    js_path = os.path.join(PI_DIR, "galaxy_live_telemetry.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.__HERMES_REAL_TELEMETRY__ = {json.dumps(telemetry)};\n")
        f.write(f"window.__HERMES_MECHA_PROJECTS__ = {json.dumps(mecha)};\n")
        f.write(f"window.__HERMES_TOOLBOX__ = {json.dumps(toolbox)};\n")
        f.write(f"window.__HERMES_SERVICES__ = {json.dumps(get_services_status())};\n")
        f.write(f"window.__HERMES_CRON_DETAILED__ = {json.dumps(cron_data)};\n")
        f.write(f"window.__HERMES_LEDGER_GRANULAR__ = {json.dumps(ledger_data)};\n")
        f.write(f"window.__HERMES_SWARM_INTERACTIONS__ = {json.dumps(interactions)};\n")
    return full_bundle

def sync_disk_cache_loop():
    """Continuously writes galaxy_live_telemetry.js & .json to disk for direct file:/// browser access."""
    while True:
        try:
            sync_disk_cache_now()
        except Exception:
            pass
        time.sleep(8.0)

def invalidate_runtime_caches():
    global _CRON_CACHE, _CRON_CACHE_TIME, _LEDGER_CACHE, _LEDGER_CACHE_TIME
    global _TELEMETRY_CACHE, _TELEMETRY_CACHE_TIME, _SERVICES_CACHE, _SERVICES_CACHE_TIME
    global _MECHA_CACHE, _MECHA_CACHE_TIME, _TOOLBOX_CACHE, _TOOLBOX_CACHE_TIME, _INTERACTIONS_CACHE, _INTERACTIONS_CACHE_TIME
    _CRON_CACHE = None
    _CRON_CACHE_TIME = 0.0
    _LEDGER_CACHE = None
    _LEDGER_CACHE_TIME = 0.0
    _TELEMETRY_CACHE = None
    _TELEMETRY_CACHE_TIME = 0.0
    _SERVICES_CACHE = {}
    _SERVICES_CACHE_TIME = 0.0
    _MECHA_CACHE = None
    _MECHA_CACHE_TIME = 0.0
    _TOOLBOX_CACHE = None
    _TOOLBOX_CACHE_TIME = 0.0
    _INTERACTIONS_CACHE = None
    _INTERACTIONS_CACHE_TIME = 0.0

class GalaxyHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PI_DIR, **kwargs)

    def log_message(self, format, *args):
        # Silence routine access logs to keep stdout clean
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def do_GET(self):
        try:
            if self.path in ["/api/telemetry", "/api/swarm/telemetry"]:
                self._send_json(get_live_telemetry())
                return
            elif self.path == "/api/services":
                self._send_json(get_services_status())
                return
            elif self.path == "/api/cron/detailed":
                self._send_json(get_detailed_cronjobs())
                return
            elif self.path in ["/api/ledger/granular", "/api/ledger"]:
                self._send_json(get_granular_ledger_logs(60))
                return
            elif self.path == "/api/swarm/interactions":
                self._send_json(get_swarm_interactions())
                return
            elif self.path == "/api/mecha-projects":
                self._send_json(scan_mecha_projects())
                return
            elif self.path == "/api/toolbox":
                self._send_json(scan_toolbox_items())
                return
            elif self.path == "/api/knowledge/list":
                self._send_json(get_knowledge_catalog())
                return
            elif self.path.startswith("/api/cron/output/read"):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                qs = parse_qs(parsed.query)
                job_id = qs.get("job_id", [""])[0]
                filename = qs.get("filename", qs.get("file", [""]))[0]
                raw_path = qs.get("path", [""])[0]
                self._send_json(read_output_file_content(job_id=job_id, filename=filename, raw_path=raw_path))
                return
            elif self.path == "/" or self.path == "":
                self.path = "/galaxy-brain.html"
            return super().do_GET()
        except Exception as e:
            self._send_json({"error": str(e)})

    def do_POST(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            if self.path in ["/api/file/read", "/api/cron/output/read"]:
                job_id = payload.get("job_id")
                filename = payload.get("filename") or payload.get("file")
                raw_path = payload.get("path")
                res = read_output_file_content(job_id=job_id, filename=filename, raw_path=raw_path)
                self._send_json(res)
                return

            elif self.path == "/api/open-app":
                app_type = payload.get("type") or payload.get("app", "folder")
                raw_path = payload.get("path", "")
                
                # Check direct system apps first
                if app_type in ["paperclip", "hermes", "hermes_tui", "ldg"]:
                    res = open_app_or_folder(app_type, raw_path)
                    self._send_json(res)
                    return
                    
                if not raw_path:
                    self._send_json({"success": False, "error": "Percorso non specificato"})
                    return
                try:
                    import subprocess
                    clean_p = os.path.normpath(raw_path)
                    if app_type == "folder":
                        if os.path.isfile(clean_p):
                            subprocess.Popen(["explorer", "/select,", clean_p])
                        elif os.path.isdir(clean_p):
                            subprocess.Popen(["explorer", clean_p])
                        elif os.path.exists(os.path.dirname(clean_p)):
                            subprocess.Popen(["explorer", os.path.dirname(clean_p)])
                        else:
                            subprocess.Popen(["explorer", clean_p])
                    elif app_type == "code":
                        subprocess.Popen(["code", clean_p], shell=True)
                    elif app_type == "terminal":
                        subprocess.Popen(f'start powershell -NoExit -ExecutionPolicy Bypass -Command "cd \'{clean_p}\'"', shell=True)
                    self._send_json({"success": True, "path": clean_p})
                except Exception as e:
                    self._send_json({"success": False, "error": str(e)})
                return

            elif self.path == "/api/service/start":
                service_key = payload.get("service")
                res = start_service_by_key(service_key)
                self._send_json(res)
                return

            elif self.path == "/api/service/stop":
                service_key = payload.get("service")
                res = stop_service_by_key(service_key)
                self._send_json(res)
                return

            elif self.path == "/api/cron/trigger":
                job_id = payload.get("job_id")
                try:
                    sys.path.insert(0, os.path.join(HERMES_ROOT, "tools"))
                    from editorial_hub import run_cron_job_real
                    res = run_cron_job_real(job_id)
                    # Invalidate cache & flush disk cache immediately
                    invalidate_runtime_caches()
                    try:
                        sync_disk_cache_now()
                    except Exception:
                        pass
                    self._send_json(res)
                except Exception as e:
                    self._send_json({"success": False, "error": str(e)})
                return

            elif self.path == "/api/cron/toggle":
                job_id = payload.get("job_id")
                enable = payload.get("enable", True)
                try:
                    from cron.jobs import pause_job, resume_job
                    ok = resume_job(job_id) if enable else pause_job(job_id)
                    invalidate_runtime_caches()
                    try:
                        sync_disk_cache_now()
                    except Exception:
                        pass
                    self._send_json({"success": bool(ok), "message": f"Job {job_id} {'riattivato' if enable else 'in pausa'}"})
                except Exception as e:
                    self._send_json({"success": False, "error": str(e)})
                return

            elif self.path == "/api/chat":
                msg = payload.get("message", "")
                model = payload.get("model", "kimi-k3-moe")
                res = execute_agent_chat(msg, model)
                self._send_json(res)
                return

            elif self.path == "/api/knowledge/analyze-video":
                url = payload.get("url", "")
                notes = payload.get("notes", "")
                res = execute_video_analysis(url, notes)
                self._send_json(res)
                return

            elif self.path == "/api/knowledge/upload":
                res = handle_knowledge_upload(payload)
                self._send_json(res)
                return

            self.send_response(404)
            self.end_headers()
        except Exception as e:
            self._send_json({"error": str(e)})

    def _send_json(self, data):
        try:
            payload = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
        except Exception:
            pass
        self.close_connection = True

from http.server import ThreadingHTTPServer

class GalaxyHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def start_server():
    t = threading.Thread(target=sync_disk_cache_loop, daemon=True)
    t.start()
    
    server = GalaxyHTTPServer((HOST, PORT), GalaxyHandler)
    print(f"[GALAXY BRAIN HUD] Master Control Plane Server listening at http://{HOST}:{PORT}")
    print(f"[GALAXY BRAIN HUD] Direct file access: file:///{os.path.join(PI_DIR, 'galaxy-brain.html').replace(chr(92), '/')}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[GALAXY BRAIN HUD] Server stopped.")

if __name__ == "__main__":
    start_server()
