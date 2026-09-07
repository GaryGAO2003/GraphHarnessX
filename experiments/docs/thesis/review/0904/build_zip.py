"""Rebuild thesis-overleaf.zip from the thesis sources (main.tex and everything it inputs)."""
from pathlib import Path
import zipfile

THESIS = Path(__file__).resolve().parents[2]
OUT = THESIS / "thesis-overleaf.zip"
files = [THESIS / "main.tex", THESIS / "preamble.tex", THESIS / "macros.tex", THESIS / "latexmkrc"]
for d in ("frontmatter", "chapters", "appendices", "bibliography"):
    files += sorted((THESIS / d).glob("*.tex"))
files += sorted(p for p in (THESIS / "figures").iterdir() if p.is_file())
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, f.relative_to(THESIS).as_posix())
print("zip entries", len(files), "->", OUT.name, OUT.stat().st_size // 1024, "KB")
for f in files:
    print("  ", f.relative_to(THESIS).as_posix())
