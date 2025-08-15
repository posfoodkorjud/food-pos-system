# Food POS System - Deployment Guide

คู่มือการ Deploy ระบบ POS ร้านอาหารขึ้นสู่อินเตอร์เน็ต

## ตัวเลือกการ Deploy

### 1. Railway (แนะนำ - ง่ายและรวดเร็ว)

#### ขั้นตอนการ Deploy

1. **สร้างบัญชี Railway**
   - ไปที่ https://railway.app และสมัครบัญชีด้วย GitHub

2. **Deploy จาก GitHub**
   - กด "New Project" → "Deploy from GitHub repo"
   - เลือก repository ของคุณ
   - Railway จะ auto-detect และ deploy อัตโนมัติ

3. **เพิ่ม PostgreSQL Database**
   - ใน Railway dashboard กด "+ New"
   - เลือก "Database" → "PostgreSQL"
   - Copy DATABASE_URL ที่ได้

4. **ตั้งค่า Environment Variables**
   - ไปที่ Variables tab ใน Railway
   - เพิ่มตัวแปรต่อไปนี้:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://... (จาก step 3)
   GOOGLE_SHEET_ID=your-sheet-id
   PROMPTPAY_VALUE=your-promptpay-number
   DOMAIN_URL=https://your-app.railway.app
   ```

5. **Deploy**
   - Railway จะ deploy อัตโนมัติเมื่อมีการ push ไปยัง GitHub

### 2. Vercel (สำหรับ Serverless)

#### ขั้นตอนการ Deploy

1. **สร้างบัญชี Vercel**
   - ไปที่ https://vercel.com และสมัครบัญชีด้วย GitHub

2. **Deploy จาก GitHub**
   - กด "New Project" และเลือก repository
   - Vercel จะใช้ vercel.json ที่เตรียมไว้

3. **ตั้งค่า Environment Variables**
   - ใน Vercel dashboard ไปที่ Settings → Environment Variables
   - เพิ่มตัวแปรเดียวกับ Railway

### 3. Heroku (แนะนำสำหรับผู้เริ่มต้น)

#### ขั้นตอนการ Deploy บน Heroku:

1. **สร้างบัญชี Heroku**
   - ไปที่ https://heroku.com และสมัครบัญชี
   - ติดตั้ง Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

2. **เตรียมโปรเจค**
   ```bash
   cd A_FOOD_POS/FOOD_POS
   git init
   git add .
   git commit -m "Initial commit"
   ```

3. **สร้าง Heroku App**
   ```bash
   heroku create your-restaurant-pos
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **ตั้งค่า Environment Variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DOMAIN_URL=https://your-restaurant-pos.herokuapp.com
   heroku config:set PROMPTPAY_VALUE=your-promptpay-number
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### 4. DigitalOcean App Platform

1. ไปที่ https://cloud.digitalocean.com/apps
2. สร้าง App ใหม่จาก GitHub repository
3. ตั้งค่า Environment Variables
4. Deploy

## การตั้งค่า Database สำหรับ Production

### PostgreSQL (แนะนำ)

1. **สร้างไฟล์ database_postgres.py**
   ```python
   import os
   import psycopg2
   from urllib.parse import urlparse
   
   def get_db_connection():
       database_url = os.environ.get('DATABASE_URL')
       if database_url:
           # PostgreSQL for production
           url = urlparse(database_url)
           conn = psycopg2.connect(
               database=url.path[1:],
               user=url.username,
               password=url.password,
               host=url.hostname,
               port=url.port
           )
       else:
           # SQLite for development
           import sqlite3
           conn = sqlite3.connect('pos_database.db')
       return conn
   ```

2. **แก้ไข requirements.txt**
   ```
   psycopg2-binary==2.9.7
   ```

## Environment Variables ที่จำเป็น

```bash
# Production Settings
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Domain Configuration
DOMAIN_URL=https://your-domain.com
QR_PATH=/order?table=

# PromptPay (ถ้าใช้)
PROMPTPAY_TYPE=phone
PROMPTPAY_VALUE=0812345678

# Google Sheets (ถ้าใช้)
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

## การตั้งค่า Domain และ SSL

### Custom Domain
1. ซื้อ domain จาก provider (เช่น Namecheap, GoDaddy)
2. ตั้งค่า DNS ให้ชี้ไปยัง hosting platform
3. เพิ่ม custom domain ใน platform dashboard
4. SSL จะถูกตั้งค่าอัตโนมัติ

## การทดสอบหลัง Deploy

1. **ทดสอบ Admin Panel**
   - เข้าไปที่ `https://your-domain.com/admin`
   - ทดสอบการเพิ่ม/แก้ไขเมนู
   - ทดสอบการจัดการโต๊ะ

2. **ทดสอบ Customer App**
   - เข้าไปที่ `https://your-domain.com/`
   - ทดสอบการสั่งอาหาร
   - ทดสอบการชำระเงิน

3. **ทดสอบ QR Code**
   - สร้าง QR Code สำหรับโต๊ะ
   - สแกน QR Code ด้วยมือถือ
   - ทดสอบการสั่งอาหารผ่าน QR

## การ Backup และ Restore

### Database Backup
```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Google Sheets Backup
- ระบบจะ sync ข้อมูลไปยัง Google Sheets อัตโนมัติ
- สามารถ export เป็น Excel ได้จาก Google Sheets

## การ Monitor และ Maintenance

1. **Logs Monitoring**
   ```bash
   heroku logs --tail  # สำหรับ Heroku
   ```

2. **Performance Monitoring**
   - ใช้ built-in monitoring ของ platform
   - ตั้งค่า alerts สำหรับ downtime

3. **Regular Updates**
   - อัพเดท dependencies เป็นประจำ
   - ทดสอบระบบหลังอัพเดท

## ปัญหาที่อาจพบและวิธีแก้ไข

### 1. Database Connection Error
- ตรวจสอบ DATABASE_URL
- ตรวจสอบ firewall settings

### 2. Static Files ไม่โหลด
- ตรวจสอบ static file configuration
- ใช้ CDN สำหรับ static files

### 3. Session ไม่ทำงาน
- ตรวจสอบ SECRET_KEY
- ตรวจสอบ cookie settings

### 4. Google Sheets ไม่ sync
- ตรวจสอบ credentials.json
- ตรวจสอบ API permissions

## การรักษาความปลอดภัย

1. **HTTPS Only**
   - บังคับใช้ HTTPS สำหรับทุก request
   - ตั้งค่า HSTS headers

2. **Environment Variables**
   - ไม่เก็บ secrets ใน code
   - ใช้ environment variables สำหรับ sensitive data

3. **Database Security**
   - ใช้ strong passwords
   - จำกัด database access
   - Regular backups

4. **Regular Updates**
   - อัพเดท dependencies เป็นประจำ
   - Monitor security vulnerabilities

---

**หมายเหตุ:** ก่อน deploy ให้ทดสอบระบบในเครื่องให้ครบถ้วนก่อน และเตรียม backup ข้อมูลสำคัญไว้เสมอ