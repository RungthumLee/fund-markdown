---
title: Master Funds
tags: [guide, master-fund, feeder, external-data]
---

# 🌐 กองทุนหลัก (Master Funds) — วิธีเก็บข้อมูลจากแหล่งภายนอก

**ที่เกี่ยวข้อง:** [[holdings-data|Holdings Data]] · [[factsheet-extraction|Factsheet Extraction]] · [[../../vault/Concepts/Feeder Fund|Feeder Fund]] · [[../../vault/Indexes/master-funds|ดัชนีกองทุนหลัก]]

---

## ปัญหาที่แก้

กองทุนไทยที่เป็น [[../../vault/Concepts/Feeder Fund|feeder fund]] เอาเงินเกือบทั้งหมด
ไปลงในกองทุนหลักต่างประเทศกองเดียว แต่ข้อมูลจาก ก.ล.ต. **หยุดที่ชายแดน** —
บอกแค่ชื่อกองหลัก ไม่บอกว่ากองหลักคิดค่าธรรมเนียมเท่าไร ใหญ่แค่ไหน ถือหุ้นอะไรจริง ๆ

พอร์ตของ feeder จาก API จึงหน้าตาแบบนี้ ซึ่งถูกต้องแต่ไร้ประโยชน์:

```
JPM US Growth I (acc) — 101.06% ของ NAV
```

---

## กุญแจสำคัญ: ใช้ ISIN ไม่ใช่ชื่อ

ชื่อกองหลักในข้อมูล ก.ล.ต. **สะกดไม่เหมือนกัน**ระหว่าง บลจ. บางที่ใส่คำว่า
"กองทุน" นำหน้า บางที่ใส่ share class บางที่ไม่ใส่ ค้นด้วยชื่อจึงพลาดเยอะ

แต่ **`out_portfolio` มี ISIN ของกองหลักอยู่แล้ว** — แถวที่ feeder ถือเกิน 50% ของ NAV
และมี `assetliab_id` อยู่ในกลุ่มหน่วยลงทุน (108, 109, 117–121, 130, 139)

```
K-CHANGE  →  GB00BYVGKV59  →  Baillie Gifford Positive Change Fund
K-INDIA   →  LU0119216801  →  Goldman Sachs India Equity Portfolio
```

`scripts/resolve_masters.py` ทำขั้นตอนนี้ ผลลัพธ์:

| | |
|---|---|
| กองไทยที่เป็น feeder | **999** |
| มี ISIN ของกองหลักชี้ชัด | **773** |
| มีแต่ชื่อ (ไม่มี ISIN) | 223 |
| **กองหลักที่ไม่ซ้ำกัน** | **618** |
| กองหลักที่มีกองไทยลงทุนมากกว่า 1 กอง | 195 |

---

## สองแหล่งข้อมูล — เสริมกัน ไม่ใช่ซ้ำกัน

> [!IMPORTANT]
> ความเข้าใจผิดที่พบบ่อยคือ "yfinance ใช้ได้แค่ ETF"
> **ไม่จริง** — ทดสอบแล้ว yfinance ดึง UCITS SICAV ลักเซมเบิร์กได้
> (`LU0248059726` → JPM US Growth, `quoteType = MUTUALFUND`) พร้อม sector
> weightings, top holdings, asset classes
>
> **แต่** ข้อมูลบางตัวขาดจริงสำหรับ non-ETF ซึ่ง FT มาเติมพอดี

| ข้อมูล | Yahoo (ETF) | Yahoo (mutual fund) | FT.com |
|---|---|---|---|
| ชื่อ / สกุลเงิน / ราคา | ✅ | ✅ | ✅ |
| Sector weightings | ✅ | ✅ | ❌ |
| Top holdings | ✅ | ✅ | ❌ |
| Asset class split | ✅ | ✅ | ❌ |
| ผลตอบแทน YTD / 3y / 5y | ✅ | ⚠️ เฉพาะ YTD | ⚠️ 1y |
| **ค่าธรรมเนียม (OCF/TER)** | ✅ | ❌ **คืน 0.0** | ✅ |
| **ขนาดกองทุน (AUM)** | ✅ | ❌ | ✅ |
| Morningstar category | ⚠️ | ❌ | ✅ |
| Domicile / โครงสร้าง (SICAV) | ❌ | ❌ | ✅ |
| ชื่อผู้จัดการกองทุน | ❌ | ❌ | ✅ |

> [!WARNING]
> Yahoo คืน `annualReportExpenseRatio = 0.0` สำหรับ SICAV ส่วนใหญ่
> ซึ่งหมายถึง **"ไม่มีข้อมูล"** ไม่ใช่ "ไม่คิดค่าธรรมเนียม"
> `fetch_masters.py` จึง **ทิ้งค่า 0 ทิ้ง** ไม่ให้โน้ตไปบอกว่ากองนี้ฟรี

ตัวอย่างจริง — JPM US Growth (`LU0248059726`):

```
Yahoo : expense ratio = 0.0        ← ผิด (ไม่มีข้อมูล)
FT    : Ongoing charge = 0.77%     ← ถูก
FT    : Fund size = 4.60bn · Domicile = Luxembourg · SICAV
FT    : Manager = Giri K Devulapally (เริ่ม 20 Dec 2010)
```

---

## FT.com — ข้อสังเกตเชิงเทคนิค

- URL: `https://markets.ft.com/data/funds/tearsheet/summary?s={ISIN}:{CUR}`
  (ไม่ใส่สกุลเงินก็ได้)
- **WebFetch ของ Claude โดนบล็อก** แต่ `curl` / `requests` เข้าได้ปกติ
- หน้าเว็บ render เป็นลำดับ label/value เมื่อลอก tag ออก จึง parse ด้วยการ
  ไล่บรรทัด ไม่ใช่ DOM (`scripts/ft_scraper.py`)
- FT ส่ง UTF-8 แต่ไม่ประกาศ encoding ต้องบังคับ `r.encoding = "utf-8"`
  ไม่งั้น `£` กลายเป็น `Â£`
- **ขนาดกองทุนที่ FT รายงานเป็น GBP เสมอ** แม้จะขอหน้า USD — เก็บค่าดิบไว้ทั้งสตริง
- FT ครอบคลุม UCITS (LU / IE / GB) ดี แต่ **ไม่มี** ETF ฮ่องกง/สหรัฐ
  ซึ่ง Yahoo ครอบคลุมเต็มอยู่แล้ว

---

## ขั้นตอน

```bash
python scripts/resolve_masters.py    # หา ISIN กองหลัก -> master_funds.json
python scripts/fetch_masters.py      # ดึง Yahoo + FT -> data/masters/*.json
python scripts/gen_master_notes.py   # สร้าง vault/MasterFunds/*.md
python scripts/gen_vault.py          # ใส่ลิงก์กองหลักลงในโน้ตกองไทย
```

`fetch_masters.py` cache ต่อกอง จึง **resume ได้** — รันซ้ำจะข้ามที่ดึงแล้ว
ใช้ `--force` เพื่อดึงใหม่ · `--limit N` เพื่อทดสอบ

---

## สิ่งที่ได้ในโน้ตกองหลัก

`vault/MasterFunds/<ชื่อกอง>.md` แต่ละไฟล์มี:

1. **ข้อมูลกองทุน** — ประเภท, โครงสร้าง (SICAV/OEIC/ETF), domicile, หมวด
   Morningstar, บริษัทจัดการ, ผู้จัดการกองทุน, วันจัดตั้ง
2. **ขนาดและค่าธรรมเนียม** — AUM และ **OCF/TER ที่เชื่อถือได้**
3. **ผลการดำเนินงาน** — YTD / 1y / 3y / 5y / beta / Morningstar rating
4. **สัดส่วนประเภทสินทรัพย์** และ **กลุ่มอุตสาหกรรม**
5. **หลักทรัพย์ที่ถือมากที่สุด** — look-through ที่แท้จริง
6. **กองทุนไทยที่ลงทุนในกองนี้** — พร้อม backlink สองทาง

---

## ประโยชน์ที่ได้ทันที

> [!IMPORTANT]
> **ค่าธรรมเนียม 2 ชั้นที่มองไม่เห็น**
> ผู้ลงทุนไทยจ่ายค่าธรรมเนียมกองไทย **บวกกับ** OCF ของกองหลัก
> TER ที่รายงานในหนังสือชี้ชวนไทยมักไม่รวมชั้นที่สอง
> ตอนนี้เห็นทั้งสองชั้นในที่เดียว

> [!IMPORTANT]
> **การกระจายความเสี่ยงลวงตา**
> กองหลักหนึ่งกองมักมีกองไทยหลายกองป้อนเข้าไป — ตัวอย่างจริง:
>
> | กองทุนหลัก | กองไทยที่ลงทุน |
> |---|---|
> | SPDR® Gold Trust | **28** |
> | PIMCO GIS Income Fund | **16** |
> | iShares Core S&P 500 ETF | **13** |
> | Hang Seng China Enterprises ETF | **12** |
>
> ถือกองไทย 3 กองที่ feed เข้ากองหลักเดียวกัน = ถือสินทรัพย์เดิมซ้ำ 3 รอบ
> ไม่ได้กระจายความเสี่ยงเลย โน้ตกองหลักจะขึ้นคำเตือนนี้อัตโนมัติ

---

## ข้อจำกัด

> [!WARNING]
> - **ตัวเลขคนละวันอ้างอิงและคนละสกุลเงิน** กับ NAV ของกองไทย
>   ห้ามเอามาคำนวณต่อโดยไม่ปรับฐาน
> - กอง **private / institutional** (เช่น Ares Core Infrastructure,
>   Apollo Debt Solutions BDC) ไม่มีทั้ง Yahoo และ FT — โน้ตจะติด
>   tag `#no-external-data` และมีเฉพาะข้อมูลฝั่งไทย
> - กองที่ไม่มี ISIN (223 กอง) ใช้การค้นด้วยชื่อผ่าน Yahoo search
>   ซึ่งแม่นยำน้อยกว่า — ตรวจชื่อในโน้ตก่อนใช้อ้างอิง
> - ข้อมูลกองหลักเป็น **ระดับกองหลัก** ไม่ใช่ share class ที่กองไทยถือจริง
>   ค่าธรรมเนียมของ share class อื่นอาจต่างกัน

---

## ที่ยังทำได้อีก

การเข้าเว็บ บลจ. ของกองหลักโดยตรงแล้วโหลด factsheet/KIID มาอ่าน
จะได้ข้อมูลครบและเป็นทางการที่สุด — แต่ต้องเขียน adapter แยกต่อ บลจ.
(BlackRock, JPMorgan, PIMCO, Fidelity ฯลฯ มีโครงสร้างเว็บคนละแบบ)
ดู [[../project/roadmap|Roadmap R-11]]
