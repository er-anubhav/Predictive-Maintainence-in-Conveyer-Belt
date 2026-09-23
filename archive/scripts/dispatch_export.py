import asyncio, json, webbrowser, secrets, websockets, base64, os
from websockets.typing import Subprotocol

COLAB = "https://colab.research.google.com"
SCRATCH_PATH = "/notebooks/empty.ipynb"

class ExportBridge:
    def __init__(self):
        self.connected = asyncio.Event()
        self.ws = None
        self.req_id = 0
        self.responses = {}

    async def handle_ws(self, websocket):
        print(f"[BRIDGE] >>> Colab browser connected from {websocket.remote_address}!", flush=True)
        self.ws = websocket
        self.connected.set()
        try:
            async for msg in websocket:
                data = json.loads(msg)
                if "id" in data:
                    self.responses[data["id"]] = data
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected.clear()

    async def call_tool(self, name, arguments=None):
        self.req_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}}
        }
        await self.ws.send(json.dumps(msg))
        for _ in range(1200):
            await asyncio.sleep(0.2)
            if self.req_id in self.responses:
                return self.responses[self.req_id]
        return None

    async def run_code(self, cell_idx, code_str, title=""):
        print(f"\n>>> Running: {title} (cellIndex={cell_idx})...", flush=True)
        add_res = await self.call_tool("add_code_cell", {"cellIndex": cell_idx, "language": "python", "code": code_str})
        cell_id = add_res.get("result", {}).get("structuredContent", {}).get("newCellId")
        if not cell_id:
            cell_id = json.loads(add_res["result"]["content"][0]["text"])["newCellId"]
        
        run_res = await self.call_tool("run_code_cell", {"cellId": cell_id})
        outputs = run_res.get("result", {}).get("structuredContent", {}).get("outputs", [])
        output_texts = []
        for out in outputs:
            if out.get("output_type") == "stream":
                txt = "".join(out.get("text", []))
                print(txt, end="")
                output_texts.append(txt)
            elif out.get("output_type") == "error":
                print("\nERROR:", out.get("ename"), out.get("evalue"))
                print("\n".join(out.get("traceback", [])[-6:]))
        return "".join(output_texts)

async def main():
    token = secrets.token_urlsafe(16)
    session = ExportBridge()
    server = await websockets.serve(
        session.handle_ws,
        host="localhost",
        port=0,
        subprotocols=[Subprotocol("mcp")],
        origins=[COLAB, "https://colab.google.com"],
        process_request=lambda ws, req: None
    )
    port = server.sockets[0].getsockname()[1]
    url = f"{COLAB}{SCRATCH_PATH}#mcpProxyToken={token}&mcpProxyPort={port}"
    print(f"COLAB PROXY URL: {url}", flush=True)
    webbrowser.get("google-chrome").open_new(url)
    
    print("Waiting for Colab tab to connect...", flush=True)
    await session.connected.wait()
    print("Connected! Running export payload...", flush=True)

    export_py = '''
import os, json, base64

drive_dir = "/content/drive/MyDrive/SIH26008_ML"

def read_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

payload = {
    "v031_model": read_b64(f"{drive_dir}/models/iforest/v0.3.1/model.joblib"),
    "v031_norm": read_b64(f"{drive_dir}/models/iforest/v0.3.1/normalization.json"),
    "v031_thresh": read_b64(f"{drive_dir}/models/iforest/v0.3.1/threshold_config.json"),
    "v031_meta": read_b64(f"{drive_dir}/models/iforest/v0.3.1/metadata.json"),
    "v05_model": read_b64(f"{drive_dir}/models/iforest/v0.5/model.joblib"),
    "v05_comm": read_b64(f"{drive_dir}/models/iforest/v0.5/commissioning_reference.json"),
    "v061_model": read_b64(f"{drive_dir}/models/iforest/v0.6.1/model.joblib"),
    "v061_config": read_b64(f"{drive_dir}/models/iforest/v0.6.1/v0.6.1_config.json")
}

import json
# Print JSON with a special delimiter
print("---PAYLOAD_START---")
print(json.dumps(payload))
print("---PAYLOAD_END---")
'''
    res_str = await session.run_code(800, export_py, "Export Model Artifacts")
    if "---PAYLOAD_START---" in res_str:
        json_part = res_str.split("---PAYLOAD_START---")[1].split("---PAYLOAD_END---")[0].strip()
        data = json.loads(json_part)
        
        # Save locally
        dest_base = "/home/anubhavtripathi/Documents/Projects/SIH26008/models/iforest"
        os.makedirs(f"{dest_base}/v0.3.1", exist_ok=True)
        os.makedirs(f"{dest_base}/v0.5", exist_ok=True)
        os.makedirs(f"{dest_base}/v0.6.1", exist_ok=True)
        
        if data.get("v031_model"):
            with open(f"{dest_base}/v0.3.1/model.joblib", "wb") as f:
                f.write(base64.b64decode(data["v031_model"]))
        if data.get("v031_norm"):
            with open(f"{dest_base}/v0.3.1/normalization.json", "wb") as f:
                f.write(base64.b64decode(data["v031_norm"]))
        if data.get("v031_thresh"):
            with open(f"{dest_base}/v0.3.1/threshold_config.json", "wb") as f:
                f.write(base64.b64decode(data["v031_thresh"]))
        if data.get("v031_meta"):
            with open(f"{dest_base}/v0.3.1/metadata.json", "wb") as f:
                f.write(base64.b64decode(data["v031_meta"]))
        if data.get("v05_model"):
            with open(f"{dest_base}/v0.5/model.joblib", "wb") as f:
                f.write(base64.b64decode(data["v05_model"]))
        if data.get("v05_comm"):
            with open(f"{dest_base}/v0.5/commissioning_reference.json", "wb") as f:
                f.write(base64.b64decode(data["v05_comm"]))
        if data.get("v061_model"):
            with open(f"{dest_base}/v0.6.1/model.joblib", "wb") as f:
                f.write(base64.b64decode(data["v061_model"]))
        if data.get("v061_config"):
            with open(f"{dest_base}/v0.6.1/v0.6.1_config.json", "wb") as f:
                f.write(base64.b64decode(data["v061_config"]))
        print("\n[SUCCESS] Successfully synced model artifacts from Colab to local repository!")
    else:
        print("\n[FAILED] Delimiters not found in output")

if __name__ == "__main__":
    asyncio.run(main())
