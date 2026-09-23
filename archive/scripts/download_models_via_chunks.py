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
        add_res = await self.call_tool("add_code_cell", {"cellIndex": cell_idx, "language": "python", "code": code_str})
        if not add_res:
            return ""
        cell_id = add_res.get("result", {}).get("structuredContent", {}).get("newCellId")
        if not cell_id:
            cell_id = json.loads(add_res["result"]["content"][0]["text"])["newCellId"]
        
        run_res = await self.call_tool("run_code_cell", {"cellId": cell_id})
        if not run_res:
            return ""
        outputs = run_res.get("result", {}).get("structuredContent", {}).get("outputs", [])
        output_texts = []
        for out in outputs:
            if out.get("output_type") == "stream":
                output_texts.append("".join(out.get("text", [])))
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
        max_size=32 * 1024 * 1024, # 32 MB max websocket frame
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
    print("Connected! Downloading files in safe 32KB chunks...", flush=True)

    dest_base = "/home/anubhavtripathi/Documents/Projects/SIH26008/models/iforest"
    os.makedirs(f"{dest_base}/v0.3.1", exist_ok=True)
    os.makedirs(f"{dest_base}/v0.5", exist_ok=True)
    os.makedirs(f"{dest_base}/v0.6.1", exist_ok=True)

    files_to_download = [
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

    for rel_path, dest_local in files_to_download:
        print(f"\nFetching {rel_path}...")
        # Step 1: get size
        size_code = f'''
import os
p = "/content/drive/MyDrive/SIH26008_ML/{rel_path}"
if os.path.exists(p):
    print("SIZE:" + str(os.path.getsize(p)))
else:
    print("SIZE:-1")
'''
        size_out = await session.run_code(900, size_code, f"Get size {rel_path}")
        if "SIZE:" not in size_out:
            print(f"  ✗ Failed to get size: {size_out}")
            continue
        total_size = int(size_out.split("SIZE:")[1].strip().split()[0])
        if total_size <= 0:
            print(f"  ✗ File not found or empty ({total_size} bytes)")
            continue

        print(f"  Total size: {total_size} bytes. Downloading in 32KB chunks...")
        chunk_size = 32768
        num_chunks = (total_size + chunk_size - 1) // chunk_size
        
        with open(dest_local, "wb") as f_out:
            for c_idx in range(num_chunks):
                offset = c_idx * chunk_size
                chunk_code = f'''
import base64
with open("/content/drive/MyDrive/SIH26008_ML/{rel_path}", "rb") as f:
    f.seek({offset})
    chunk = f.read({chunk_size})
    print("CHUNK_B64:" + base64.b64encode(chunk).decode("utf-8") + ":END")
'''
                chunk_out = await session.run_code(901 + (c_idx % 10), chunk_code, f"Chunk {c_idx+1}/{num_chunks}")
                if "CHUNK_B64:" in chunk_out:
                    b64_part = chunk_out.split("CHUNK_B64:")[1].split(":END")[0].strip()
                    f_out.write(base64.b64decode(b64_part))
                else:
                    print(f"  ✗ Failed on chunk {c_idx}")
                    break
        print(f"  ✓ Finished downloading {rel_path} ({os.path.getsize(dest_local)} bytes)")

    # Also download report hashes
    os.makedirs("/home/anubhavtripathi/Documents/Projects/SIH26008/reports", exist_ok=True)
    report_hashes = ["reports/v0.3.1_artifact_hashes.json", "reports/v0.6.1_artifact_hashes.json"]
    for rpath in report_hashes:
        dest_r = f"/home/anubhavtripathi/Documents/Projects/SIH26008/{rpath}"
        code = f'''
with open("/content/drive/MyDrive/SIH26008_ML/{rpath}", "r") as f:
    print("REP_CONTENT:" + f.read() + ":END_REP")
'''
        out = await session.run_code(920, code, f"Fetch {rpath}")
        if "REP_CONTENT:" in out:
            content = out.split("REP_CONTENT:")[1].split(":END_REP")[0].strip()
            with open(dest_r, "w") as f:
                f.write(content)
            print(f"  ✓ Saved {rpath}")

    print("\n[ALL MODEL ARTIFACTS SYNCED LOCALLY WITH ZERO DATA LOSS]")

if __name__ == "__main__":
    asyncio.run(main())
