from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from database import get_all_tenders, update_tender_status, init_db, save_tender
from ai import analyse_tender

app = FastAPI(title="MeraPath Tender Command Centre")

# Allow browser to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected WebSocket clients (for live alerts)
connected_clients = []

# ── STARTUP ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    print("✅ MeraPath Tender Command Centre is running!")
    print("📊 Open your browser at: http://localhost:8000")

# ── ROUTES ────────────────────────────────────────────────────────────────

@app.get("/")
async def home():
    """Serve the dashboard"""
    return FileResponse("frontend/index.html")

@app.get("/tenders")
async def get_tenders(priority: str = None, status: str = None):
    """Get all tenders — optionally filter by priority or status"""
    tenders = get_all_tenders(priority=priority, status=status)
    return {"tenders": tenders, "count": len(tenders)}

@app.get("/tenders/{tender_id}")
async def get_tender(tender_id: int):
    """Get a single tender by ID"""
    tenders = get_all_tenders()
    for t in tenders:
        if t["id"] == tender_id:
            return t
    return {"error": "Tender not found"}

@app.patch("/tenders/{tender_id}/status")
async def update_status(tender_id: int, body: dict):
    """Move a tender to a different pipeline stage"""
    new_status = body.get("status")
    valid = ["new", "reviewing", "bidding", "submitted", "won", "lost"]
    if new_status not in valid:
        return {"error": f"Status must be one of: {valid}"}
    update_tender_status(tender_id, new_status)

    # Notify all dashboard clients in real time
    await broadcast({
        "type": "status_update",
        "tender_id": tender_id,
        "new_status": new_status
    })
    return {"success": True, "tender_id": tender_id, "status": new_status}

@app.get("/stats")
async def get_stats():
    """Dashboard stat cards"""
    tenders = get_all_tenders()
    return {
        "total":       len(tenders),
        "critical":    sum(1 for t in tenders if t.get("priority") == "critical"),
        "high":        sum(1 for t in tenders if t.get("priority") == "high"),
        "eligible":    sum(1 for t in tenders if t.get("eligibility_status") == "met"),
        "total_value": f"₹{sum_values(tenders)}",
        "pipeline": {
            "new":       sum(1 for t in tenders if t.get("status") == "new"),
            "reviewing": sum(1 for t in tenders if t.get("status") == "reviewing"),
            "bidding":   sum(1 for t in tenders if t.get("status") == "bidding"),
            "submitted": sum(1 for t in tenders if t.get("status") == "submitted"),
        }
    }

@app.post("/scan")
async def trigger_scan():
    """Manually trigger the tender scan pipeline"""
    from scraper import run_daily_scan
    import asyncio

    # Run in background so API doesn't hang
    async def run_scan_background():
        results = run_daily_scan()
        await broadcast({
            "type": "scan_complete",
            "message": f"Scan done — {len(results)} tenders processed",
            "count": len(results)
        })

    asyncio.create_task(run_scan_background())
    return {"status": "Scan started", "message": "Check dashboard for results"}

@app.post("/analyse")
async def analyse_text(body: dict):
    """Analyse pasted tender text on the fly"""
    text  = body.get("text", "")
    title = body.get("title", "Manual Analysis")
    if not text:
        return {"error": "No text provided"}
    result = analyse_tender(text, title)
    return result

@app.get("/alerts")
async def get_alerts():
    """Get recent alerts"""
    tenders = get_all_tenders()
    alerts = []

    for t in tenders:
        # Flag tenders with deadlines soon
        if t.get("deadline") and t.get("status") not in ["submitted", "won", "lost"]:
            alerts.append({
                "type": "deadline",
                "tender_id": t["id"],
                "title": t["title"],
                "message": f"Deadline: {t['deadline']}",
                "priority": t.get("priority", "medium")
            })

    return {"alerts": alerts, "count": len(alerts)}

# ── WEBSOCKET ─────────────────────────────────────────────────────────────
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time alerts — dashboard connects here"""
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"📡 Dashboard connected ({len(connected_clients)} clients)")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"📡 Dashboard disconnected ({len(connected_clients)} clients)")

async def broadcast(message: dict):
    """Send a message to all connected dashboards"""
    dead = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            dead.append(client)
    for d in dead:
        connected_clients.remove(d)

# ── HELPER ────────────────────────────────────────────────────────────────
def sum_values(tenders):
    """Add up tender values for the stat card"""
    total = 0
    for t in tenders:
        val = t.get("value", "")
        try:
            # Handle "2.5 Cr", "1.8 Crore", "50 Lakh" etc.
            val = val.lower().replace(",", "").strip()
            if "cr" in val:
                num = float(''.join(c for c in val if c.isdigit() or c == '.'))
                total += num
            elif "lakh" in val:
                num = float(''.join(c for c in val if c.isdigit() or c == '.'))
                total += num / 100
        except Exception:
            pass
    return f"{total:.1f} Cr"

# ── RUN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)