"""
run_all.py - Run the whole Fund Knowledge pipeline end to end.

    python run_all.py                 # full run (skips work already done)
    python run_all.py --from vault    # start at a later stage
    python run_all.py --skip factsheets
    python run_all.py --smoke         # small run for testing

Stages: harvest -> transform -> factsheets -> parse -> masters -> entities
        -> vault -> changelog -> validate
Every stage is individually resumable, so re-running is cheap and safe.

This is the **from-scratch** build. For the scheduled rebuild use `daily.py`,
which refreshes only what has aged out and reports what changed - see
docs/guides/daily-operation.md.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

STAGES = [
    ("harvest",    [PY, "scripts/harvest.py"],
     "ดึงข้อมูลดิบทั้ง 21 dataset จาก SEC API"),
    ("transform",  [PY, "scripts/transform.py"],
     "รวม/กรอง/ทำความสะอาด -> data/processed/"),
    ("navhist",    [PY, "scripts/nav_history.py"],
     "สร้าง NAV ย้อนหลัง ~120 วัน + สถิติ (จาก data/raw/nav.jsonl)"),
    ("factorseries", [PY, "scripts/fetch_factor_series.py"],
     "ดึง series ปัจจัย (ทอง/น้ำมัน/ดอกเบี้ย/USD/SET) จาก Yahoo"),
    ("correlations", [PY, "scripts/correlations.py"],
     "correlation ของ NAV กอง กับปัจจัย (อดีต)"),
    ("factsheets", [PY, "scripts/fetch_factsheets.py"],
     "ดาวน์โหลด factsheet PDF"),
    ("parse",      [PY, "scripts/parse_factsheets.py"],
     "แกะข้อความจาก PDF -> vault/Factsheets/"),
    ("masters",    [PY, "scripts/resolve_masters.py"],
     "หา ISIN กองทุนหลักจากพอร์ตของ feeder"),
    ("masterdata", [PY, "scripts/fetch_masters.py"],
     "ดึงข้อมูลกองทุนหลักจาก Yahoo Finance + FT.com"),
    ("masternotes", [PY, "scripts/gen_master_notes.py"],
     "สร้างโน้ตกองทุนหลัก vault/MasterFunds/"),
    ("entities",   [PY, "scripts/normalize_entities.py"],
     "รวมชื่อสินทรัพย์ที่สะกดต่างกันให้เป็นตัวตนเดียว"),
    ("figi",       [PY, "scripts/fetch_figi.py"],
     "ผูกสินทรัพย์กับรหัสสากลของ Bloomberg (OpenFIGI)"),
    ("entities2",  [PY, "scripts/normalize_entities.py"],
     "รวมชื่ออีกรอบ คราวนี้มีชื่อและประเภทจาก OpenFIGI แล้ว"),
    ("lookthrough", [PY, "scripts/lookthrough.py"],
     "คูณทะลุกองทุนหลักไปถึงหลักทรัพย์จริง"),
    ("entitynotes", [PY, "scripts/gen_entity_notes.py"],
     "สร้างโน้ตสินทรัพย์ vault/Entities/ + ดัชนี by-holding / by-lookthrough"),
    ("vault",      [PY, "scripts/gen_vault.py"],
     "สร้างโน้ต Obsidian"),
    ("policies",   [PY, "scripts/gen_policy_notes.py"],
     "สร้างโน้ตหมวดนโยบายที่โน้ตกองทุนลิงก์ถึง"),
    ("docs",       [PY, "scripts/gen_api_docs.py"],
     "สร้างคู่มือ API 21 หน้า"),
    ("dictionary", [PY, "scripts/gen_data_dictionary.py"],
     "สร้าง data dictionary รวม"),
    ("quality",    [PY, "scripts/gen_data_quality.py"],
     "สร้างรายงานคุณภาพข้อมูลจากผลรันจริง"),
    ("changelog",  [PY, "scripts/gen_changelog.py", "--init"],
     "บันทึก snapshot แรกไว้ให้ daily.py เทียบในรอบถัดไป"),
    ("validate",   [PY, "scripts/validate_vault.py"],
     "ตรวจลิงก์เสีย / orphan / frontmatter"),
    ("semantics",  [PY, "scripts/validate_semantics.py"],
     "ตรวจความสมเหตุสมผลเชิงความหมาย (ตัวตนผิด / benchmark ขัดพื้นที่ / ตัวเลขเพี้ยน)"),
]

# stages allowed to exit non-zero without aborting the run: both are reporting
# gates whose data is already written and whose next stages do not depend on them
NON_BLOCKING = {"validate", "semantics"}

SMOKE_ARGS = {
    "masterdata": ["--limit", "15"],
    "factsheets": ["--limit", "20"],
    "parse": ["--limit", "20"],
    "vault": ["--limit", "50"],
}


def main() -> None:
    argv = sys.argv[1:]
    smoke = "--smoke" in argv
    start = argv[argv.index("--from") + 1] if "--from" in argv else None
    skip = {argv[i + 1] for i, a in enumerate(argv) if a == "--skip"}

    names = [s[0] for s in STAGES]
    if start:
        if start not in names:
            print(f"unknown stage '{start}'. choose from: {names}")
            sys.exit(2)
        stages = STAGES[names.index(start):]
    else:
        stages = STAGES

    print("=" * 70)
    print("Fund Knowledge pipeline")
    print("=" * 70)

    t_all = time.time()
    results = []
    for name, cmd, desc in stages:
        if name in skip:
            print(f"\n-- SKIP {name}")
            results.append((name, "skipped", 0.0))
            continue
        full = list(cmd) + (SMOKE_ARGS.get(name, []) if smoke else [])
        print(f"\n{'=' * 70}\n>> {name}: {desc}\n   $ {' '.join(full)}\n{'=' * 70}")
        t0 = time.time()
        proc = subprocess.run(full, cwd=ROOT)
        dt = time.time() - t0
        status = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"
        results.append((name, status, dt))
        # validate/semantics exit non-zero on findings, which shouldn't abort
        if proc.returncode != 0 and name not in NON_BLOCKING:
            print(f"\n!! stage '{name}' failed ({status}) — stopping")
            break

    print("\n" + "=" * 70)
    print(f"{'stage':<12} {'status':<12} {'seconds':>9}")
    print("-" * 70)
    for name, status, dt in results:
        print(f"{name:<12} {status:<12} {dt:>9.1f}")
    print("-" * 70)
    print(f"{'TOTAL':<12} {'':<12} {time.time() - t_all:>9.1f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
