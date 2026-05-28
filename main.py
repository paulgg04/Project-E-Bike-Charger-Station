import uasyncio as asyncio
import json
import network
import time

# --- Setup Network connection ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print('Connected! IP address:', wlan.ifconfig()[0])

# Replace with your actual local network credentials
connect_wifi("Your_WiFi_SSID", "Your_WiFi_Password")

# The local IP address of your laptop running app.py
SERVER_IP = "10.189.15.212"  # Change to your computer's actual local IP

# Mock states for testing the system flow
simulated_soc = 10  # State of Charge (%)
simulated_energy = 0.0

async def send_telemetry_task():
    global simulated_soc, simulated_energy
    
    import usocket as socket
    
    # Simple manual WebSocket handshaking layout for MicroPython
    while True:
        try:
            ai = socket.getaddrinfo(SERVER_IP, 8000)
            addr = ai[0][-1]
            s = socket.socket()
            s.connect(addr)
            
            # Perform a basic HTTP Upgrade handshake to start WebSockets
            handshake = (
                "GET /ws/pico HTTP/1.1\r\n"
                f"Host: {SERVER_IP}:8000\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            )
            s.send(handshake.encode())
            response = s.recv(1024) # Clear handshake response from server buffer
            
            print("Successfully linked to Application Backend Server!")
            
            while True:
                # 1. Simulate changing metrics safely [cite: 61, 215]
                if simulated_soc < 100:
                    simulated_soc += 1
                simulated_current = 2.35  # Reading from I2C sensor [cite: 120, 130]
                simulated_power = (230 * simulated_current) / 1000.0  # kW [cite: 215]
                simulated_energy += (simulated_power * (2 / 3600))  # Accumulating Wh [cite: 215]
                
                # 2. Package data as a JSON packet layout structure [cite: 56, 164]
                telemetry_data = {
                    "soc": simulated_soc,
                    "current": simulated_current,
                    "power": simulated_power,
                    "energy": simulated_energy
                }
                
                payload = json.dumps(telemetry_data)
                
                # WebSocket text framing byte structure header
                bytes_payload = payload.encode('utf-8')
                length = len(bytes_payload)
                
                # Frame formatting header rule for unmasked text frame
                header = bytearray([0x81])
                if length <= 125:
                    header.append(length)
                s.send(header + bytes_payload)
                
                await asyncio.sleep(2) # Send updates every 2 seconds 
                
        except Exception as e:
            print("Connection dropped, retrying in 5s...", e)
            await asyncio.sleep(5)

asyncio.run(send_telemetry_task())