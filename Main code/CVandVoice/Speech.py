import speech_recognition as sr
import websocket
import google.generativeai as genai
import threading
import time
import signal
import sys

# ESP32 WebSocket IP (replace with your actual ESP32 IP)
ESP32_IP = "ws://192.168.47.254:81"  # Replace with your ESP32 IP address

# Gemini API Key
genai.configure(api_key="AIzaSyAx9VLRb83uZk0pjCq7p_O54ryaCLl2QNo")

# API limit variables
MAX_REQUESTS_PER_MINUTE = 15
request_counter = 0
last_request_time = time.time()

def get_intent(command):
    """Use Gemini AI to understand the user's command intent with throttling."""
    global request_counter, last_request_time
    
    # Check if the request limit has been reached in the last minute
    if request_counter >= MAX_REQUESTS_PER_MINUTE:
        # Wait for the next minute
        time_elapsed = time.time() - last_request_time
        if time_elapsed < 60:
            print(f"API limit reached. Sleeping for {60 - time_elapsed} seconds...")
            time.sleep(60 - time_elapsed)  # Sleep until the limit resets
        # Reset the request counter
        request_counter = 0
        last_request_time = time.time()

    prompt = f"Analyze this command and return ONLY the action: {command}. Possible actions: 'LED ON', 'LED OFF', 'FAN ON', 'FAN OFF', 'VIDEO PLAY', 'VIDEO PAUSE'. If unclear, return 'unknown'."
    
    model = genai.GenerativeModel("gemini-1.5-pro")  # ✅ Available in your API key

    try:
        response = model.generate_content(prompt)
        request_counter += 1  # Increment the request counter
        return response.text.strip().lower()
    
    except google.api_core.exceptions.ResourceExhausted as e:
        print(f"Error: {e}. Retrying in 30 seconds...")
        time.sleep(30)  # Wait for 30 seconds before retrying
        return get_intent(command)  # Retry the request after waiting

def on_message(ws, message):
    """Handles incoming messages from WebSocket (Optional)"""
    print(f"Received from ESP32: {message}")

def on_error(ws, error):
    """Handles WebSocket errors"""
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    """Handles WebSocket closure"""
    print("WebSocket closed")

def on_open(ws):
    """Handles WebSocket connection open"""
    print("WebSocket connected")

def execute_command(action, ws):
    """Send the appropriate command to ESP32 based on AI intent."""
    valid_commands = ["led on", "led off", "fan on", "fan off", "video play", "video pause"]
    
    if action in valid_commands:
        print(f"Sending: {action.upper()}")
        ws.send(action.upper())  # Send command to ESP32
    else:
        print("⚠️ Unknown command")

def reconnect_websocket(ws):
    """Reconnect WebSocket if closed."""
    print("Reconnecting to WebSocket...")
    while not ws.sock or not ws.sock.connected:
        try:
            ws.run_forever()  # Attempt to reconnect to the WebSocket server
            time.sleep(1)
        except Exception as e:
            print(f"Reconnection failed: {e}")
            time.sleep(5)  # Retry after 5 seconds if connection fails

def listen_and_process():
    recognizer = sr.Recognizer()

    # WebSocket connection
    ws = websocket.WebSocketApp(ESP32_IP,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)

    # Run WebSocket connection in a separate thread
    websocket_thread = threading.Thread(target=ws.run_forever)
    websocket_thread.start()  # Start the WebSocket connection in a new thread

    with sr.Microphone() as source:
        print("🎤 Listening for commands... (Say 'exit' to stop)")

        while True:
            try:
                print("🔄 Ready... Speak now!")
                audio = recognizer.listen(source, phrase_time_limit=5)  # Waits for input, max 5 sec per command
                command = recognizer.recognize_google(audio).lower()
                print(f"🎙 Recognized: {command}")

                if "exit" in command:
                    print("🛑 Exiting voice control...")
                    break  # Exit loop if user says "exit"

                action = get_intent(command)
                execute_command(action, ws)  # Send action to ESP32 via WebSocket

            except sr.UnknownValueError:
                print("❌ Could not understand audio")
            except sr.RequestError:
                print("⚠️ Speech recognition service unavailable")
            except sr.WaitTimeoutError:
                print("⌛ No speech detected. Waiting for input...")
                continue  # Keeps listening even if no speech is detected
            except KeyboardInterrupt:
                print("\n🛑 Stopping voice control...")
                break  # Allow manual stop with Ctrl+C

def stop_program(signal, frame):
    """Gracefully exit the program when Ctrl+C is pressed"""
    print("\n🛑 Exiting program...")
    sys.exit(0)

if __name__ == "__main__":
    # Register the SIGINT signal handler for graceful exit (Ctrl+C)
    signal.signal(signal.SIGINT, stop_program)
    listen_and_process()
