"""Lint a submission-qa-prep output against the submission it was generated from.

Usage:
  python3 check_output.py snapshot <submission_dir> > before.sha
  python3 check_output.py check <output.md> <submission_dir> [before.sha]

Checks the parts of the output contract a script can see; answer quality
(honesty, accuracy) still needs a human read against fixture-answer-key.md.
"""
import hashlib
import re
import sys
from pathlib import Path

CATEGORIES = [f"C{i}" for i in range(1, 7)]
REQUIRED_FIELDS = ["출제 근거", "모범 답안", "외울 키워드", "확인용 근거", "꼬리 질문"]
MAX_ANSWER_CHARS = 600
CITE = re.compile(r"([\w./-]+\.(?:py|md|ts|tsx|js|jsx|go|java|kt|rs|json|ya?ml|toml|sql|txt)):(\d+)(?:-(\d+))?")


def snapshot(root):
    lines = []
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}")
    return "\n".join(lines) + "\n"


def pair_blocks(text):
    parts = re.split(r"^### (C[1-6]-\d+)\.?", text, flags=re.M)
    return list(zip(parts[1::2], parts[2::2]))


def answer_text(body):
    m = re.search(r"모범 답안[^:：\n]*[:：]\**\s*(.*?)(?=\n- (?:외울 키워드|확인용 근거|꼬리 질문)|\n\*\*(?:외울|확인용|꼬리)|\Z)", body, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def resolve(root, path):
    p = Path(root) / path
    if p.is_file():
        return p
    hits = [h for h in Path(root).rglob(Path(path).name) if str(h).endswith(path)]
    return hits[0] if len(hits) == 1 else None


def check(out_md, root, before=None):
    text = Path(out_md).read_text(encoding="utf-8")
    errors = []
    blocks = pair_blocks(text)
    seen = {b[0].split("-")[0] for b in blocks}
    for c in CATEGORIES:
        if c not in seen:
            errors.append(f"missing category {c}")
    for pid, body in blocks:
        for f in REQUIRED_FIELDS:
            if f not in body:
                errors.append(f"{pid}: missing field '{f}'")
        ans = answer_text(body)
        if not ans:
            errors.append(f"{pid}: empty answer")
        elif len(ans) > MAX_ANSWER_CHARS:
            errors.append(f"{pid}: answer {len(ans)} chars > {MAX_ANSWER_CHARS}")
        if not CITE.search(body):
            errors.append(f"{pid}: no file:line citation")
    for m in CITE.finditer(text):
        path, start, end = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        p = resolve(root, path)
        if p is None:
            errors.append(f"citation to missing file: {m.group(0)}")
            continue
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        if end > n or start < 1:
            errors.append(f"citation past end of file ({n} lines): {m.group(0)}")
    if "약점" not in text:
        errors.append("missing weakness list (약점)")
    if before is not None and Path(before).read_text() != snapshot(root):
        errors.append("submission directory changed during the run")
    print(f"{len(blocks)} pairs, {len(errors)} problems")
    for e in errors:
        print("  -", e)
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "snapshot":
        sys.stdout.write(snapshot(sys.argv[2]))
    elif len(sys.argv) >= 4 and sys.argv[1] == "check":
        sys.exit(check(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None))
    else:
        sys.exit(__doc__)
