#include <WiFi.h>
#include <WebSocketsServer.h>

// Replace with your network credentials
const char* ssid = "SSID";         // Your Wi-Fi SSID
const char* password = "password"; // Your Wi-Fi password

WebSocketsServer webSocket(81);  // WebSocket server on port 81

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.print("Connected! ESP32 IP: ");
  Serial.println(WiFi.localIP());  // Print ESP32 IP

  // Start WebSocket server
  webSocket.begin();
  Serial.println("WebSocket server started!");

}

void loop() {
  // Keep checking WebSocket events
  webSocket.loop();
}
