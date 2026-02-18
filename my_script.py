from pathlib import Path

root = Path(r"D:\skypro\run_with_love_crm")
exclude_parts = {"venv", "migrations", "__pycache__"}

total = 0
files = 0

for p in root.rglob("*.py"):
    if any(part in exclude_parts for part in p.parts):
        continue
    try:
        total += sum(1 for _ in p.open("r", encoding="utf-8"))
        files += 1
    except UnicodeDecodeError:
        total += sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore"))
        files += 1

print("files:", files)
print("lines:", total)