<div align="center">

![header](https://capsule-render.vercel.app/api?type=waving&height=300&color=gradient&text=Angler&fontAlignY=35&fontColor=ffff&desc=%20Real-Time%20Phishing%20Framework%20Designed%20For%20Authorized%20Penetration)

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-SocketIO-000000?style=for-the-badge&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-34A853?style=for-the-badge)

</div>

---

## `$ Overview`

Angler is a real-time phishing framework designed for **authorized penetration testing and security research**. It simulates a multi-step Google login flow, captures credentials live via WebSockets, and allows the operator to push custom 2FA challenge screens to the target in real time.

> **This tool is strictly for educational purposes and authorized testing only. Unauthorized use is illegal.**

---

## `$ Screenshots`

<div align="center">

Admin Panle

![Step 1](https://github.com/iNarrow12/Angler/blob/main/src/image.png)

</div>

---

## `$ Tree Overview`

```
.
├── server.py                  # Main Flask + SocketIO server
├── sessions.log               # Session event log
├── static/
│   └── google.png             # Static assets
└── templates/
    ├── admin/
    │   └── panel.html         # Real-time admin control panel
    └── user/
        ├── step1.html         # Email input page
        ├── step2.html         # Password input page
        ├── processing.html    # Verifying screen
        ├── step3a.html        # 2FA - SMS Code
        ├── step3b.html        # 2FA - Authenticator
        ├── step3c.html        # 2FA - Push Notification
        ├── step3d.html        # 2FA - Email Code
        └── step3e.html        # 2FA - Number Match
```

---

## `$ Features`

| Module | Description |
|--------|-------------|
| **Multi-step flow** | Email → Password → Processing → 2FA |
| **Real-time capture** | Credentials streamed live via WebSockets |
| **2FA bypass** | SMS, Authenticator, Push, Email, Number Match |
| **Admin panel** | Live credential display, device detection, session timer |
| **Copy buttons** | One-click copy for captured credentials |
| **Sound alerts** | Audio notification on email, password, and code capture |
| **Device detection** | Auto-detects OS, device type, and browser from User-Agent |
| **Session logging** | All events logged to `sessions.log` |

---

## `$ Installation`

```bash
git clone https://github.com/iNarrow12/Angler.git
cd Angler
pip install flask flask-socketio
```

---

## `$ Usage`

```bash
# Default port 5800
python server.py

# Custom port
python server.py --port 8080
```

| URL | Description |
|-----|-------------|
| `http://localhost:5800/` | Victim-facing phishing page |
| `http://localhost:5800/admin` | Admin control panel |

Admin credentials: `admin / admin`

---

## `$ Exposing Publicly`

```bash
cloudflared tunnel --url http://localhost:5800
```

---

## `$ Attack Flow`

```
Victim visits URL
      |
      v
Step 1 — Email input
      |
      v
Step 2 — Password input          <- Captured, sent to admin
      |
      v
Processing (Verifying...)
      |
      v
Admin selects 2FA variant
      |
      v
Step 3 — 2FA code input          <- Captured, sent to admin
```

---

## `$ Admin Panel`

| Feature | Description |
|---------|-------------|
| Live credentials | Email and password displayed in real time |
| Session info | IP address, device type, OS, browser tags |
| 2FA push | Select which 2FA screen to push to victim |
| Number Match | Manually enter number to display to victim |
| Event log | Color-coded log of all session events |
| Session timer | Tracks elapsed time since first capture |
| Copy buttons | One-click copy for email and password |
| Clear | Reset all session data and timer |

---

## `$ Logging`

All events are logged to `sessions.log` in JSON format:

```json
{"timestamp": "2026-03-10T12:00:00Z", "event": "submit_step1", "email": "user@gmail.com", "ip": "x.x.x.x"}
{"timestamp": "2026-03-10T12:00:10Z", "event": "submit_step2", "password": "...", "ip": "x.x.x.x"}
```

---

## `$ License`

MIT — For authorized security research and educational use only.

<div align="center">

![footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=100&section=footer)

</div>
