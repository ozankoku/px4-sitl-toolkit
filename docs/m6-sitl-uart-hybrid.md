# M6 — SITL + UART Hybrid Test

**Goal:** Verify that `sim_main.py` on the Raspberry Pi can connect to
ArduPilot SITL running in WSL2 on the Windows workstation, using the
`util_udp_relay.py` bridge to cross the WSL2 network boundary.

---

## Prerequisites

| What | Where | Notes |
|------|-------|-------|
| ArduPilot SITL + MAVProxy | WSL2 (Ubuntu 22.04) | `sim_vehicle.py` must be on PATH |
| `sim_main.py` + dependencies | Raspberry Pi | `pymavlink`, `numpy`, `matplotlib` |
| `util_udp_relay.py` | Windows host | Runs with the system Python |
| Both ESP32s powered | Bench | Bridged ESP32 connected to Pi via UART |
| Pi on the same LAN | — | Same Wi-Fi/switch as the Windows workstation |

---

## Why a relay is needed

WSL2 uses a private virtual network (`172.x.x.x`) that is not reachable
from the LAN. The Raspberry Pi can reach the Windows host (`192.168.x.x`)
but not WSL2 directly. The relay runs on the Windows host, which can reach
both sides, and cross-forwards UDP packets between them.

```
Pi (192.168.x.x)
      │  UDP:14551
      ▼
Windows host (192.168.x.x / 172.x.x.1)
  util_udp_relay.py
      │  UDP:14551
      ▼
WSL2 SITL (172.x.x.x)
```

---

## Step-by-step

### Step 1 — Find your addresses

**In PowerShell (Windows):**
```powershell
# WSL2 IP
wsl hostname -I
# example output: 172.22.144.5

# Windows LAN IP (look for the adapter connected to your router)
ipconfig | findstr "IPv4"
# example: 192.168.1.42
```

**In WSL2 bash:**
```bash
# Windows host IP as seen from WSL2 (the default gateway)
ip route | grep default | awk '{print $3}'
# example output: 172.22.144.1
```

---

### Step 2 — Start SITL in WSL2

Open a WSL2 terminal and launch SITL. The `--out` flag tells MAVProxy to
push MAVLink packets to the Windows relay:

```bash
sim_vehicle.py -v ArduCopter \
  --console --map \
  --out=udp:<WINDOWS_HOST_IP>:14551
```

Replace `<WINDOWS_HOST_IP>` with the gateway IP from Step 1
(e.g. `172.22.144.1`).

Wait until you see the MAVProxy console and the vehicle appears on the map.

---

### Step 3 — Start the relay on Windows

Open a **cmd or PowerShell** window (not WSL2) in the repo root and run:

```cmd
python simulation\util_udp_relay.py <WSL2_IP>
```

Replace `<WSL2_IP>` with the value from Step 1 (e.g. `172.22.144.5`).

If Windows Firewall prompts you, allow access on private networks.

Expected output:
```
[relay] Listening on 0.0.0.0:14551
[relay] WSL2 expected at: 172.22.144.5
[relay] Waiting for packets from both sides...
```

After a few seconds the relay will start logging forwarded packet counts
every 10 seconds once both sides connect.

---

### Step 4 — Verify UART on the Pi (optional but recommended)

Before running the full simulation, confirm the ESP32 bridge is still live:

```bash
# On the Pi — run standalone UART reader
python3 -c "
from hw_uart_reader import ESP32UARTReader
import time
r = ESP32UARTReader('/dev/ttyAMA0', 115200)
r.start()
time.sleep(5)
print(r.get_neighbours())
r.stop()
"
```

Expected: a dict containing the second ESP32's drone ID with a recent
timestamp. If empty, check power and UART wiring before proceeding.

---

### Step 5 — Run sim_main.py on the Pi

```bash
cd /path/to/skybeacon/simulation
python3 sim_main.py udpout:<WINDOWS_LAN_IP>:14551
```

Replace `<WINDOWS_LAN_IP>` with the Windows host's LAN IP (e.g. `192.168.1.42`).

**Expected sequence:**
1. `Connecting to MAVLink endpoint: udpout:192.168.1.42:14551`
2. `Heartbeat received from system 1, component 1`
3. `--- Connection Established ---`
4. Scenario loop begins — same output as the pure-SITL M5 runs

---

## Pass criteria for M6

- [ ] Relay shows non-zero `fwd pi←wsl2` and `pi→wsl2` counts within 30 s
- [ ] Pi prints `Heartbeat received` and `Connection Established`
- [ ] At least one scenario runs to completion without a MAVLink timeout
- [ ] `Stale position data` warning does **not** appear during normal flight

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Relay shows `wsl2=waiting` | SITL `--out` points to wrong host IP | Re-check `ip route` in WSL2; use the gateway address |
| Relay shows `pi=waiting` | Pi using wrong Windows LAN IP | Re-check `ipconfig` on Windows |
| `Heartbeat received` never prints | Windows Firewall blocking UDP 14551 | Add inbound rule for UDP 14551, or temporarily disable private-network firewall |
| `MAVLink 2.0 required` assertion | SITL outputting MAVLink 1 | Add `--mavversion 2` to `sim_vehicle.py` command |
| Relay exits immediately | WSL2 IP not passed as argument | `python util_udp_relay.py 172.x.x.x` |

---

## Teardown

1. `Ctrl+C` on `sim_main.py` (Pi)
2. `Ctrl+C` on `util_udp_relay.py` (Windows)
3. `Ctrl+C` on MAVProxy / SITL (WSL2)
