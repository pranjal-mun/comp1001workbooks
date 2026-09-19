# PyLab Workbooks

Interactive workbooks for **COMP 1001: Introduction to Programming**
(Memorial University). Code listings run in the browser, checkpoints and
practice problems are checked as you work, and correct answers earn XP that
can be spent to reveal model answers. Python runs locally in the page
(Pyodide in a Web Worker); there is no server and nothing is uploaded.

**Live site:** <https://pranjal-mun.github.io/comp1001workbooks/>

## Run locally

```bash
python3 -m http.server 9000
```

Then open <http://localhost:9000/>. Add `?localAssets=1` to a page URL to
use the pinned copies in `vendor/` instead of the CDN (offline testing).

## Layout

```
index.html    landing page
workbooks/    one folder per lecture: index.html + exercises.json (+ build_exercises.py)
              a lecture may also have boss/ with the same three files: its boss problems
setup/        installing Python and IDLE on Windows or macOS
lab/          PyLab, a full-screen editor with files and interactive input();
              ?boss=<workbook>/<exercise> opens one boss problem with its tests
runtime/      shared engine: Pyodide worker, grader, widgets, theme, fonts
tools/        check_workbook.py (verify a workbook), answers.py (base64 helper)
vendor/       pinned Pyodide and CodeMirror for the offline fallback
```

Verify a workbook with `python3 tools/check_workbook.py workbooks/lecture-NN`.

## Notes

- Press **F** on a workbook page to present it in class, one topic at a time.
- Progress and XP live in the browser's `localStorage`; the `⋯` menu exports
  and imports them as JSON.
- The site is plain static files with relative paths; GitHub Pages serves the
  repository root (`.nojekyll` keeps `vendor/` untouched).
