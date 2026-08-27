"""
daily.py - The scheduled run. Refresh what has gone stale, rebuild the vault,
and report what changed.

`run_all.py` is the from-scratch build: it assumes nothing exists and does
everything. That is the wrong shape for a job that runs every morning, for two
reasons.

  1. **The .done checkpoints would make it a no-op.** harvest skips any dataset
     that has ever completed, so a second run fetches nothing at all. Daily
     mode instead asks each dataset whether it has aged past *its own* cadence
     (harvest.MAX_AGE_HOURS): NAV every 20 hours, portfolios weekly, fee
     schedules fortnightly. Re-pulling all 21 daily would cost ~40 minutes and
     ~2,000 API calls to rediscover data that did not move.

  2. **Rebuilding is not the point; the diff is.** Nobody reads 7,000
     regenerated notes. What a holder wants to know is that their fund's fee
     went up, its risk band was re-rated, or a new quarterly portfolio landed.
     That is the changelog stage, and it is why the run ends rather than begins
     with a snapshot.

Stages whose inputs did not change are skipped, so a quiet day costs a couple
of minutes rather than three quarters of an hour.

    python daily.py                # the scheduled run
    python daily.py --dry-run      # print the plan, touch nothing
    python daily.py --full         # ignore freshness, refresh everything
    python daily.py --no-network   # rebuild from cached data only

Exit code is non-zero if any stage fails, so a scheduler can alert on it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# the Windows console defaults to cp874 here and would mangle every Thai
# stage description; the scripts themselves do the same in sec_client
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
PY = sys.executable

RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
STATE = ROOT / "data" / "state"
LOGDIR = ROOT / "data" / "logs"

# Inputs a stage reads. If none of them changed this run, the stage is skipped:
# regenerating identical notes wastes minutes and makes the git diff unreadable.
#   name -> (command, description, depends-on-these-files, needs-network)
Stage = tuple[str, list[str], str, list[str], bool]

STAGES: list[Stage] = [
    ("harvest", [PY, "scripts/harvest.py", "--stale"],
     "ดึงเฉพาะ dataset ที่หมดอายุตามรอบของตัวเอง", [], True),
    ("transform", [PY, "scripts/transform.py"],
     "รวม/กรอง/ทำความสะอาด -> data/processed/",
     ["data/raw/*.jsonl"], False),
    ("factsheets", [PY, "scripts/fetch_factsheets.py"],
     "ดาวน์โหลด factsheet PDF ที่ยังไม่มี",
     ["data/processed/funds.json"], True),
    ("parse", [PY, "scripts/parse_factsheets.py"],
     "แกะข้อความจาก PDF -> vault/Factsheets/",
     ["data/factsheets/_manifest.json"], False),
    ("masters", [PY, "scripts/resolve_masters.py"],
     "หา ISIN กองทุนหลักจากพอร์ตของ feeder",
     ["data/processed/funds.json"], False),
    ("masterdata", [PY, "scripts/fetch_masters.py"],
     "เติมข้อมูลกองทุนหลักที่ยังขาด (Yahoo + FT)",
     ["data/processed/master_funds.json"], True),
    ("masternotes", [PY, "scripts/gen_master_notes.py"],
     "สร้างโน้ตกองทุนหลัก",
     ["data/processed/master_funds.json", "data/masters/*.json"], False),
    ("figi", [PY, "scripts/fetch_figi.py"],
     "ผูกสินทรัพย์กับรหัสสากลของ Bloomberg (OpenFIGI)",
     ["data/processed/entities.json"], True),
    ("entities", [PY, "scripts/normalize_entities.py"],
     "รวมชื่อสินทรัพย์ให้เป็นตัวตนเดียว",
     ["data/processed/funds.json", "data/processed/master_funds.json",
      "data/processed/figi.json"], False),
    ("lookthrough", [PY, "scripts/lookthrough.py"],
     "คูณทะลุกองทุนหลักไปถึงหลักทรัพย์จริง",
     ["data/processed/entities.json", "data/processed/master_funds.json",
      "data/masters/*.json"], False),
    ("entitynotes", [PY, "scripts/gen_entity_notes.py"],
     "สร้างโน้ตสินทรัพย์ + ดัชนี by-holding + by-lookthrough",
     ["data/processed/entities.json", "data/processed/lookthrough.json"], False),
    ("vault", [PY, "scripts/gen_vault.py"],
     "สร้างโน้ตกองทุน / บลจ. / ดัชนี",
     ["data/processed/funds.json", "data/processed/entity_links.json",
      "data/processed/master_links.json",
      "data/processed/lookthrough.json"], False),
    ("policies", [PY, "scripts/gen_policy_notes.py"],
     "สร้างโน้ตหมวดนโยบาย",
     ["data/processed/funds.json"], False),
    ("quality", [PY, "scripts/gen_data_quality.py"],
     "รายงานคุณภาพข้อมูลจากผลรันจริง",
     ["data/processed/funds.json"], False),
    ("changelog", [PY, "scripts/gen_changelog.py"],
     "เทียบกับ snapshot ครั้งก่อน -> vault/Changes/",
     ["data/processed/funds.json", "data/processed/entities.json"], False),
    ("validate", [PY, "scripts/validate_vault.py"],
     "ตรวจลิงก์เสีย / orphan / frontmatter", [], False),
    ("semantics", [PY, "scripts/validate_semantics.py"],
     "ตรวจความสมเหตุสมผลเชิงความหมาย (ตัวตน / benchmark / ตัวเลข)",
     ["data/processed/funds.json"], False),
]

# stages that must run every time regardless of input fingerprints
ALWAYS = {"harvest", "changelog", "validate", "semantics"}


def fingerprint(patterns: list[str]) -> str:
    """Cheap content signature: (path, size, mtime) for every matching file.

    Hashing 700 MB of raw JSONL every morning would cost more than the stage
    it is meant to skip, and size+mtime is enough - these files are rewritten
    wholesale by their producing stage, never edited in place.
    """
    parts: list[str] = []
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            try:
                st = path.stat()
            except OSError:
                continue
            parts.append(f"{path.relative_to(ROOT).as_posix()}:{st.st_size}:"
                         f"{int(st.st_mtime)}")
    return "|".join(parts)


def load_state() -> dict:
    path = STATE / "daily.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "daily.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    full = "--full" in argv
    offline = "--no-network" in argv
    only = {argv[i + 1] for i, a in enumerate(argv) if a == "--only"}
    skip = {argv[i + 1] for i, a in enumerate(argv) if a == "--skip"}

    state = load_state()
    prints = state.get("fingerprints", {})
    started = datetime.now()
    LOGDIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"Fund Knowledge — daily run  {started:%Y-%m-%d %H:%M:%S}")
    if full:
        print("  mode: --full (freshness ignored)")
    if offline:
        print("  mode: --no-network (cached data only)")
    print("=" * 72)

    results: list[tuple[str, str, float]] = []
    failed = 0
    t_all = time.time()

    for name, cmd, desc, deps, needs_net in STAGES:
        if only and name not in only:
            continue
        if name in skip:
            results.append((name, "skipped", 0.0))
            continue
        if offline and needs_net:
            results.append((name, "offline", 0.0))
            continue

        # the stage's own script counts as an input: editing a generator must
        # rebuild what it generates, or an edit silently does nothing
        watched = deps + [c for c in cmd if c.endswith(".py")]
        before = fingerprint(watched) if deps else ""
        if (deps and not full and name not in ALWAYS
                and prints.get(name) == before):
            print(f"\n-- {name}: อินพุตไม่เปลี่ยน ข้าม")
            results.append((name, "unchanged", 0.0))
            continue

        full_cmd = list(cmd)
        if full and name == "harvest":
            full_cmd = [PY, "scripts/harvest.py", "--force"]

        print(f"\n{'=' * 72}\n>> {name}: {desc}\n   $ {' '.join(full_cmd)}\n"
              f"{'=' * 72}")
        if dry:
            results.append((name, "would run", 0.0))
            continue

        t0 = time.time()
        proc = subprocess.run(full_cmd, cwd=ROOT)
        dt = time.time() - t0

        if proc.returncode == 0:
            results.append((name, "ok", dt))
            prints[name] = fingerprint(watched) if deps else ""
        elif name in ("validate", "semantics"):
            # these exit non-zero on findings: a real signal, but the data is
            # already written and the next stages do not depend on it
            results.append((name, "warnings", dt))
            failed += 1
        else:
            results.append((name, f"exit {proc.returncode}", dt))
            failed += 1
            print(f"\n!! stage '{name}' failed — stopping")
            break

    print("\n" + "=" * 72)
    print(f"{'stage':<14} {'status':<12} {'seconds':>9}")
    print("-" * 72)
    for name, status, dt in results:
        print(f"{name:<14} {status:<12} {dt:>9.1f}")
    print("-" * 72)
    total = time.time() - t_all
    print(f"{'TOTAL':<14} {'':<12} {total:>9.1f}")
    print("=" * 72)

    if not dry:
        state["fingerprints"] = prints
        state["last_run"] = started.isoformat(timespec="seconds")
        state["last_status"] = "ok" if not failed else "failed"
        state["history"] = ([{
            "at": started.isoformat(timespec="seconds"),
            "seconds": round(total, 1),
            "failed": failed,
            "stages": {n: s for n, s, _ in results},
        }] + state.get("history", []))[:60]
        save_state(state)

        log = LOGDIR / f"daily-{started:%Y-%m-%d}.log"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"\n{started:%Y-%m-%d %H:%M:%S} "
                     f"total={total:.1f}s failed={failed}\n")
            for name, status, dt in results:
                fh.write(f"  {name:<14} {status:<12} {dt:>8.1f}s\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
