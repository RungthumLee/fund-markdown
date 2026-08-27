# 📊 Fund Knowledge Base — คลังความรู้กองทุนรวมไทย

ฐานความรู้กองทุนรวมไทยแบบ Obsidian vault สร้างจาก **SEC Open Data API v2**
พร้อมคู่มือ API ฉบับภาษาไทยครบทั้ง 21 endpoints

**ขอบเขต:** กองทุนที่ยัง `Registered` · **ไม่รวม** Term Fund · **ไม่รวม** PVD

---

## เริ่มต้นอย่างไร

| อยากทำอะไร | ไปที่ |
|---|---|
| อ่านข้อมูลกองทุน | เปิด `vault/` ด้วย Obsidian → เริ่มที่ `Indexes/00-home.md` |
| เรียนรู้การใช้ API | [docs/guides/quickstart.md](docs/guides/quickstart.md) |
| ดูรายละเอียด endpoint | [docs/api-reference/00-index.md](docs/api-reference/00-index.md) |
| ดูสถานะงาน/ปัญหา | [docs/project/tasks.md](docs/project/tasks.md) · [docs/project/issues.md](docs/project/issues.md) |
| รันใหม่ทั้งหมด | `python run_all.py` |

---

## โครงสร้างโปรเจกต์

```
Fund-knowledge/
├── .env.local              🔒 API keys (ไม่ commit)
├── run_all.py              รัน pipeline ทั้งหมด
│
├── docs/                   📚 เอกสาร
│   ├── api-reference/      คู่มือ 21 endpoints (auto-generated)
│   ├── guides/             วิธีใช้งาน + แนวคิด + data dictionary
│   └── project/            tasks · issues · decisions · outstanding · roadmap
│
├── scripts/                🐍 โค้ด
│   ├── sec_client.py       API client (retry, key failover, pagination)
│   ├── harvest.py          ดึงข้อมูลดิบ 21 dataset
│   ├── transform.py        รวม/กรอง/ทำความสะอาด
│   ├── fetch_factsheets.py ดาวน์โหลด PDF
│   ├── parse_factsheets.py แกะข้อความจาก PDF
│   ├── gen_vault.py        สร้างโน้ต Obsidian
│   ├── gen_api_docs.py     สร้างคู่มือ API
│   ├── gen_data_dictionary.py
│   └── validate_vault.py   ตรวจลิงก์เสีย/orphan
│
├── data/
│   ├── raw/                *.jsonl จาก API (ไม่ commit, ~1 GB)
│   ├── processed/          funds.json · amcs.json · excluded.json · stats.json
│   └── factsheets/         *.pdf + _manifest.json
│
├── vault/                  🧠 Obsidian vault
│   ├── Indexes/            00-home (MOC) + ดัชนีจัดกลุ่ม
│   ├── Funds/              1 โน้ตต่อกองทุน
│   ├── AMCs/               1 โน้ตต่อ บลจ.
│   ├── Concepts/           แนวคิดพื้นฐาน
│   └── Factsheets/         ข้อความจาก PDF
│
├── _spec/                  สำเนา API catalog
└── logs/                   log ของทุกสคริปต์
```

---

## รัน pipeline

```bash
python run_all.py                    # ครบทุกขั้น (ข้ามที่ทำแล้ว)
python run_all.py --smoke            # ทดสอบขนาดเล็ก
python run_all.py --from vault       # เริ่มจากขั้นที่กำหนด
python run_all.py --skip factsheets
```

ทีละขั้น:

```bash
python scripts/harvest.py            # 1. ดึงข้อมูลดิบ
python scripts/transform.py          # 2. รวม/กรอง
python scripts/fetch_factsheets.py   # 3. โหลด PDF
python scripts/parse_factsheets.py   # 4. แกะข้อความ
python scripts/gen_vault.py          # 5. สร้างโน้ต
python scripts/validate_vault.py     # 6. ตรวจสอบ
```

ทุกขั้น **resume ได้** — รันซ้ำจะข้ามงานที่ทำเสร็จแล้ว

---

## เปิด vault ใน Obsidian

1. Obsidian → **Open folder as vault** → เลือกโฟลเดอร์ `vault/`
2. เปิด `Indexes/00-home.md`
3. แนะนำให้ติดตั้งปลั๊กอิน **Dataview** — ทุกโน้ตมี frontmatter พร้อมใช้งาน

> เปิดที่โฟลเดอร์ `vault/` เท่านั้น ไม่ต้องเปิดทั้งโปรเจกต์
> (ลิงก์ข้ามไป `docs/` จะเป็นลิงก์ค้างใน Obsidian — เปิดใน editor แทน)

---

## ต้องใช้อะไรบ้าง

- Python 3.10+
- `requests`, `PyMuPDF`
- SEC API subscription key ใน `.env.local`:
  ```ini
  SEC_SUBSCRIPTION_KEY=...
  SEC_secondary_key=...
  ```

---

## แหล่งข้อมูล

- SEC Open Data Developer Portal — https://secopendata.sec.or.th/sec-open-apis
- API host — `https://api.sec.or.th`

> ข้อมูลทั้งหมดเป็นข้อมูลสาธารณะที่สำนักงาน ก.ล.ต. เผยแพร่
> คลังนี้เป็น**ข้อมูลอ้างอิงเพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน**
