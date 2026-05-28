from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
import json
import uvicorn

app = FastAPI()

# Store active smartphone application browser connections
active_connections = []

# --- Secure Server User Database ---
# Maps unique hardware NFC Card UIDs to user account profiles
USER_DATABASE = {
    "4A2C9F88": {"name": "Paul G.", "vehicle": "E-Bike Shimano", "balance_kwh": 15.5},
    "B3D912FF": {"name": "Raul Varga", "vehicle": "Trotinetă Xiaomi", "balance_kwh": 8.0}
}

# Tracks who is currently authenticated and charging at the physical station terminal
current_active_user = None

@app.get("/")
async def get_root_status():
    return {"status": "Central Communication Hub Active", "port": 8090}

# New endpoint specifically for testing and simulation via /docs
@app.post("/test-nfc-scan")
async def test_nfc_scan(uid: str = Body(..., embed=True, description="The NFC Card UID to simulate")):
    global current_active_user
    
    print(f"\n--- [SIMULATION] Received Test HTTP Post Scan Request for UID: {uid} ---")
    
    if uid in USER_DATABASE:
        current_active_user = USER_DATABASE[uid]
        print(f"[SIMULATION] Access GRANTED to: {current_active_user['name']}")
        
        simulated_packet = {
            "soc": 65,
            "current": 2.35,
            "power": 0.54,
            "energy": 1.48,
            "user_name": current_active_user["name"],
            "vehicle": current_active_user["vehicle"]
        }
        
        for connection in active_connections:
            await connection.send_json(simulated_packet)
            
        return {"status": "SUCCESS", "authenticated_user": current_active_user["name"], "message": "Phone app updated live!"}
    else:
        print(f"[SIMULATION] Access DENIED for unrecognized card ID: {uid}")
        current_active_user = None
        for connection in active_connections:
            await connection.send_json({
                "soc": 0, "current": 0.0, "power": 0.0, "energy": 0.0,
                "user_name": "Card Neautorizat!", "vehicle": "Acces Respins"
            })
        return {"status": "DENIED", "message": "Card ID not found in USER_DATABASE"}

# WebSocket Route: Handles smartphone dashboard view connections
@app.websocket("/ws/browser")
async def browser_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print("New smartphone app connection registered on server.")
    try:
        while True:
            await websocket.receive_text()  # Keeps the network pipe open
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Smartphone app connection closed.")

# WebSocket Route: Handles incoming stream from your Raspberry Pi Pico hardware
@app.websocket("/ws/pico")
async def pico_websocket(websocket: WebSocket):
    global current_active_user
    await websocket.accept()
    print("Raspberry Pi Pico hardware station connected successfully over Wi-Fi.")
    try:
        while True:
            data_string = await websocket.receive_text()
            data = json.loads(data_string)
            
            # Check if the incoming packet is a Card Scan Event from the NFC Module
            if "scan_uid" in data:
                scanned_uid = data["scan_uid"]
                print(f"NFC Scan Event Captured! Processing UID: {scanned_uid}")
                
                if scanned_uid in USER_DATABASE:
                    current_active_user = USER_DATABASE[scanned_uid]
                    print(f"Access GRANTED to: {current_active_user['name']}")
                    await websocket.send_json({
                        "auth_status": "SUCCESS", 
                        "user_name": current_active_user["name"]
                    })
                else:
                    print(f"Access DENIED for unrecognized card ID: {scanned_uid}")
                    await websocket.send_json({
                        "auth_status": "DENIED"
                    })
            
            # Handle standard charging telemetry metrics packets
            else:
                if current_active_user:
                    data["user_name"] = current_active_user["name"]
                    data["vehicle"] = current_active_user["vehicle"]
                else:
                    data["user_name"] = "Așteptare scanare..."
                    data["vehicle"] = "Vehicul: nescanat"
                
                for connection in active_connections:
                    await connection.send_json(data)
                    
    except WebSocketDisconnect:
        print("Raspberry Pi Pico hardware terminal disconnected.")
        current_active_user = None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)