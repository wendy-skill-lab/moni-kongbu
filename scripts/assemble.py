#!/usr/bin/env python3
"""film.html = film_head.html (generic iPhone/WeChat engine) + part.js (this film's modules + setTime + closing tags).
Title comes from src/TITLE (written by new_film.sh) or argv[1]."""
import sys
from pathlib import Path
d = Path(__file__).parent
title = sys.argv[1] if len(sys.argv) > 1 else (d / 'TITLE').read_text().strip()
part = d / 'part.js'
if not part.exists():  # older projects named it kb_part.js / part_film.js
    part = next(p for p in (d / 'kb_part.js', d / 'part_film.js') if p.exists())
head = (d / 'film_head.html').read_text().replace('{{TITLE}}', title)
(d / 'film.html').write_text(head + '\n' + part.read_text())
print('film.html', len((d / 'film.html').read_text()), 'from', part.name)
