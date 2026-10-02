# 🚀 cPanel Subdomain Deployment Guide (የ cPanel ሰብዶሜይን መጫኛ ሙሉ መመሪያ)

> **የሲስተሙ ስም:** Smart Seedling Nursery IoT Platform  
> **የአሰራር ዘዴ:** cPanel "Setup Python App" (Phusion Passenger WSGI)  
> **ስሪት:** 1.0 Production Ready  

---

## 📋 የዝግጅት ቅደም ተከተል ማጠቃለያ (Step-by-Step Overview)

1. **ደረጃ 1:** በ cPanel ላይ ሰብዶሜይን (Subdomain) መፍጠር (ለምሳሌ፡ `seedling.yourdomain.com`)
2. **ደረጃ 2:** በ cPanel ላይ ዳታቤዝ (Database) መፍጠር
3. **ደረጃ 3:** በ cPanel "Setup Python App" ውስጥ የ Python አፕሊኬሽን መክፈት
4. **ደረጃ 4:** የፕሮጀክት ፋይሎችን በ File Manager (ወይም Git) መጫን
5. **ደረጃ 5:** የ `.env` ፋይልን ማስተካከል (Subdomain URL እና Database ማገናኘት)
6. **ደረጃ 6:** በ cPanel Terminal ውስጥ Dependencies መጫን እና ዳታቤዝ ማዘጋጀት
7. **ደረጃ 7:** አፑን Restart ማድረግና በብሮውዘር መክፈት

---

## 🛠️ ደረጃ በደረጃ ዝርዝር መመሪያ

### ደረጃ 1፡ በ cPanel ላይ ሰብዶሜይን (Subdomain) መፍጠር

1. ወደ **cPanel** አካውንትዎ ይግቡ።
2. **"Domains"** $\rightarrow$ **"Domains"** (ወይም **"Subdomains"**) የሚለውን ይክፈቱ።
3. **"Create A New Domain"** የሚለውን ይጫኑ።
4. የሰብዶሜይኑን ስም ያስገቡ (ለምሳሌ፡ `seedling.yourdomain.com`)።
5. **Document Root** በሚለው ሳጥን ላይ የፎልደሩን ስም ይስጡት (ለምሳሌ፡ `public_html/seedling` ወይም `seedling.yourdomain.com`)።
6. **"Submit"** የሚለውን ይጫኑ።

---

### ደረጃ 2፡ በ cPanel ላይ ዳታቤዝ ማዘጋጀት

* **አማራጭ ሀ (PostgreSQL Database - በ cPanel)**፡
  1. cPanel ላይ **"PostgreSQL Databases"** ገጽ ይክፈቱ።
  2. አዲስ Database ይፍጠሩ (ለምሳሌ፡ `cpaneluser_seedlingdb`)።
  3. አዲስ Database User እና Password ይፍጠሩ (ለምሳሌ፡ `cpaneluser_dbuser` / `YourStrongPass123!`)።
  4. ተጠቃሚውን ከዳታቤዙ ጋር በማያያዝ **"All Privileges"** ይስጡ።

* **አማራጭ ለ (SQLite - ምንም ኮንፊገሬሽን ሳያስፈልግ)**፡
  * ምንም ዳታቤዝ መፍጠር ሳያስፈልግ እዚሁ ኮምፒውተርዎ ላይ ያለውን `db.sqlite3` በቀጥታ መጠቀም ይችላሉ!

---

### ደረጃ 3፡ "Setup Python App" ማዘጋጀት

1. cPanel ላይ **"Software"** $\rightarrow$ **"Setup Python App"** የሚለውን ይክፈቱ።
2. **"Create Application"** የሚለውን ሰማያዊ አዝራር ይጫኑ።
3. ቅጾቹን እንደሚከተለው ይሙሉ፡
   * **Python version:** `3.10`፣ `3.11`፣ ወይም `3.12` ይምረጡ።
   * **Application root:** የፕሮጀክቱ ፎልደር ስም (ለምሳሌ፡ `smart_seedling` ወይም `seedling.yourdomain.com`)።
   * **Application URL:** የፈጠሩትን ሰብዶሜይን ይምረጡ (`seedling.yourdomain.com`)።
   * **Application startup file:** `passenger_wsgi.py` ብለው ይጻፉ።
   * **Application Entry point:** `application` ብለው ይጻፉ።
4. **"Create"** የሚለውን አዝራር ይጫኑ።
5. ከላይ በኩል **`source /home/youruser/virtualenv/.../bin/activate`** የሚል ትዕዛዝ ይሰጥዎታል፤ ያንን መስመር Copy ያድርጉ።

---

### ደረጃ 4፡ የፕሮጀክቱን ፋይሎች መጫን (File Upload)

1. በኮምፒውተርዎ ላይ ያለውን የ **`smart_seedling`** ፎልደር በሙሉ ወደ **`.zip`** ፋይል ይቀይሩት (ማስታወሻ፡ `venv` ፎልደር ካለ `.zip` ውስጥ እንዳይገባ ያድርጉ)።
2. cPanel **"File Manager"** ከፍተው ወደ ፕሮጀክትዎ ፎልደር (ለምሳሌ `/home/youruser/smart_seedling`) ይግቡ።
3. የ `.zip` ፋይሉን Upload አድርገው **"Extract"** (ይፍቱት)።

---

### ደረጃ 5፡ የ `.env` ፋይል በ cPanel ላይ ማዘጋጀት

በ cPanel File Manager ውስጥ በፕሮጀክቱ ስር **`.env`** የሚል ፋይል ይክፈቱና የሚከተለውን ያስገቡ፡

```ini
# Security & Debug
SECRET_KEY=your-super-secret-production-key-here-982374829184
DEBUG=False

# Your cPanel Subdomain
ALLOWED_HOSTS=seedling.yourdomain.com,www.seedling.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://seedling.yourdomain.com,http://seedling.yourdomain.com

# Timezone
TIME_ZONE=UTC

# (አማራጭ) PostgreSQL የሚጠቀሙ ከሆነ:
DATABASE_URL=postgresql://cpaneluser_dbuser:YourStrongPass123!@127.0.0.1:5432/cpaneluser_seedlingdb
```

---

### ደረጃ 6፡ በ cPanel Terminal ውስጥ ትዕዛዞችን ማስኬድ

1. cPanel ላይ **"Terminal"** የሚለውን ክፍል ይክፈቱ።
2. በደረጃ 3 ላይ Copy ያደረጉትን የ virtualenv ማብሪያ መስመር Paste አድርገው `Enter` ይጫኑ (ለምሳሌ፡ `source /home/youruser/virtualenv/.../bin/activate`)።
3. ወደ ፕሮጀክትዎ ፎልደር ይግቡ፡
   ```bash
   cd ~/smart_seedling
   ```
4. መስፈርቶችን ይጫኑ (Install Requirements):
   ```bash
   pip install -r requirements.txt
   ```
5. ዳታቤዙን ያዘጋጁ (Run Migrations):
   ```bash
   python manage.py migrate
   ```
6. የዲዛይን ፋይሎችን ይሰብስቡ (Collect Static):
   ```bash
   python manage.py collectstatic --no-input
   ```
7. የሙከራ ዳታዎችን ለመሙላት (Seed Demo Data) ወይም አዲስ Super Admin ለመፍጠር፡
   ```bash
   python manage.py seed_demo
   # ወይም
   python manage.py createsuperuser
   ```

---

### ደረጃ 7፡ አፑን Restart ማድረግና መክፈት

1. ወደ cPanel **"Setup Python App"** ገጽ ይመለሱ።
2. በፈጠሩት አፕሊኬሽን ፊት ለፊት ያለውን **"Restart"** 🔄 አዝራር ይጫኑ።
3. አሁን በብሮውዘርዎ ወደ ሰብዶሜይንዎ ይግቡ፡
   * 👉 **`https://seedling.yourdomain.com/dashboard/`**
   * 👉 **`https://seedling.yourdomain.com/admin/`**

---

## 📡 ለ ESP32 ሃርድዌር የሚሰጥ አዲስ URL

ሲስተሙ በሰብዶሜይኑ ላይ ከተጫነ በኋላ፣ በ ESP32 C++ ኮድ ውስጥ የሰርቨሩን URL ወደ አዲሱ ሰብዶሜይን ይቀይሩታል፡

```cpp
// ESP32 Firmware Target URL:
const char* SERVER_URL = "https://seedling.yourdomain.com/api/v1/device/readings/";
const char* DEVICE_ID  = "ESP32-001";
const char* API_KEY    = "your-device-api-key";
```

---

> 🌿 **Smart Seedling Platform በ cPanel ሰብዶሜይንዎ ላይ በሙሉ አቅሙ በቀጥታ መስራት ጀመረ!**
