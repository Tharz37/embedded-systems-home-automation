import websocket

ESP32_IP = "ws://192.168.23.254:81"  # 🔹 Replace with your ESP32's IP

# Connect to ESP32 WebSocket Server
ws = websocket.WebSocket()
ws.connect(ESP32_IP)

# Send a test message
ws.send("Hello ESP32!")

# Receive response
response = ws.recv()
print("ESP32 says:", response)

# Close connection
ws.close()
