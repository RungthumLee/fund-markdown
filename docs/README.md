---
title: Documentation Index
tags: [index, docs]
---

# 📚 สารบัญเอกสาร

จุดเริ่มต้นสำหรับเอกสารทั้งหมดของโปรเจกต์ Fund Knowledge Base

---

## 🚀 เริ่มต้นที่นี่

| เอกสาร | เนื้อหา |
|---|---|
| [[guides/quickstart\|Quickstart]] | ตั้งค่า key → เรียก API ครั้งแรก → สร้าง vault |
| [[guides/pipeline\|Pipeline Overview]] | ภาพรวมทั้งระบบ 6 ขั้นตอน |
| [[../README\|README]] | โครงสร้างโปรเจกต์และคำสั่งหลัก |

---

## 📖 คู่มือการใช้งาน API

| เอกสาร | เนื้อหา |
|---|---|
| [[guides/authentication\|Authentication]] | subscription key, key failover, portal migration |
| [[guides/pagination\|Pagination]] | cursor-based paging และตัวเลขประสิทธิภาพจริง |
| [[guides/rate-limits-and-errors\|Rate limits & Errors]] | HTTP status, retry policy, resilience |
| [[guides/bulk-vs-per-fund\|Bulk vs Per-fund]] | ทำไม bulk เร็วกว่า 24 เท่า |
| [[guides/api-v1-vs-v2\|API v1 vs v2]] | ความต่างและการย้ายจากของเดิม |
| [[api-reference/00-index\|API Reference]] | **21 endpoints ครบทุกตัว** |

---

## 🧠 ความเข้าใจเรื่องข้อมูล

| เอกสาร | เนื้อหา |
|---|---|
| [[guides/fund-identifiers\|Fund Identifiers]] | `proj_id` vs `regis_id` vs `fund_class_name` และวิธี join |
| [[guides/fund-taxonomy\|Fund Taxonomy]] | ตารางรหัส (enum) ทั้งหมดพร้อมความหมาย |
| [[guides/data-dictionary\|Data Dictionary]] | 104 field จากทุก endpoint |
| [[guides/scope-and-filters\|Scope & Filters]] | เกณฑ์คัดกรอง Registered / ไม่ใช่ Term / ไม่ใช่ PVD |
| [[guides/holdings-data\|Holdings Data]] | พอร์ตการลงทุน 5 แหล่ง และ feeder look-through |
| [[guides/factsheet-extraction\|Factsheet Extraction]] | แกะ sector / country / rating / ผู้จัดการ จาก PDF |
| [[guides/master-fund-sources\|Master Funds]] | ข้อมูลกองทุนหลักต่างประเทศจาก Yahoo Finance + FT.com |
| [[guides/web-search-enrichment\|Web Search Enrichment]] | ใช้ผลค้นเว็บเติมกองหลักที่ Yahoo/FT ไม่มี — และขอบเขตที่ใช้ไม่ได้ |
| [[guides/entity-normalization\|Entity Normalization]] | รวมชื่อสินทรัพย์ 26,586 ชื่อให้เหลือ 4,488 ตัวตน |
| [[guides/lookthrough\|Look-through]] | ทะลุกองทุนหลักไปถึงหุ้นจริง และข้อจำกัดของมัน |
| [[guides/openfigi\|OpenFIGI]] | ผูกสินทรัพย์กับรหัสสากลของ Bloomberg — ticker, ประเภท, FIGI |
| [[guides/daily-operation\|Daily Operation]] | รันประจำวัน รอบการอัปเดต การข้าม stage และ changelog |

---

## 🛠️ การจัดการโปรเจกต์

| เอกสาร | เนื้อหา |
|---|---|
| [[project/tasks\|Task Board]] | สถานะงานทุกรายการ |
| [[project/issues\|Issue Log]] | ปัญหาที่เจอ + วิธีแก้ |
| [[project/outstanding\|Outstanding Items]] | สิ่งที่ยังค้าง / ยอมรับข้อจำกัดไว้ก่อน |
| [[project/decisions\|Decision Log]] | การตัดสินใจเชิงออกแบบ + เหตุผล |
| [[project/data-quality\|Data Quality]] | coverage และข้อจำกัดของข้อมูล (auto-generated) |
| [[project/validation-report\|Validation Report]] | ลิงก์เสีย / orphan (auto-generated) |
| [[project/roadmap\|Roadmap]] | ทิศทางถัดไป |
| [[project/security-notes\|Security Notes]] | การจัดการ key และความลับ |
| [[project/handover\|Handover]] | สรุปผลลัพธ์และวิธีรับช่วงต่อ |

---

## 📁 เอกสารที่สร้างอัตโนมัติ

| ไฟล์ | สร้างโดย |
|---|---|
| `api-reference/*.md` | `scripts/gen_api_docs.py` |
| `guides/data-dictionary.md` | `scripts/gen_data_dictionary.py` |
| `project/data-quality.md` | `scripts/gen_data_quality.py` |
| `project/validation-report.md` | `scripts/validate_vault.py` |

> [!WARNING]
> อย่าแก้ไฟล์เหล่านี้ด้วยมือ — จะถูกเขียนทับเมื่อรันสคริปต์ใหม่
> ถ้าต้องแก้เนื้อหา ให้แก้ที่สคริปต์ที่สร้างมัน

---

## 🧭 คลังความรู้กองทุน

vault อยู่ที่โฟลเดอร์ [`vault/`](../vault/Indexes/00-home.md) — เปิดด้วย Obsidian
