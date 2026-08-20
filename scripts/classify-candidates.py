#!/usr/bin/env python3
"""
Classify candidate repos by relevance to the user's goal using Ollama.
Usage: classify-candidates.py {task-dir} {candidates.json} {goal} [--model MODEL] [--max N]
Output: JSON array of top N candidates with relevance reason, to stdout.
Fallback: if Ollama not available, exits 1 (agent falls back to LLM classification).
"""
import sys, json, os, urllib.request, subprocess, argparse, datetime

LOG_FILE = None

def log(phase, status, msg):
    if LOG_FILE:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] [{phase}] [{status}] {msg}\n")

def detect_ollama():
    """Return (available: bool, mode: str). mode is 'local', 'cloud', or 'unavailable'."""
    try:
        subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        return True, "local"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    if os.environ.get("OLLAMA_API_KEY"):
        return True, "cloud"
    return False, "unavailable"

def call_ollama(prompt, model):
    """Call Ollama (local or cloud) and return (response_text, mode_used)."""
    # Try local first
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip(), "local"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Try cloud
    key = os.environ.get("OLLAMA_API_KEY")
    if key:
        req = urllib.request.Request(
            "https://ollama.com/v1/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip(), "cloud"
    return None, None

def classify(candidates, goal, model, max_n, phase):
    results = []
    mode_used = None
    for repo in candidates:
        name = repo.get("full_name", "?")
        desc = repo.get("description", "") or ""
        topics = ", ".join(repo.get("topics", []))
        lang = repo.get("language", "") or ""

        prompt = (
            f'Given the goal: "{goal}"\n\n'
            f"Repo: {name}\nDescription: {desc}\nLanguage: {lang}\nTopics: {topics}\n\n"
            f"Is this repo relevant to the goal? Answer with EXACTLY one line:\nYES|NO - one sentence reason"
        )

        response, mode = call_ollama(prompt, model)
        if mode and not mode_used:
            mode_used = mode
            log(phase, "OK", f"Ollama {mode} used for classification (model={model})")

        if response is None:
            print(f"ERROR: Ollama call failed for {name}", file=sys.stderr)
            log(phase, "WARN", f"Ollama call failed for {name}")
            results.append({**repo, "relevant": "UNKNOWN", "reason": "Ollama unavailable"})
            continue

        relevant = "YES" if response.upper().startswith("YES") else "NO"
        reason = response.split("-", 1)[-1].strip() if "-" in response else response
        results.append({**repo, "relevant": relevant, "reason": reason})
        print(f"  {name}: {relevant} — {reason}", file=sys.stderr)

    yes_results = [r for r in results if r["relevant"] == "YES"]
    yes_results.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    kept = yes_results[:max_n]
    log(phase, "OK", f"classified {len(candidates)} repos, kept {len(kept)} (via Ollama {mode_used or 'unknown'})")
    return kept

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir", help="Task directory for logging")
    parser.add_argument("candidates_file", help="JSON file with candidate repos")
    parser.add_argument("goal", help="User's goal statement")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name")
    parser.add_argument("--max", type=int, default=12, help="Max candidates to keep")
    args = parser.parse_args()

    global LOG_FILE
    LOG_FILE = os.path.join(args.task_dir, "run.log")
    os.makedirs(args.task_dir, exist_ok=True)

    available, mode = detect_ollama()
    if not available:
        print("ERROR: Ollama not available. Agent should fall back to LLM classification.", file=sys.stderr)
        log("PHASE2", "FALLBACK", "Ollama unavailable, agent should use LLM classification")
        sys.exit(1)

    log("PHASE2", "INFO", f"Ollama {mode} detected, model={args.model}")

    with open(args.candidates_file) as f:
        candidates = json.load(f)

    print(f"Classifying {len(candidates)} candidates with model={args.model}...", file=sys.stderr)
    top = classify(candidates, args.goal, args.model, args.max, "PHASE2")
    print(f"Kept {len(top)} relevant candidates.", file=sys.stderr)

    json.dump(top, sys.stdout, indent=2)

if __name__ == "__main__":
    main()