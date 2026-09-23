import asyncio, json, webbrowser, secrets, websockets, base64, os, sys
from websockets.typing import Subprotocol

COLAB = "https://colab.research.google.com"
SCRATCH_PATH = "/notebooks/empty.ipynb"

class ColabBridge:
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
        for _ in range(1500):
            await asyncio.sleep(0.2)
            if self.req_id in self.responses:
                return self.responses[self.req_id]
        return None

    async def run_code(self, cell_idx, code_str, title=""):
        print(f"\n>>> Running: {title} (cellIndex={cell_idx})...", flush=True)
        add_res = await self.call_tool("add_code_cell", {"cellIndex": cell_idx, "language": "python", "code": code_str})
        if not add_res:
            print("Failed to add cell!")
            return ""
        cell_id = add_res.get("result", {}).get("structuredContent", {}).get("newCellId")
        if not cell_id:
            cell_id = json.loads(add_res["result"]["content"][0]["text"])["newCellId"]
        
        run_res = await self.call_tool("run_code_cell", {"cellId": cell_id})
        if not run_res:
            print("Failed to get run_res!")
            return ""
        outputs = run_res.get("result", {}).get("structuredContent", {}).get("outputs", [])
        output_texts = []
        for out in outputs:
            if out.get("output_type") == "stream":
                txt = "".join(out.get("text", []))
                output_texts.append(txt)
            elif out.get("output_type") == "error":
                print("\nERROR:", out.get("ename"), out.get("evalue"))
                print("\n".join(out.get("traceback", [])[-6:]))
        return "".join(output_texts)

async def main():
    token = secrets.token_urlsafe(16)
    session = ColabBridge()
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
    print("Connected! Checking and downloading files chunk by chunk...", flush=True)

    dest_base = "/home/anubhavtripathi/Documents/Projects/SIH26008/models/iforest"
    os.makedirs(f"{dest_base}/v0.3.1", exist_ok=True)
    os.makedirs(f"{dest_base}/v0.5", exist_ok=True)
    os.makedirs(f"{dest_base}/v0.6.1", exist_ok=True)

    files_to_fetch = [
        ("models/iforest/v0.3.1/model.joblib", f"{dest_base}/v0.3.1/model.joblib"),
        ("models/iforest/v0.3.1/normalization.json", f"{dest_base}/v0.3.1/normalization.json"),
        ("models/iforest/v0.3.1/threshold_config.json", f"{dest_base}/v0.3.1/threshold_config.json"),
        ("models/iforest/v0.3.1/metadata.json", f"{dest_base}/v0.3.1/metadata.json"),
        ("models/iforest/v0.3.1/model_card.md", f"{dest_base}/v0.3.1/model_card.md"),
        ("models/iforest/v0.5/model.joblib", f"{dest_base}/v0.5/model.joblib"),
        ("models/iforest/v0.5/commissioning_reference.json", f"{dest_base}/v0.5/commissioning_reference.json"),
        ("models/iforest/v0.5/model_card.md", f"{dest_base}/v0.5/model_card.md"),
        ("models/iforest/v0.6.1/model.joblib", f"{dest_base}/v0.6.1/model.joblib"),
        ("models/iforest/v0.6.1/v0.6.1_config.json", f"{dest_base}/v0.6.1/v0.6.1_config.json"),
        ("models/iforest/v0.6.1/model_card.md", f"{dest_base}/v0.6.1/model_card.md"),
    ]

    for rel_path, dest_local in files_to_fetch:
        code = f'''
import os, base64
p = "/content/drive/MyDrive/SIH26008_ML/{rel_path}"
if os.path.exists(p):
    with open(p, "rb") as f:
        print("B64_START:" + base64.b64encode(f.read()).decode("utf-8") + ":B64_END")
else:
    print("NOT_FOUND")
'''
        out = await session.run_code(810, code, f"Fetch {rel_path}")
        if "B64_START:" in out:
            b64_str = out.split("B64_START:")[1].split(":B64_END")[0].strip()
            with open(dest_local, "wb") as f:
                f.write(base64.b64decode(b64_str))
            print(f"  ✓ Downloaded {rel_path} ({os.path.getsize(dest_local)} bytes)")
        else:
            print(f"  ✗ Could not fetch {rel_path}")

    # Also fetch reports/v0.3.1_artifact_hashes.json and reports/v0.6.1_artifact_hashes.json
    report_files = [
        "reports/v0.3.1_artifact_hashes.json",
        "reports/v0.5_artifact_hashes.json",
        "reports/v0.6.1_artifact_hashes.json",
        "reports/poc_model_provenance.md"
    ]
    os.makedirs("/home/anubhavtripathi/Documents/Projects/SIH26008/reports", exist_ok=True)
    for rpath in report_files:
        code = f'''
import os, base64
p = "/content/drive/MyDrive/SIH26008_ML/{rpath}"
if os.path.exists(p):
    with open(p, "rb") as f:
        print("B64_START:" + base64.b64encode(f.read()).decode("utf-8") + ":B64_END")
else:
    print("NOT_FOUND")
'''
        out = await session.run_code(820, code, f"Fetch {rpath}")
        if "B64_START:" in out:
            b64_str = out.split("B64_START:")[1].split(":B64_END")[0].strip()
            with open(f"/home/anubhavtripathi/Documents/Projects/SIH26008/{rpath}", "wb") as f:
                f.write(base64.b64decode(b64_str))
            print(f"  ✓ Downloaded {rpath}")

    print("\n[ALL MODEL ARTIFACTS SYNCED LOCALLY]")

if __name__ == "__main__":
    asyncio.run(main())
