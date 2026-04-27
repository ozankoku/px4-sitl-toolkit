#!/usr/bin/env python
"""util_udp_relay.py — UDP relay for WSL2 ↔ Pi MAVLink bridging.

Run this on the Windows HOST (not inside WSL2) so it can reach both:
  - WSL2 (172.x.x.x virtual network, unreachable from LAN)
  - Raspberry Pi (192.168.x.x LAN)

Usage
-----
1. Find your WSL2 IP (run in PowerShell):
       wsl hostname -I

2. Edit WSL2_IP below, or pass it as a command-line argument:
       python util_udp_relay.py 172.22.144.5

3. Start SITL in WSL2 with MAVProxy outputting to the Windows host:
       sim_vehicle.py -v ArduCopter --out=udp:<WINDOWS_HOST_IP>:14551
   WINDOWS_HOST_IP from inside WSL2:
       ip route | grep default | awk '{print $3}'

4. On the Pi, set sim_main.py connection string to:
       udpout:<WINDOWS_LAN_IP>:14551

5. Run this script on Windows. Allow it through Windows Firewall if prompted.

How it works
------------
Both SITL (in WSL2) and sim_main.py (on Pi) send UDP to Windows:14551.
The relay distinguishes them by source IP prefix and cross-forwards:
  WSL2 packet  → forwarded to Pi's last known return address
  Pi packet    → forwarded to WSL2's last known return address

PORT = 14551 (matches MAVLINK_CONNECTION_SITL in hw_mavlink.py)
"""

import socket
import threading
import sys
import time

# ---------------------------------------------------------------------------
# Configuration — edit WSL2_IP or pass it on the command line
# ---------------------------------------------------------------------------
WSL2_IP  = "172.x.x.x"   # replace with output of: wsl hostname -I
PORT     = 14551
# ---------------------------------------------------------------------------


def _wsl2_ip_prefix(ip: str) -> bool:
    """Return True if ip looks like a WSL2 address (172.x or 127.x)."""
    return ip.startswith("172.") or ip.startswith("127.")


def run_relay(wsl2_ip: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(1.0)

    pi_addr   = None   # (ip, port) of the Pi's sim_main.py socket
    wsl2_addr = None   # (ip, port) of MAVProxy's output socket in WSL2

    fwd_to_pi   = 0
    fwd_to_wsl2 = 0
    last_log    = time.time()

    print(f"[relay] Listening on 0.0.0.0:{port}")
    print(f"[relay] WSL2 expected at: {wsl2_ip}")
    print(f"[relay] Waiting for packets from both sides...")

    while True:
        try:
            data, addr = sock.recvfrom(65536)
        except socket.timeout:
            # Periodic status log every 10 s
            if time.time() - last_log > 10:
                print(
                    f"[relay] pi={'connected' if pi_addr else 'waiting'} | "
                    f"wsl2={'connected' if wsl2_addr else 'waiting'} | "
                    f"fwd pi←wsl2={fwd_to_pi} pi→wsl2={fwd_to_wsl2}"
                )
                last_log = time.time()
            continue

        src_ip = addr[0]

        if _wsl2_ip_prefix(src_ip):
            # Packet from WSL2/SITL — record sender, forward to Pi
            wsl2_addr = addr
            if pi_addr:
                sock.sendto(data, pi_addr)
                fwd_to_pi += 1
        else:
            # Packet from Pi — record sender, forward to WSL2
            pi_addr = addr
            if wsl2_addr:
                sock.sendto(data, wsl2_addr)
                fwd_to_wsl2 += 1
            else:
                # Pi sent first; nudge WSL2 so MAVProxy learns our port
                sock.sendto(data, (wsl2_ip, port))
                fwd_to_wsl2 += 1


def main() -> None:
    wsl2_ip = sys.argv[1] if len(sys.argv) > 1 else WSL2_IP
    if "x" in wsl2_ip:
        print("ERROR: WSL2_IP is not set.")
        print("  Edit WSL2_IP in this script, or pass it as an argument:")
        print("    python util_udp_relay.py 172.22.144.5")
        print("  Get your WSL2 IP with:  wsl hostname -I")
        sys.exit(1)

    t = threading.Thread(target=run_relay, args=(wsl2_ip, PORT), daemon=True)
    t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[relay] Stopped.")


if __name__ == "__main__":
    main()
