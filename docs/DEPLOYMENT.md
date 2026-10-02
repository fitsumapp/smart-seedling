# Production Cloud Deployment Guide (Render & PostgreSQL)

This guide walks you through deploying the **Smart Seedling IoT Platform** to the cloud so that your ESP32 device can send telemetry from any Wi-Fi network globally over secure HTTPS.

---

## Architecture Flow

```
[ ESP32 Hardware anywhere in the world ]
               │ (Wi-Fi / 4G Hotspot)
               ▼ HTTPS POST /api/v1/device/readings/
[ Cloud Web Service (Render / Gunicorn / WhiteNoise) ]
               │
               ▼
[ Managed PostgreSQL Database ]
               ▲
               │
[ Real-Time Web Dashboard (Desktop & Mobile) ]
```

---

## Step 1: Push Code to GitHub

1. Initialize Git repository and commit your files:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Smart Seedling production platform"
   ```

2. Create a new repository on [GitHub](https://github.com/new) (e.g. `smart_seedling`).

3. Push code to GitHub:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/smart_seedling.git
   git push -u origin main
   ```

---

## Step 2: Deploy to Render.com (Free & Fast)

1. Create a free account on [Render.com](https://render.com/).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect your GitHub repository `smart_seedling`.
4. Render will automatically detect `render.yaml` and provision:
   * **Web Service**: Running Django with Gunicorn and WhiteNoise static serving.
   * **PostgreSQL Database**: Free managed database.
5. Click **Apply**. Render will automatically run `./build.sh` (installs requirements, collects static files, applies migrations, and seeds the admin user).

---

## Step 3: Get Your Live HTTPS Public URL

Once the build finishes (usually 2 minutes), Render will give you a public URL like:
👉 `https://smart-seedling-xxxx.onrender.com`

* **Live Dashboard**: `https://smart-seedling-xxxx.onrender.com/dashboard/`
* **Django Unfold Admin**: `https://smart-seedling-xxxx.onrender.com/admin/` (Login: `admin` / `admin1234`)

---

## Step 4: Update ESP32 Firmware URL

In your Arduino C++ code, change `SERVER_URL` from the local IP to the public HTTPS cloud URL:

```cpp
const char* SERVER_URL = "https://smart-seedling-xxxx.onrender.com/api/v1/device/readings/";
```

> **Note on ESP32 HTTPS**:
> In Arduino ESP32, when using `https://`, you can use `WiFiClientSecure` or set `http.begin(client, SERVER_URL)` with `client.setInsecure();` so it sends encrypted telemetry securely over port 443 without needing custom CA certificate bundles.

Flash the ESP32 with the new URL, and your Smart Seedling nursery system is fully operational in production!
