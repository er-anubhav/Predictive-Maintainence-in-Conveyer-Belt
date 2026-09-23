import base64
code = '''
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
with open("/tmp/colab_export.json", "w") as f:
    json.dump(payload, f)
print("EXPORT_READY: " + str({k: len(v) if v else 0 for k, v in payload.items()}))
'''
print(code)
