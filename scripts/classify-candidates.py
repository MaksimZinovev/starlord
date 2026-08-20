#!/usr/bin/env python3
"""
Classify candidate repos by relevance to the user's goal using Ollama.
Usage: classify-candidates.py {candidates.json} {goal} [--model MODEL] [--max N]
Input: JSON array of repo objects (from pull-stars.sh or keyword filter)
Output: JSON array of top N candidates with relevance reason, to stdout.
Fallback: if Ollama not available, prints error to stderr and exits 1
          (agent should fall back to LLM classification).
"""
import sys, json, os, urllib.request, subprocess, argparse

def ollama_available():
    """Check if ollama CLI exists and is running."""
    try:
        subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Check Ollama cloud
    if os.environ.get("OLLAMA_API_KEY"):
        return True
    return False

def call_ollama(prompt, model="gemma3:4b"):
    """Call Ollama (local or cloud) and return the response text."""
    # Try local first
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Try cloud
    key = os.environ.get("OLLAMA_API_KEY")
    if key:
        req = urllib.request.Request(
            "https://ollama.com/v1/chat/completions",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    return None

def classify(candidates, goal, model, max_n):
    """Classify each candidate and return top N."""
    results = []
    for repo in candidates:
        name = repo.get("full_name", "?")
        desc = repo.get("description", "") or ""
        topics = ", ".join(repo.get("topics", []))
        lang = repo.get("language", "") or ""

        prompt = (
            f"Given the goal: \"{goal}\"\n\n"
            f"Repo: {name}\n"
            f"Description: {desc}\n"
            f"Language: {lang}\n"
            f"Topics: {topics}\n\n"
            f"Is this repo relevant to the goal? Answer with EXACTLY one line:\n"
            f"YES|NO - one sentence reason"
        )

        response = call_ollama(prompt, model)
        if response is None:
            print(f"ERROR: Ollama call failed for {name}" , file=sys.stderr)
            results.append({**repo, "relevant": "UNKNOWN", "reason": "Ollama unavailable"})
            continue

        relevant = "YES" if response.upper().startswith("YES") else "NO"
        reason = response.split("-", 1)[-1].strip() if "-" in response else response

        results.append({**repo, "relevant": relevant, "reason": reason})
        print(f"  {name}: {relevant} — {reason}", file=sys.stderr)

    # Filter to YES and take top N
    yes_results = [r for r in results if r["relevant"] == "YES"]
    yes_results.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    return yes_results[:max_n]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidates_file", help="JSON file with candidate repos")
    parser.add_argument("goal", help="User's goal statement")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name")
    parser.add_argument("--max", type=int, default=12, help="Max candidates to keep")
    args = parser.parse_args()

    if not ollama_available():
        print("ERROR: Ollama not available. Agent should fall back to LLM classification.", file=sys.stderr)
        sys.exit(1)

    with open(args.candidates_file) as f:
        candidates = json.load(f)

    print(f"Classifying {len(candidates)} candidates with model={args.model}...", file=sys.stderr)
    top = classify(candidates, args.goal, args.model, args.max)
    print(f"Kept {len(top)} relevant candidates.", file=sys.stderr)

    json.dump(top, sys.stdout, indent=2)

if __name__ == "__main__":
    main()