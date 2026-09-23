import http.server
import socketserver
import os, json, sys, threading, time, base64

UPLOAD_DIR = "/home/anubhavtripathi/Documents/Projects/SIH26008/models/iforest"
os.makedirs(f"{UPLOAD_DIR}/v0.3.1", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/v0.5", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/v0.6.1", exist_ok=True)

class UploadHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(length)
        data = json.loads(post_data.decode('utf-8'))
        
        filename = data.get("filename") # e.g. "v0.3.1/model.joblib"
        content_b64 = data.get("content_b64")
        
        target_path = os.path.join(UPLOAD_DIR, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(content_b64))
            
        print(f"  [RECEIVER] Saved {filename} ({len(base64.b64decode(content_b64))} bytes)")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

PORT = 51841
server = socketserver.TCPServer(("0.0.0.0", PORT), UploadHandler)
print(f"Listening on port {PORT}...")
server.serve_forever()
