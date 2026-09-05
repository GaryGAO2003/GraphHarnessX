"""Rebuild THESIS-overleaf.zip from the thesis sources (THESIS.tex, ucl_logo.png, ch/*.tex, fig/*)."""
from pathlib import Path
import zipfile

THESIS = Path(__file__).resolve().parents[2]
OUT = THESIS / "THESIS-overleaf.zip"
files = [THESIS / "THESIS.tex", THESIS / "ucl_logo.png"]
files += sorted((THESIS / "ch").glob("*.tex"))
files += sorted(p for p in (THESIS / "fig").iterdir() if p.is_file())
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f, f.relative_to(THESIS).as_posix())
print("zip entries", len(files), "->", OUT.name, OUT.stat().st_size // 1024, "KB")
for f in files:
    print("  ", f.relative_to(THESIS).as_posix())
