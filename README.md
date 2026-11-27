# Scientific PDF Evidence Reader

This submission contains a reusable Agent Skill for evidence-linked parsing of scientific PDFs. It targets text extraction, two-column reading order, tables, formulas, figure captions, references, OCR fallback, and traceable page evidence.

## Package

- `SKILL.md`: runtime instructions and task-specific behavior
- `scripts/parse_pdf.py`: deterministic PDF parser
- `scripts/validate_result.py`: structural output validator
- `references/result-schema.md`: result model and contract mapping
- `references/quality-checklist.md`: table, formula, reading-order, and OCR review checks
- `environment/resources.yaml`: expected runtime capabilities
- `requirements.txt`: Python dependencies

## Local Invocation

```bash
python scripts/parse_pdf.py \
  --case /input/case.json \
  --task /input/task.md \
  --out /app/output/result.json

python scripts/validate_result.py /app/output/result.json --case /input/case.json
```

The parser writes `document.md`, `pages.json`, `tables.json`, `evidence.jsonl`, and `run.log` beside `result.json`.

## Design Notes

The parser combines `pdfplumber` coordinates with `pypdf` text ordering and spacing repair. It detects repeated margins, page columns, full-width headings, table boxes, figure boxes, equation-like lines, and references. Missing text layers are reported as partial unless OCR succeeds.

No prepared answers or hidden-case outputs are included. Every result is generated from the supplied PDF at invocation time.
