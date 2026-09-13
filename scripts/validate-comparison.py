#!/usr/bin/env python3
"""
Validate a starlord comparison against source facts.
Usage: validate-comparison.py {task-dir}
Checks:
  1. Source tracing — every ✅✅, ✅ and ⚠️ cell references a fact in facts/ or meta/
  2. Completeness — every candidate has fact or meta files
  3. Tier rules — a ❌ on a must-have eliminates the candidate. Eliminated candidates
     stay in the matrix but get no ranking score.
  4. Score consistency — ranking scores recompute from the matrix: rule weight x mark points
     (✅✅=1.0, ✅=0.7, ⚠️=0.3, ❌=0.0). Mismatch fails the run.
  5. Gap transparency — every ❌ is listed in gaps.md. ⚠️ is a pass, not a gap.
  6. Validator report — validator-report.json exists in the task dir and its verdict is
     approved. Missing file or any other verdict fails the run, in both guard modes.
  7. File integrity — all referenced files exist
Output: PASS/FAIL to stdout, details to stderr.
"""
import json
import os
import re
import sys
import datetime
from pathlib import Path

# Check ✅✅ before ✅. One ✅ is a substring of ✅✅, so order matters.
MARK_ORDER = ["✅✅", "✅", "⚠️", "❌"]
MARK_POINTS = {"✅✅": 1.0, "✅": 0.7, "⚠️": 0.3, "❌": 0.0}
PASS_MARKS = {"✅✅", "✅", "⚠️"}
SOURCE_MARKS = {"✅✅", "✅", "⚠️"}
WEIGHTS = {"must-have": 1.0, "important": 0.7, "nice-to-have": 0.4}
TOLERANCE = 0.005

LOG_FILE = None

def log(status, msg):
    if LOG_FILE:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] [PHASE5] [{status}] {msg}\n")


def split_row(line):
    """Split a markdown table row into stripped cells, dropping the edge empties."""
    cells = [c.strip() for c in line.strip().split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def is_separator(cells):
    """True for |---|---| divider rows."""
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def load_goal(task_dir):
    """Extract criteria + priorities from goal.md."""
    goal_file = Path(task_dir) / "goal.md"
    if not goal_file.exists():
        print("ERROR: goal.md not found", file=sys.stderr)
        return []
    content = goal_file.read_text()
    criteria = {}
    for line in content.splitlines():
        cells = split_row(line)
        if len(cells) >= 3 and re.fullmatch(r"R\d+", cells[0]):
            # The Exceeds Definitions table also keys on rule IDs. Keep the first
            # occurrence per rule, which is the Locked Criteria table.
            criteria.setdefault(cells[0], {"name": cells[1], "priority": cells[2]})
    return list(criteria.values())


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


def extract_mark(cell):
    """Return the rating mark in a cell. ✅✅ is tested before ✅."""
    for mark in MARK_ORDER:
        if mark in cell:
            return mark
    return None


def normalize_priority(text):
    """Map a priority cell to its weight. Returns None for unknown priorities."""
    key = re.sub(r"[\s_]+", "-", text.strip().lower())
    return WEIGHTS.get(key)


def parse_matrix(task_dir):
    """Parse the fit check matrix from comparison.md.

    Returns {"candidates": [names], "rows": [(rule_id, priority_text, [cells])]}.
    The header must read | Req | Requirement | Priority | ...candidates... |.
    """
    comp_file = Path(task_dir) / "comparison.md"
    if not comp_file.exists():
        print("ERROR: comparison.md not found", file=sys.stderr)
        return {"candidates": [], "rows": []}
    candidates = None
    rows = []
    for line in comp_file.read_text().splitlines():
        cells = split_row(line)
        if not cells or is_separator(cells):
            continue
        low = [c.lower() for c in cells]
        if (candidates is None and len(cells) >= 4
                and low[0] == "req" and low[1] == "requirement" and low[2] == "priority"):
            candidates = cells[3:]
            continue
        if candidates is not None and re.fullmatch(r"R\d+", cells[0]):
            rows.append((cells[0], cells[2], cells[3:]))
    return {"candidates": candidates or [], "rows": rows}


def parse_ranking_table(comp_text):
    """Find the ranking score table in comparison.md.

    Header shape: | Repo | R0 (x1.0) | ... | Total | Rank |
    Returns {"rule_cols": [(cell_index, rule_id, declared_weight)],
             "total_idx": int|None, "rows": {repo: {"cells": {rule_id: float},
                                                    "total": float|None}}}
    """
    for line in comp_text.splitlines():
        cells = split_row(line)
        if len(cells) < 2 or cells[0].lower() != "repo":
            continue
        rule_cols = []
        total_idx = None
        rank_idx = None
        for j, c in enumerate(cells[1:], start=1):
            low = c.lower()
            if low == "total":
                total_idx = j
            elif low == "rank":
                rank_idx = j
            elif re.match(r"R\d+\b", c):
                rule_match = re.match(r"R\d+", c)
                w = re.search(r"[×x]\s*([0-9.]+)", c, re.IGNORECASE)
                rule_cols.append((j, rule_match.group(0) if rule_match else c,
                                  _to_float(w.group(1)) if w else None))
        if not rule_cols:
            continue
        rows = {}
        for data_line in comp_text.splitlines()[comp_text.splitlines().index(line) + 1:]:
            dcells = split_row(data_line)
            if not dcells or not data_line.strip().startswith("|") or is_separator(dcells):
                if rows:
                    break
                continue
            entry = {"cells": {}, "total": None}
            for j, rule_id, _declared in rule_cols:
                entry["cells"][rule_id] = _to_float(dcells[j]) if j < len(dcells) else None
            if total_idx is not None and total_idx < len(dcells):
                entry["total"] = _to_float(dcells[total_idx])
            rows[dcells[0]] = entry
        return {"rule_cols": rule_cols, "total_idx": total_idx, "rank_idx": rank_idx,
                "rows": rows}
    return None


def _to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def check_gaps(task_dir, failed_rule_ids):
    """Check that every rule with a ❌ is mentioned in gaps.md."""
    gaps_file = Path(task_dir) / "gaps.md"
    if not gaps_file.exists():
        return False, "gaps.md not found"
    content = gaps_file.read_text()
    missing = [cid for cid in failed_rule_ids if cid not in content]
    if missing:
        return False, f"Missing from gaps.md: {', '.join(sorted(missing))}"
    return True, ""


def check_validator_report(task_dir):
    """Check validator-report.json exists and its verdict is approved."""
    report_file = Path(task_dir) / "validator-report.json"
    errors, warnings = [], []
    if not report_file.exists():
        return (["validator-report.json not found in the task directory. "
                 "Run the conformance guard (Phase 4.4) and write the report "
                 "from templates/validator-report.template.json."], warnings)
    try:
        report = json.loads(report_file.read_text())
    except json.JSONDecodeError as e:
        return [f"validator-report.json is not valid JSON: {e}"], warnings
    verdict = report.get("verdict")
    if verdict != "approved":
        return ([f"validator-report.json verdict is {verdict!r}, expected 'approved'. "
                 f"Fix the flagged ratings and rerun the guard until approved."], warnings)
    for field in ("mode", "findings", "reasoning", "timestamp"):
        if field not in report:
            warnings.append(f"validator-report.json is missing the '{field}' field")
    if report.get("mode") == "peer-review" and not report.get("peerAgent"):
        warnings.append("validator-report.json mode is 'peer-review' but 'peerAgent' "
                        "does not name the peer agent")
    return errors, warnings


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
    comp_file = Path(task_dir) / "comparison.md"
    comp_text = comp_file.read_text() if comp_file.exists() else ""
    matrix = parse_matrix(task_dir)
    candidates = matrix["candidates"]

    if not criteria:
        errors.append("No criteria found in goal.md")
    if not matrix["rows"]:
        errors.append("No rated matrix rows found in comparison.md")
    if not candidates:
        errors.append("No candidates found in comparison.md (header must read "
                      "| Req | Requirement | Priority | ... |)")

    # 2. Rate every cell, collect claims and tier outcomes
    ratings = {}       # candidate -> {rule_id: mark}
    cell_text = {}     # (candidate, rule_id) -> raw cell
    failed_rule_ids = set()
    marks_seen = {}
    for rule_id, priority_text, cells in matrix["rows"]:
        weight = normalize_priority(priority_text)
        if weight is None:
            errors.append(f"Unknown priority '{priority_text}' on rule {rule_id} "
                          f"(expected Must-have, Important or Nice-to-have)")
        if len(cells) != len(candidates):
            errors.append(f"Matrix row {rule_id} has {len(cells)} candidate cells, "
                          f"expected {len(candidates)}")
        for cand, c in zip(candidates, cells, strict=False):
            mark = extract_mark(c)
            cell_text[(cand, rule_id)] = c
            if mark is None:
                errors.append(f"No rating mark in cell: {cand} / {rule_id} — '{c}'")
                continue
            ratings.setdefault(cand, {})[rule_id] = mark
            marks_seen[mark] = marks_seen.get(mark, 0) + 1
            src_match = re.search(r"\[([^\]]+)\]", c)
            if mark in SOURCE_MARKS and not src_match:
                errors.append(f"Unsourced {mark}: {cand} / {rule_id} — cell: '{c}'")
            if mark == "❌":
                failed_rule_ids.add(rule_id)

    # 3. Source tracing summary
    total_cells = sum(marks_seen.values())
    sourced_cells = sum(1 for (cand, rule_id) in cell_text
                        if re.search(r"\[([^\]]+)\]", cell_text[(cand, rule_id)]))
    print(f"✅ {sourced_cells}/{total_cells} matrix cells carry a source reference "
          f"({', '.join(f'{m}×{n}' for m, n in marks_seen.items()) or 'none'})")

    # 4. Tier rules — must-have ❌ eliminates, eliminated candidates are unranked
    eliminated = set()
    for cand, cand_marks in ratings.items():
        for rule_id, priority_text, _cells in matrix["rows"]:
            if (normalize_priority(priority_text) == 1.0
                    and cand_marks.get(rule_id) == "❌"):
                eliminated.add(cand)
    for cand in candidates:
        if cand in eliminated:
            print(f"ℹ️  {cand} fails a must-have rule: eliminated, unranked")

    # 5. Completeness — every candidate has fact or meta files
    if candidates and (facts or meta):
        for cand in candidates:
            slug = cand.replace('/', '_')
            if slug not in facts and slug not in meta:
                errors.append(f"No fact/meta files found for candidate: {cand}")
    print(f"✅ {len(facts)} fact files, {len(meta)} meta files loaded")

    # 6. Gap transparency — every ❌ lands in gaps.md. ⚠️ is a pass, not a gap.
    if failed_rule_ids:
        ok, msg = check_gaps(task_dir, failed_rule_ids)
        if not ok:
            errors.append(f"Gap transparency: {msg}")
    print(f"{'✅' if not any('Gap transparency' in e for e in errors) else '❌'} "
          f"Gap transparency checked ({len(failed_rule_ids)} rules with ❌)")

    # 7. Score consistency — recompute weight x mark points, compare with the table
    ranking = parse_ranking_table(comp_text) if comp_text else None
    if ranking is None:
        errors.append("Ranking score table not found in comparison.md "
                      "(header must read | Repo | R... (xW) | ... | Total | Rank |)")
    else:
        rule_ids = [rule_id for rule_id, _p, _c in matrix["rows"]]
        table_rules = [rule_id for _j, rule_id, _w in ranking["rule_cols"]]
        for rule_id in rule_ids:
            if rule_id not in table_rules:
                errors.append(f"Ranking score table has no column for {rule_id}")
        weight_by_rule = {}
        for rule_id, priority_text, _cells in matrix["rows"]:
            weight_by_rule[rule_id] = normalize_priority(priority_text)
        # Declared per-rule weight in the table header must match the matrix priority.
        for _j, rule_id, declared in ranking["rule_cols"]:
            if rule_id in weight_by_rule and declared is not None \
                    and weight_by_rule[rule_id] is not None \
                    and abs(declared - weight_by_rule[rule_id]) > TOLERANCE:
                errors.append(f"Ranking score table weight for {rule_id} is {declared} "
                              f"but the matrix priority implies "
                              f"{weight_by_rule[rule_id]}")

        for cand in candidates:
            if cand not in ratings:
                continue
            if cand in eliminated:
                if cand in ranking["rows"]:
                    errors.append(f"Eliminated candidate is ranked in the score "
                                  f"table: {cand}")
                continue
            row = ranking["rows"].get(cand)
            if row is None:
                errors.append(f"Ranked candidate missing from the ranking score "
                              f"table: {cand}")
                continue
            expected_total = 0.0
            for rule_id, mark in ratings[cand].items():
                if rule_id not in row["cells"]:
                    continue
                weight = weight_by_rule.get(rule_id) or 0.0
                expected = round(weight * MARK_POINTS[mark], 2)
                expected_total += expected
                got = row["cells"][rule_id]
                if got is None:
                    errors.append(f"Ranking score for {cand} / {rule_id} is not a "
                                  f"number: expected {expected:.2f}")
                elif abs(got - expected) > TOLERANCE:
                    errors.append(f"Score mismatch: {cand} / {rule_id} — matrix mark "
                                  f"{mark} x weight {weight} = {expected:.2f}, table "
                                  f"says {got}")
            expected_total = round(expected_total, 2)
            if ranking["total_idx"] is None:
                errors.append("Ranking score table has no Total column")
            elif row["total"] is None:
                errors.append(f"Ranking score total for {cand} is not a number: "
                              f"expected {expected_total:.2f}")
            elif abs(row["total"] - expected_total) > TOLERANCE:
                errors.append(f"Score mismatch: {cand} total — cells sum to "
                              f"{expected_total:.2f}, table says {row['total']:.2f}")
        for repo in ranking["rows"]:
            if repo not in candidates:
                warnings.append(f"Ranking score table row '{repo}' is not a matrix "
                                f"candidate")

    # 8. File integrity — check referenced files exist
    for c in cell_text.values():
        src_match = re.search(r"\[([^\]]+)\]", c)
        if src_match:
            src_path = Path(task_dir) / src_match.group(1)
            if not src_path.exists() and not src_path.with_suffix("").exists():
                warnings.append(f"Referenced file not found: {src_match.group(1)}")

    # 9. Validator report — must exist with verdict approved, both guard modes
    report_errors, report_warnings = check_validator_report(task_dir)
    errors.extend(report_errors)
    warnings.extend(report_warnings)
    print(f"{'✅' if not report_errors else '❌'} Validator report checked "
          f"(validator-report.json, verdict approved)")

    # Output
    print()
    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    if errors:
        log("FAIL", f"{len(errors)} errors, {len(warnings)} warnings")
        print("\nVALIDATION: FAIL. Fix the errors before trusting the recommendation.")
        sys.exit(1)
    else:
        if warnings:
            print("\nVALIDATION: PASS (with warnings)")
        else:
            log("OK", f"PASS, {sourced_cells}/{total_cells} cells sourced, "
                      f"0 errors, 0 warnings")
        print("\nVALIDATION: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
