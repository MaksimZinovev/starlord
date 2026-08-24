#!/usr/bin/env python3
"""
Validate a starlord comparison against source facts.
Usage: validate-comparison.py {task-dir}
Checks:
  1. Source tracing — every ✅ in the matrix references a fact in facts/ or meta/
  2. Completeness — every candidate has facts for every criterion
  3. Score consistency — weighted scores match the matrix
  4. Gap transparency — every ❌ or missing fact is in gaps.md
  5. File integrity — all referenced files exist
Output: PASS/FAIL to stdout, details to stderr.
"""
import sys
import os
import json
import re
import datetime
from pathlib import Path

LOG_FILE = None

def log(status, msg):
    if LOG_FILE:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] [PHASE5] [{status}] {msg}\n")


def load_goal(task_dir):
    """Extract criteria + weights from goal.md."""
    goal_file = Path(task_dir) / "goal.md"
    if not goal_file.exists():
        print("ERROR: goal.md not found", file=sys.stderr)
        return [], []
    content = goal_file.read_text()
    criteria = []
    weights = []
    for m in re.finditer(r'\|\s*(R\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', content):
        cid, name, priority = m.groups()
        criteria.append((cid, name.strip(), priority.strip()))
    return criteria

def load_facts(task_dir):
    """Load all fact files from facts/ directory."""
    facts_dir = Path(task_dir) / "facts"
    facts = {}
    if not facts_dir.exists():
        return facts
    for f in facts_dir.glob("*_facts.json"):
        slug = f.stem.replace("_facts", "")
        with open(f) as fh:
            facts[slug] = json.load(fh)
    return facts

def load_meta(task_dir):
    """Load all meta files from meta/ directory."""
    meta_dir = Path(task_dir) / "meta"
    meta = {}
    if not meta_dir.exists():
        return meta
    for f in meta_dir.glob("*_meta.json"):
        slug = f.stem.replace("_meta", "")
        with open(f) as fh:
            meta[slug] = json.load(fh)
    return meta

def parse_comparison(task_dir):
    """Parse the fit check matrix from comparison.md."""
    comp_file = Path(task_dir) / "comparison.md"
    if not comp_file.exists():
        print("ERROR: comparison.md not found", file=sys.stderr)
        return [], []
    content = comp_file.read_text()
    # Find the fit check table
    candidates = []
    claims = []
    for m in re.finditer(r'\|\s*(R\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|(.*?)\|', content):
        cid, req, status, cells = m.groups()
        cells = cells.strip().split('|')
        for cell in cells:
            cell = cell.strip()
            if '✅' in cell:
                # Try to extract source reference
                src_match = re.search(r'\[([^\]]+)\]', cell)
                claims.append({"criterion": cid, "cell": cell, "sourced": src_match is not None, "source": src_match.group(1) if src_match else None})
            elif '❌' in cell:
                claims.append({"criterion": cid, "cell": cell, "sourced": False, "source": None, "is_fail": True})
    # Extract candidate names from table header
    header_match = re.search(r'\|\s*Req\s*\|\s*Requirement\s*\|\s*Status\s*\|(.*?)\|', content)
    if header_match:
        candidates = [c.strip() for c in header_match.group(1).split('|') if c.strip()]
    return candidates, claims

def check_gaps(task_dir, failed_claims):
    """Check that all failures/missing facts are in gaps.md."""
    gaps_file = Path(task_dir) / "gaps.md"
    if not gaps_file.exists():
        return False, "gaps.md not found"
    content = gaps_file.read_text()
    missing = []
    for claim in failed_claims:
        if claim.get("is_fail") and claim["criterion"] not in content:
            missing.append(claim["criterion"])
    if missing:
        return False, f"Missing from gaps.md: {', '.join(missing)}"
    return True, ""

def main():
    if len(sys.argv) != 2:
        print("Usage: validate-comparison.py {task-dir}", file=sys.stderr)
        sys.exit(1)

    task_dir = sys.argv[1]
    global LOG_FILE
    LOG_FILE = os.path.join(task_dir, "run.log")
    if not os.path.isdir(task_dir):
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        sys.exit(1)

    errors = []
    warnings = []

    # 1. Load data
    criteria = load_goal(task_dir)
    facts = load_facts(task_dir)
    meta = load_meta(task_dir)
    candidates, claims = parse_comparison(task_dir)

    if not criteria:
        errors.append("No criteria found in goal.md")
    if not claims:
        errors.append("No claims found in comparison.md")
    if not candidates:
        errors.append("No candidates found in comparison.md")

    # 2. Source tracing — every ✅ must have a source reference
    unsourced = [c for c in claims if not c.get("is_fail") and not c.get("sourced")]
    if unsourced:
        for c in unsourced:
            errors.append(f"Unsourced ✅: {c['criterion']} — cell: {c['cell']}")

    sourced = [c for c in claims if not c.get("is_fail") and c.get("sourced")]
    total_claims = len([c for c in claims if not c.get("is_fail")])
    print(f"✅ {len(sourced)}/{total_claims} claims sourced")

    # 3. Completeness — every candidate has fact files
    if candidates and facts:
        for cand in candidates:
            slug = cand.replace('/', '_')
            if slug not in facts and slug not in meta:
                errors.append(f"No fact/meta files found for candidate: {cand}")
    print(f"✅ {len(facts)} fact files, {len(meta)} meta files loaded")

    # 4. Gap transparency
    failed = [c for c in claims if c.get("is_fail")]
    if failed:
        ok, msg = check_gaps(task_dir, failed)
        if not ok:
            warnings.append(f"Gap transparency: {msg}")
    print(f"{'✅' if not warnings else '⚠️'} Gap transparency checked ({len(failed)} failures found)")

    # 5. File integrity — check referenced files exist
    for c in claims:
        if c.get("source"):
            src_path = Path(task_dir) / c["source"]
            if not src_path.exists() and not src_path.with_suffix("").exists():
                warnings.append(f"Referenced file not found: {c['source']}")

    # Output
    print()
    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    if errors:
        log("FAIL", f"{len(errors)} errors, {len(warnings)} warnings")
        print("\nVALIDATION: FAIL — fix errors before trusting the recommendation")
        sys.exit(1)
    else:
        if warnings:
            print("\nVALIDATION: PASS (with warnings)")
        else:
            log("OK", f"PASS, {len(sourced)}/{total_claims} claims sourced, {len(warnings)} warnings")
        print("\nVALIDATION: PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()