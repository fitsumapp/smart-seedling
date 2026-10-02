# 🌱 Smart Seedling Nursery IoT Monitoring & Control System

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![ESP32](https://img.shields.io/badge/ESP32-IoT-E7352C?style=for-the-badge&logo=espressif&logoColor=white)](https://www.espressif.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Tailwind / Unfold](https://img.shields.io/badge/Unfold-Admin-0c3b20?style=for-the-badge)](https://github.com/unfoldadmin/django-unfold)

---

## 📌 ፕሮጀክት አጠቃላይ መረጃ (Project Overview)

**Smart Seedling** ለችግኝ ማፍያ ማዕከላት (Nursery Facilities & Greenhouses) የተሰራ የተሟላ የ **IoT እና የድር መተግበሪያ (Web Application)** ነው።  
ከ **ESP32 Microcontroller** የሚመጡ የአፈር ሙቀት እና እርጥበት መረጃዎችን በየሰከንዱ በመቀበል አውቶማቲክ የመስኖ ፓምፕ ይቆጣጠራል፣ የቀጥታ የትንታኔ ዳሽቦርድ ያሳያል፣ እና ለእያንዳንዱ ችግኝ የ **QR Code ዲጂታል ፓስፖርት** ያትማል።

---

## 📖 የሰነዶች ዝርዝር (Documentation Links)

1. 📘 **[የተሟላ የተጠቃሚ መመሪያ (User Manual)](docs/USER_MANUAL.md)** — እያንዳንዱ ክፍል ምን እንደሚሰራና እንዴት እንደምንጠቀምበት በአማርኛ የተዘጋጀ የተሟላ ማብራሪያ።
2. 📟 **[የ ESP32 ሃርድዌር አሰራርና ኮድ (ESP32 Integration Guide)](docs/ESP32_INTEGRATION.md)** — የሽቦ አሰካክ (Wiring Diagram) እና የተሟላ የ Arduino C++ ኮድ።
3. 🚀 **[የክላውድ ዲፕሎይመንት መመሪያ (Cloud Deployment Guide)](docs/DEPLOYMENT.md)** — በ Render.com እና PostgreSQL ላይ በነፃ የመጫኛ መመሪያ።
4. 📡 **[የ REST API ሰነድ (REST API Documentation)](docs/API.md)** — ለ ESP32 እና ውጫዊ ሲስተሞች የተዘጋጀ የ API ዝርዝር።
5. 🌐 **[የ cPanel ሰብዶሜይን መጫኛ መመሪያ (cPanel Subdomain Deployment)](docs/CPANEL_DEPLOYMENT.md)** — በ cPanel ሰብዶሜይን ላይ ደረጃ በደረጃ የመጫኛ መመሪያ።


---

## ⚡ ፈጣን ማስጀመሪያ (Quick Start)

### 1. መስፈርቶችን መጫን (Install Requirements):
```bash
pip install -r requirements.txt
```

### 2. ዳታቤዝ ማዘጋጀት እና የሙከራ ዳታ መሙላት (Migrate & Seed Demo):
```bash
python manage.py migrate
python manage.py seed_demo
```

### 3. ሰርቨሩን ማስጀመር (Run Local Dev Server):
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 🔑 የመግቢያ መለያዎች (Default Credentials)

* **Super Admin:** `admin` / `admin1234` $\rightarrow$ [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
* **Nursery Administrator:** `nursery_admin` / `manager1234` $\rightarrow$ [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
* **Live Interactive Dashboard:** 👉 [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
* **Public QR Plant Passport:** 👉 [http://127.0.0.1:8000/plant/46f5beda479343e09d84abdd6f537c1a/](http://127.0.0.1:8000/plant/46f5beda479343e09d84abdd6f537c1a/)
