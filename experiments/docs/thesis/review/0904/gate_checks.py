"""Objective gate for the overnight thesis review loop (forge-my-loop, Phase 3 step 1).

Exit code 0 = GATE PASSED, 1 = GATE FAILED.  Every check is mechanical; nothing here
reads a reviewer's opinion.  Results are also written to gate_result.json next to this file.

Checks
  compile     pdflatex (up to 3 passes): zero "! " errors, zero undefined refs/citations,
              zero multiply-defined labels, zero overfull \\hbox, 30 <= pages <= 120
  abstract    physical page 2 starts with "Abstract", page 3 with "Contents" (abstract fits one page)
  exclusion   no banned campaign names or banned numbers anywhere in the .tex sources (comments stripped);
              lines mentioning shakedown/smoke/commissioning must not carry a measurement
  anchors     every \\F{n} used in the body has a ledger row; no duplicate rows (uncited rows = WARN)
  bib         every \\cite key is a \\bibitem; every \\bibitem is cited
  unanchored  WARN only: sentences with a percentage / dollar / count and no \\F{n} anchor
  scores      figures/scores-table.tex is byte-identical to what plot_campaign_scores.py regenerates
              from the whitelist runs (skip with --no-regen)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
THESIS = HERE.parents[1]  # experiments/docs/thesis
REPO = THESIS.parents[2]  # D:\PycharmProj\HarnessX
PDFLATEX = Path(os.environ.get("GHX_PDFLATEX") or shutil.which("pdflatex") or "pdflatex")
PDFTOTEXT = Path(os.environ.get("GHX_PDFTOTEXT") or shutil.which("pdftotext") or "pdftotext")
PLOT = REPO / "experiments" / "analysis" / "plot_campaign_scores.py"
RESULT = HERE / "gate_result.json"

MAIN = "main"  # main.tex -> main.log / main.pdf
SRC_DIRS = ("frontmatter", "chapters", "appendices", "bibliography")
CH = sorted(p for d in SRC_DIRS for p in (THESIS / d).glob("*.tex"))
LEDGER = THESIS / "appendices" / "ledger.tex"
BIB = THESIS / "bibliography" / "references.tex"
BODY = [p for p in CH if p != BIB]
PROSE = [p for p in CH if p not in (BIB, LEDGER)]

HARD_BANNED = [
    r"\bM24\b",
    r"\bM25\b",
    r"28\.8",
    r"(?<![\d.])0/6\b",
    r"(?<![\d.])4/4\b",
    r"\b1\.04\b",
    r"1,375",
    r"\\times\s*20\b",
    r"×\s*20",
    r"26--33",  # 1.99 is the whitelist M22-L0 lift (F-row), not banned
    r"twenty-fold",
    r"\bx20\b",
]
SOFT_WORDS = re.compile(r"shakedown|smoke|commissioning", re.I)
MEASUREMENT = re.compile(r"\d+(?:\.\d+)?\s*(?:\\%|%|pp\b|\$|tasks\b|candidates\b|rounds\b)|\$\s*\d")


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        buf, prev = [], ""
        for ch in line:
            if ch == "%" and prev != "\\":
                break
            buf.append(ch)
            prev = ch
        out.append("".join(buf))
    return "\n".join(out)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- checks
OUTDIR: Path | None = None  # --outdir DIR: compile into DIR (private build for a maker); None = in place


def check_compile(compile_: bool = True) -> dict:
    t0 = time.time()
    log = ""
    logdir = OUTDIR or THESIS

    def aux_state() -> str:  # latexmk's criterion: stop when the auxiliary files stop changing
        return "".join(
            read(logdir / f"{MAIN}.{ext}") if (logdir / f"{MAIN}.{ext}").exists() else ""
            for ext in ("aux", "toc", "lof", "lot", "out")
        )

    before = aux_state() if compile_ else ""
    for _ in range(4 if compile_ else 1):
        if compile_:
            cmd = [str(PDFLATEX), "-interaction=nonstopmode"]
            if OUTDIR:
                OUTDIR.mkdir(parents=True, exist_ok=True)
                cmd.append(f"-output-directory={OUTDIR}")
            subprocess.run(
                cmd + [MAIN + ".tex"], cwd=THESIS, capture_output=True, text=True, errors="replace", timeout=600
            )
        log = read(logdir / (MAIN + ".log"))
        if not compile_:
            break
        after = aux_state()
        if after == before and "Rerun to get" not in log and "Label(s) may have changed" not in log:
            break
        before = after
    errors = [line for line in log.splitlines() if line.startswith("! ")]
    undefined_refs = "There were undefined references." in log
    undefined_list = re.findall(r"(?:Reference|Citation) `([^']+)'[^\n]*\n?[^\n]*?undefined", log)
    multiply = "There were multiply-defined labels." in log
    overfull_h = re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log)
    overfull_v = len(re.findall(r"Overfull \\vbox", log))
    # with -output-directory the path precedes the name and the log wraps at 79 columns
    m = re.search(r"Output written on .{0,400}?" + re.escape(MAIN) + r"\.pdf\s*\((\d+)\s*pages", log, re.S)
    pages = int(m.group(1)) if m else None
    fails = []
    if errors:
        fails.append(f"{len(errors)} error(s): {errors[0][:80]}")
    if undefined_refs or undefined_list:
        fails.append(f"undefined refs/citations: {sorted(set(undefined_list))[:8]}")
    if multiply:
        fails.append("multiply-defined labels")
    if overfull_h:
        fails.append(f"{len(overfull_h)} overfull hbox (max {max(map(float, overfull_h)):.1f}pt)")
    if pages is None:
        fails.append("no PDF written")
    elif not 30 <= pages <= 120:
        fails.append(f"page count {pages} outside [30,120]")
    return {
        "status": "FAIL" if fails else "PASS",
        "pages": pages,
        "errors": len(errors),
        "overfull_hbox": len(overfull_h),
        "overfull_vbox": overfull_v,
        "seconds": round(time.time() - t0, 1),
        "fails": fails,
    }


def check_abstract() -> dict:
    def first_line(page: int) -> str:
        pdf = str((OUTDIR or THESIS) / (MAIN + ".pdf"))
        p = subprocess.run(
            [str(PDFTOTEXT), "-f", str(page), "-l", str(page), pdf, "-"],
            cwd=THESIS,
            capture_output=True,
            text=True,
            errors="replace",
        )
        return next((line.strip() for line in p.stdout.splitlines() if line.strip()), "")

    p2, p3 = first_line(2), first_line(3)
    # page 3 is whatever front-matter section follows the abstract (declarations since round 1, else Contents)
    ok = p2 == "Abstract" and (p3 == "Contents" or p3.startswith("Declaration"))
    return {
        "status": "PASS" if ok else "FAIL",
        "page2": p2,
        "page3": p3,
        "fails": [] if ok else [f"page 2 starts '{p2}', page 3 starts '{p3}' (abstract must fit one page)"],
    }


def check_layout() -> dict:
    """Body prose pages must look like 12pt at 1.5 spacing: the median full page
    carries 18-36 text lines. Guards against an unscoped size/spacing switch.
    Chapter openers (short) and figure pages (TikZ nodes read as many lines) are
    not prose pages and are excluded from the median; a hard ceiling still
    catches a genuine shrink, which would move every page at once."""
    pdf = str((OUTDIR or THESIS) / (MAIN + ".pdf"))
    counts, prose = {}, []
    for page in range(26, 71, 4):
        p = subprocess.run(
            [str(PDFTOTEXT), "-f", str(page), "-l", str(page), "-layout", pdf, "-"],
            cwd=THESIS,
            capture_output=True,
            text=True,
            errors="replace",
        )
        lines = [line for line in p.stdout.splitlines() if re.search(r"[a-z]", line)]
        n = len(lines)
        counts[page] = n
        head = lines[0].strip() if lines else ""
        if n >= 12 and not re.match(r"^Chapter\s+\d", head):
            prose.append(n)
    prose.sort()
    med = prose[len(prose) // 2] if prose else 0
    fails = []
    if not prose:
        fails.append("no prose page found among the sampled body pages")
    elif not 18 <= med <= 36:
        fails.append(f"median prose page = {med} text lines; expected 18-36 for 12pt at 1.5 spacing {counts}")
    elif med and prose[-1] > 3 * med // 2 + 20:
        fails.append(f"densest prose page {prose[-1]} far above the median {med} {counts}")
    return {"status": "FAIL" if fails else "PASS", "median_prose_lines": med, "lines_per_page": counts, "fails": fails}


def check_exclusion() -> dict:
    hard_hits, soft_bad, soft_ok = [], [], []
    for p in CH:
        for i, line in enumerate(strip_comments(read(p)).splitlines(), 1):
            for pat in HARD_BANNED:
                if re.search(pat, line):
                    hard_hits.append(f"{p.name}:{i} [{pat}] {line.strip()[:90]}")
            if SOFT_WORDS.search(line):
                (soft_bad if MEASUREMENT.search(line) else soft_ok).append(f"{p.name}:{i} {line.strip()[:90]}")
    fails = hard_hits + [f"measurement on an excluded-campaign line: {s}" for s in soft_bad]
    return {
        "status": "FAIL" if fails else "PASS",
        "hard_hits": hard_hits,
        "soft_with_measurement": soft_bad,
        "soft_mentions": soft_ok,
        "fails": fails,
    }


def check_anchors() -> dict:
    rows = re.findall(r"\\item\[\\textbf\{F(\d+[a-z]?)\}", read(LEDGER))
    dup = [r for r, c in Counter(rows).items() if c > 1]
    uses = Counter()
    for p in BODY:
        for m in re.findall(r"\\F\{(\d+[a-z]?)\}", strip_comments(read(p))):
            uses[m] += 1
    missing = sorted(set(uses) - set(rows), key=lambda s: (len(s), s))
    uncited = sorted(set(rows) - set(uses), key=lambda s: (int(re.match(r"\d+", s).group()), s))
    fails = []
    if missing:
        fails.append(f"anchors without a ledger row: {missing}")
    if dup:
        fails.append(f"duplicate ledger rows: {dup}")
    return {
        "status": "FAIL" if fails else "PASS",
        "rows": len(rows),
        "anchors_used": sum(uses.values()),
        "distinct_used": len(uses),
        "uncited_rows": uncited,
        "fails": fails,
    }


def check_bib() -> dict:
    keys = re.findall(r"\\bibitem\{([^}]+)\}", read(BIB))
    cites = Counter()
    for p in BODY:
        for grp in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]+)\}", strip_comments(read(p))):
            for k in grp.split(","):
                cites[k.strip()] += 1
    undefined = sorted(set(cites) - set(keys))
    uncited = sorted(set(keys) - set(cites))
    dup = [k for k, c in Counter(keys).items() if c > 1]
    fails = []
    if undefined:
        fails.append(f"cited but no bibitem: {undefined}")
    if uncited:
        fails.append(f"bibitem never cited: {uncited}")
    if dup:
        fails.append(f"duplicate bibitem keys: {dup}")
    return {"status": "FAIL" if fails else "PASS", "entries": len(keys), "distinct_cited": len(cites), "fails": fails}


def check_unanchored() -> dict:
    hits = []
    for p in PROSE:
        text = strip_comments(read(p))
        text = re.sub(r"\\begin\{(table|figure)\}.*?\\end\{\1\}", " ", text, flags=re.S)
        for para in re.split(r"\n\s*\n", text):
            flat = " ".join(para.split())
            for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z\\])", flat):
                if MEASUREMENT.search(sent) and "\\F{" not in sent and "\\ref" not in sent:
                    hits.append(f"{p.name}: {sent[:110]}")
    return {"status": "WARN" if hits else "PASS", "count": len(hits), "hits": hits, "fails": []}


def check_scores(regen: bool) -> dict:
    if not regen:
        return {"status": "SKIP", "fails": []}
    table = THESIS / "figures" / "scores-table.tex"
    before = read(table)
    t0 = time.time()
    p = subprocess.run(
        [sys.executable, str(PLOT)], cwd=REPO, capture_output=True, text=True, errors="replace", timeout=900
    )
    after = read(table)
    fails = []
    if p.returncode != 0:
        fails.append(f"plot_campaign_scores.py exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}")
    elif before != after:
        table.write_text(before, encoding="utf-8", newline="\n")  # restore; the maker must regenerate on purpose
        fails.append("figures/scores-table.tex differs from a fresh regeneration (restored the checked-in version)")
    return {"status": "FAIL" if fails else "PASS", "seconds": round(time.time() - t0, 1), "fails": fails}


# --------------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    global OUTDIR, RESULT
    regen = "--no-regen" not in argv
    compile_ = "--no-compile" not in argv  # --no-compile: judge the existing main.log / main.pdf
    if "--outdir" in argv:  # private build directory (makers working in parallel)
        OUTDIR = Path(argv[argv.index("--outdir") + 1]).resolve()
        RESULT = OUTDIR / "gate_result.json"
        regen = False
    results = {
        "compile": check_compile(compile_),
        "abstract": check_abstract(),
        "layout": check_layout(),
        "exclusion": check_exclusion(),
        "anchors": check_anchors(),
        "bib": check_bib(),
        "unanchored": check_unanchored(),
        "scores": check_scores(regen),
    }
    results["_meta"] = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "argv": argv}
    RESULT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    failed = False
    for name, r in results.items():
        if name.startswith("_"):
            continue
        extra = ""
        if name == "compile":
            extra = f"pages={r['pages']} errors={r['errors']} overfull_hbox={r['overfull_hbox']} ({r['seconds']}s)"
        elif name == "anchors":
            extra = f"rows={r['rows']} used={r['distinct_used']} uncited={len(r['uncited_rows'])}"
        elif name == "bib":
            extra = f"entries={r['entries']} cited={r['distinct_cited']}"
        elif name == "unanchored":
            extra = f"sentences={r['count']}"
        elif name == "exclusion":
            extra = f"hard={len(r['hard_hits'])} soft_bad={len(r['soft_with_measurement'])} soft_ok={len(r['soft_mentions'])}"
        print(f"[{r['status']:4}] {name:10} {extra}")
        for f in r.get("fails", []):
            print(f"        - {f}")
        failed |= r["status"] == "FAIL"
    print("GATE FAILED" if failed else "GATE PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
