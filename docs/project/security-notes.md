---
title: Security Notes
tags: [project, security]
---

# 🔒 Security Notes

[[tasks|Tasks]] · [[../guides/authentication|Authentication]]

---

## ความลับในโปรเจกต์นี้

| ไฟล์ | มีอะไร | สถานะ |
|---|---|---|
| `.env.local` | SEC API keys, DB credentials, Ollama config | อยู่ใน `.gitignore` ✅ |

## หลักที่ยึดในทุกสคริปต์

1. **อ่าน key จาก `.env.local` เท่านั้น** — ไม่ hardcode ที่ไหนเลย
2. **ไม่เขียน key ลง output** — ทั้ง markdown, JSON, log
   `scripts/sec_client.py` ส่ง key ผ่าน header เท่านั้น ไม่ผ่าน query string
   (query string จะติดใน log ของ proxy)
3. **ไม่ log URL เต็มพร้อม params ที่มี key** — logger บันทึกแค่ path
4. **`data/raw/` ไม่ commit** — เป็นข้อมูลสาธารณะแต่ไฟล์ใหญ่มาก (หลาย GB)

## ตรวจสอบก่อน commit

```bash
# ยืนยันว่า .env.local ไม่หลุดเข้า git
git check-ignore -v .env.local

# ค้นหา key ที่อาจหลุดใน output
grep -rIl --exclude-dir=.git -E "[0-9a-f]{32}" docs/ vault/ || echo "clean"
```

## ข้อมูลที่เก็บ

ข้อมูลทั้งหมดในคลังนี้เป็น **ข้อมูลสาธารณะ** ที่ ก.ล.ต. เผยแพร่ผ่าน Open Data API
ไม่มีข้อมูลส่วนบุคคลหรือข้อมูลที่ไม่เปิดเผย

> [!NOTE]
> `.env.local` มี `DB_PASSWORD` ของฐานข้อมูลอื่นอยู่ด้วย
> โปรเจกต์นี้**ไม่ได้ใช้**ตัวแปรเหล่านั้นเลย — ใช้เฉพาะ `SEC_SUBSCRIPTION_KEY`
> และ `SEC_secondary_key`
