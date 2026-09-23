import json
import os
import sys
from typing import Dict, Any, Optional, Tuple

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


class TelemetrySender:
    def __init__(self, target_url: Optional[str] = None, timeout: float = 5.0):
        # Default target API endpoint
        self.target_url = target_url or os.getenv(
            "TELEMETRY_API_URL", "http://localhost:8000/api/v1/telemetry"
        )
        self.timeout = timeout

    def send(self, payload: Dict[str, Any]) -> Tuple[bool, int, str]:
        """
        Sends telemetry dictionary payload to destination endpoint via HTTP POST.
        Returns:
            (is_success, status_code, message)
        """
        if HAS_REQUESTS:
            try:
                response = requests.post(
                    self.target_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout,
                )
                if response.status_code in (200, 201, 202):
                    return True, response.status_code, response.text
                else:
                    return False, response.status_code, response.text
            except requests.RequestException as e:
                return False, 0, str(e)
        else:
            # Fallback to standard library urllib
            try:
                data_bytes = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.target_url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_body = resp.read().decode("utf-8")
                    if resp.status in (200, 201, 202):
                        return True, resp.status, resp_body
                    else:
                        return False, resp.status, resp_body
            except urllib.error.HTTPError as e:
                return False, e.code, e.read().decode("utf-8")
            except Exception as e:
                return False, 0, str(e)
