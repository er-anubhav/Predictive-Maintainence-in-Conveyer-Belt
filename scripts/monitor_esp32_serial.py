#!/usr/bin/env python3
"""
SIH 26008 — ESP32 Conveyor Live Hardware Serial Monitor
======================================================
Connects directly to the physical NodeMCU-32 / ESP32 over USB serial,
continuously displays raw output, and parses live telemetry packets
to verify whether actual physical sensor/motor readings are being generated.
"""

import os
import sys
import glob
import json
import time
import re
import argparse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


# Configurable default thresholds
DEFAULT_BAUD = 115200
DEFAULT_STALE_SEC = 3.0
DEFAULT_DISCONNECT_SEC = 10.0


def find_serial_ports() -> List[Tuple[str, str]]:
    """Discovers available USB/ACM serial ports on Linux."""
    ports = []
    
    # 1. Use pySerial port listing if available
    if serial is not None:
        try:
            for p in serial.tools.list_ports.comports():
                dev = p.device
                desc = p.description or "Serial Device"
                hwid = p.hwid or ""
                if "USB" in dev or "ACM" in dev:
                    ports.append((dev, f"{desc} [{hwid}]"))
        except Exception:
            pass

    # 2. Direct filesystem glob fallback
    if not ports:
        candidates = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        for dev in candidates:
            desc = "USB Serial Interface"
            # Read sysfs device info if possible
            base = os.path.basename(dev)
            syspath = f"/sys/class/tty/{base}/device"
            if os.path.exists(syspath):
                desc = f"USB Serial Device ({base})"
            ports.append((dev, desc))

    return ports


def select_port(user_port: Optional[str] = None) -> str:
    """Selects target serial port automatically or interactively."""
    if user_port:
        if not os.path.exists(user_port):
            print(f"[-] Specified port '{user_port}' does not exist.")
            sys.exit(1)
        return user_port

    available = find_serial_ports()
    if not available:
        print("[-] No ESP32 serial devices found on /dev/ttyUSB* or /dev/ttyACM*.")
        print("    Please check physical USB cable connection and permissions.")
        print("    Try running: ls -l /dev/ttyUSB* /dev/ttyACM*")
        sys.exit(1)

    if len(available) == 1:
        selected = available[0][0]
        print(f"[+] Auto-detected single ESP32 port: {selected} ({available[0][1]})")
        return selected

    print("[?] Multiple serial ports detected:")
    for idx, (p, desc) in enumerate(available):
        print(f"    [{idx + 1}] {p} - {desc}")

    try:
        choice = input(f"Select port [1-{len(available)}]: ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(available):
            return available[idx][0]
    except (ValueError, EOFError, KeyboardInterrupt):
        pass

    return available[0][0]


class TelemetryParser:
    """Parses raw serial lines into structured telemetry or logs."""

    SAMPLE_REGEX = re.compile(
        r"\[SAMPLE\s+#(?P<seq>\d+)\]\s+"
        r"source=(?P<src>[^\s]+)\s+"
        r"vib_rms=(?P<rms>[0-9.]+)\s+"
        r"peak=(?P<peak>[0-9.]+)\s+"
        r"kurt=(?P<kurt>[0-9.]+)\s+"
        r"temp=(?P<temp>[0-9.]+)\s+"
        r"rpm=(?P<rpm>[0-9.]+)\s+"
        r"speed=(?P<speed>[0-9.]+)\s+"
        r"load=(?P<load>[0-9.]+)\s+"
        r"track=(?P<track>[+-]?[0-9.]+)"
    )

    @classmethod
    def parse_line(cls, line: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Returns (message_type, parsed_dict):
        message_type in ('CANONICAL_JSON', 'SAMPLE_TAG', 'BOOT_HEADER', 'LOG', 'RAW')
        """
        trimmed = line.strip()
        if not trimmed:
            return "EMPTY", None

        # 1. Try Canonical JSON packet
        if trimmed.startswith("{") and trimmed.endswith("}"):
            try:
                data = json.loads(trimmed)
                if isinstance(data, dict) and ("sequence" in data or "node_id" in data):
                    return "CANONICAL_JSON", data
            except json.JSONDecodeError:
                pass

        # 2. Try [SAMPLE #...] tag line
        m = cls.SAMPLE_REGEX.search(trimmed)
        if m:
            d = m.groupdict()
            parsed = {
                "sequence": int(d["seq"]),
                "source": d["src"],
                "vibration": {
                    "rms": float(d["rms"]),
                    "peak": float(d["peak"]),
                    "kurtosis": float(d["kurt"]),
                },
                "temperature": float(d["temp"]),
                "rpm": float(d["rpm"]),
                "belt_speed": float(d["speed"]),
                "load": float(d["load"]),
                "tracking_position": float(d["track"]),
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }
            return "SAMPLE_TAG", parsed

        # 3. Boot header detection
        if "SIH 26008 ESP32 CONVEYOR SENSOR NODE" in trimmed:
            return "BOOT_HEADER", {"text": trimmed}

        if trimmed.startswith("[") and "]" in trimmed:
            return "LOG", {"text": trimmed}

        return "RAW", {"text": trimmed}


class LiveHardwareMonitor:
    def __init__(self, port: str, baud: int, stale_sec: float, disconnect_sec: float):
        self.port = port
        self.baud = baud
        self.stale_sec = stale_sec
        self.disconnect_sec = disconnect_sec

        self.packets_received = 0
        self.valid_telemetry = 0
        self.invalid_unparsed = 0

        self.last_packet_time: Optional[float] = None
        self.last_sequence: Optional[int] = None
        self.sequence_advancing: bool = True
        self.sequence_stuck_count: int = 0

        self.packet_timestamps: List[float] = []
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        self.latest_raw_line: str = "<No data yet>"
        self.last_log_line: str = ""
        self.firmware_version: str = "Unknown"

    def calculate_rate(self) -> float:
        now = time.time()
        # Keep timestamps from last 5 seconds
        self.packet_timestamps = [t for t in self.packet_timestamps if now - t <= 5.0]
        if len(self.packet_timestamps) > 1:
            duration = self.packet_timestamps[-1] - self.packet_timestamps[0]
            if duration > 0.05:
                return float(len(self.packet_timestamps) / duration)
        return float(len(self.packet_timestamps)) / 5.0 if self.packet_timestamps else 0.0

    def compute_status(self) -> str:
        if self.last_packet_time is None:
            if self.last_log_line:
                clean_log = self.last_log_line.replace("\n", " ").strip()
                return f"BOOTING / INITIALIZING ({clean_log[:32]})"
            return "ESP32 BOOTING (Waiting for Sample #1 ~5-8s)"
        elapsed = time.time() - self.last_packet_time
        if elapsed >= self.disconnect_sec:
            return "DISCONNECTED / NO TELEMETRY"
        elif elapsed >= self.stale_sec:
            return "STALE"
        return "CONNECTED"

    def format_source_display(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Determines overall source and detailed per-modality breakdown.
        """
        primary = data.get("source")
        sources_obj = data.get("sensor_sources", {})

        if not primary:
            # Check if simulation flags exist
            if data.get("is_simulated") is True:
                primary = "SIMULATED"
            elif data.get("is_simulated") is False:
                primary = "REAL_HARDWARE"
            else:
                primary = "UNKNOWN"

        details = []
        if isinstance(sources_obj, dict):
            for k, v in sources_obj.items():
                tag = f"{k.upper()}={v}"
                details.append(tag)

        detail_str = " | ".join(details) if details else "No per-sensor source flags"
        return primary, detail_str

    def render_screen(self):
        # Clear screen and move cursor to top
        os.system("clear" if os.name == "posix" else "cls")

        status = self.compute_status()
        rate = self.calculate_rate()
        now_ts = time.time()
        elapsed_str = f"{(now_ts - self.last_packet_time):.1f} sec ago" if self.last_packet_time else "Never"

        data = self.latest_telemetry or {}

        # Envelope details
        seq = data.get("sequence", "N/A")
        node_id = data.get("node_id", "NODE-001")
        ts = data.get("timestamp", "--:--:--")
        if "T" in str(ts):
            ts = str(ts).split("T")[-1].replace("Z", "")

        # Physical metrics
        temp = data.get("temperature")
        temp_str = f"{temp:.1f} °C" if temp is not None and not (isinstance(temp, float) and (temp != temp)) else "N/A"

        rpm = data.get("rpm")
        rpm_str = f"{rpm:.1f} RPM" if rpm is not None else "0.0 RPM"

        speed = data.get("belt_speed")
        speed_str = f"{speed:.2f} m/s" if speed is not None else "0.00 m/s"

        # Vibration
        vib = data.get("vibration", {})
        if isinstance(vib, dict):
            rms = vib.get("rms")
            peak = vib.get("peak")
            kurt = vib.get("kurtosis")
            rms_str = f"{rms:.3f}g" if rms is not None else "--"
            peak_str = f"{peak:.3f}g" if peak is not None else "--"
            kurt_str = f"{kurt:.2f}" if kurt is not None else "--"
            vib_str = f"RMS={rms_str} | Peak={peak_str} | Kurt={kurt_str}"
        else:
            vib_str = "N/A"

        # Tracking / IR
        track = data.get("tracking_position")
        if track is not None:
            if abs(track) > 0.1:
                track_str = f"DRIFT DETECTED ({track:+.1f} mm)"
            else:
                track_str = "CENTERED (0.0 mm)"
        else:
            track_str = "N/A"

        # Load
        load = data.get("load")
        load_str = f"{load:.1f}%" if load is not None else "N/A"

        # Device Health
        health = data.get("device_health", {})
        wifi_str = "N/A"
        if isinstance(health, dict):
            wifi_conn = health.get("wifi_connected")
            rssi = health.get("wifi_rssi")
            if wifi_conn is True:
                wifi_str = f"ONLINE ({rssi} dBm)"
            elif wifi_conn is False:
                wifi_str = "STANDALONE / SETUP AP"

        primary_source, source_details = self.format_source_display(data)

        print("=" * 66)
        print("         ESP32 CONVEYOR LIVE HARDWARE MONITOR")
        print("=" * 66)
        print(f" Port:   {self.port:<20} Baud:   {self.baud}")
        print(f" Status: {status:<20} Health: WiFi={wifi_str}")
        print("-" * 66)
        print(f" Time        Sequence      Node               Temperature")
        print(f" {ts:<11} {str(seq):<13} {str(node_id):<18} {temp_str}")
        print("")
        print(f" RPM         Belt Speed    Load        Tracking/IR")
        print(f" {rpm_str:<11} {speed_str:<13} {load_str:<11} {track_str}")
        print("")
        print(f" Vibration:  {vib_str}")
        print(f" Source:     {primary_source}")
        print(f" Channels:   {source_details}")
        print("-" * 66)

        # Warning banner if sequence stopped advancing
        if not self.sequence_advancing:
            print(" >> WARNING: TELEMETRY SEQUENCE NOT ADVANCING <<")
            print("-" * 66)

        print(f" Last packet:       {elapsed_str}")
        print(f" Packets received:  {self.packets_received}")
        print(f" Valid telemetry:   {self.valid_telemetry}")
        print(f" Invalid/unparsed:  {self.invalid_unparsed}")
        print(f" Packets/sec:       {rate:.2f}")
        print("=" * 66)
        print("RAW SERIAL STREAM:")
        print(f"{self.latest_raw_line[:120]}")
        if self.last_log_line and self.last_log_line != self.latest_raw_line:
            print(f"LOG: {self.last_log_line[:120]}")
        print("=" * 66)
        print("Press Ctrl+C to stop monitor.")

    def run(self):
        if serial is None:
            print("[-] Error: 'pyserial' is not installed.")
            print("    Install it via: pip install pyserial")
            sys.exit(1)

        print(f"[*] Opening serial port {self.port} at {self.baud} baud...")
        try:
            ser = serial.Serial()
            ser.port = self.port
            ser.baudrate = self.baud
            ser.timeout = 0.5
            ser.dtr = False
            ser.rts = False
            ser.open()
            time.sleep(0.1)
            ser.dtr = False
            ser.rts = False
        except serial.SerialException as e:
            print(f"[-] Serial connection failed on {self.port}: {e}")
            print("    Check permissions: sudo chmod a+rw " + self.port)
            sys.exit(1)

        last_render = 0.0

        try:
            while True:
                now = time.time()
                raw_bytes = ser.readline()

                if raw_bytes:
                    raw_str = raw_bytes.decode("utf-8", errors="replace").strip()
                    if raw_str:
                        self.packets_received += 1
                        self.latest_raw_line = raw_str

                        msg_type, parsed = TelemetryParser.parse_line(raw_str)

                        if msg_type in ("CANONICAL_JSON", "SAMPLE_TAG") and parsed:
                            self.valid_telemetry += 1
                            self.last_packet_time = now
                            self.packet_timestamps.append(now)

                            new_seq = parsed.get("sequence")
                            if new_seq is not None:
                                if self.last_sequence is not None:
                                    if new_seq > self.last_sequence:
                                        self.sequence_advancing = True
                                        self.sequence_stuck_count = 0
                                    else:
                                        self.sequence_stuck_count += 1
                                        if self.sequence_stuck_count >= 2:
                                            self.sequence_advancing = False
                                self.last_sequence = new_seq

                            if msg_type == "CANONICAL_JSON":
                                self.latest_telemetry = parsed
                            else:  # SAMPLE_TAG
                                if self.latest_telemetry is None:
                                    self.latest_telemetry = parsed
                                else:
                                    # Merge update without stripping rich JSON keys
                                    for k, v in parsed.items():
                                        if k == "vibration" and isinstance(v, dict) and isinstance(self.latest_telemetry.get("vibration"), dict):
                                            self.latest_telemetry["vibration"].update(v)
                                        elif k != "timestamp" or "timestamp" not in self.latest_telemetry:
                                            self.latest_telemetry[k] = v

                        elif msg_type == "LOG":
                            self.last_log_line = raw_str
                        else:
                            self.invalid_unparsed += 1

                # Re-render every 200ms
                if now - last_render >= 0.2:
                    self.render_screen()
                    last_render = now

        except KeyboardInterrupt:
            print("\n[*] Monitor stopped by user.")
        finally:
            if ser.is_open:
                ser.close()


def main():
    parser = argparse.ArgumentParser(description="SIH 26008 ESP32 Conveyor Live Hardware Monitor")
    parser.add_argument("--port", "-p", help="Serial port (e.g. /dev/ttyUSB0)")
    parser.add_argument("--baud", "-b", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("--stale", type=float, default=DEFAULT_STALE_SEC, help="Seconds before marking STALE")
    parser.add_argument("--disconnect", type=float, default=DEFAULT_DISCONNECT_SEC, help="Seconds before marking DISCONNECTED")
    args = parser.parse_args()

    port = select_port(args.port)
    monitor = LiveHardwareMonitor(
        port=port,
        baud=args.baud,
        stale_sec=args.stale,
        disconnect_sec=args.disconnect,
    )
    monitor.run()


if __name__ == "__main__":
    main()
