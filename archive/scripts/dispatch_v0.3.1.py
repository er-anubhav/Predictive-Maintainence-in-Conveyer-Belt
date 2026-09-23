import asyncio, json, webbrowser, secrets, websockets
from websockets.typing import Subprotocol

COLAB = "https://colab.research.google.com"
SCRATCH_PATH = "/notebooks/empty.ipynb"

class V031ColabBridge:
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
        for _ in range(3000): # wait up to 10 mins
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
        for out in outputs:
            if out.get("output_type") == "stream":
                print("".join(out.get("text", [])), end="")
            elif out.get("output_type") == "error":
                print("\nERROR:", out.get("ename"), out.get("evalue"))
                print("\n".join(out.get("traceback", [])[-6:]))
        return run_res

async def main():
    token = secrets.token_urlsafe(16)
    session = V031ColabBridge()
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
    print("Colab connected! Executing IF-v0.3.1 Leakage-Free Pipeline...", flush=True)

    with open("/home/anubhavtripathi/Documents/Projects/SIH26008/scripts/run_v0.3.1_pipeline.py") as f:
        code_to_run = f.read()

    await session.run_code(300, code_to_run, "Execute IF-v0.3.1 Leakage-Free Experiment")
    print("\n[IF-v0.3.1 EXPERIMENT] Execution complete!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
