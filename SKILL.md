---
name: scientific-pdf-evidence-reader
description: Parse scientific PDFs into page- and coordinate-linked structured results. Use for literature extraction, two-column reading order, tables, equations, figures, citations, OCR fallback, or evidence-backed PDF question answering.
---

# Scientific PDF Evidence Reader

Turn a scientific PDF into a reviewable result instead of an untraceable wall of text. Preserve the source file as authoritative and attach every extracted section, table, figure, formula, and reference line to a page and bounding box.

## When to Use

Use this skill when a task asks an agent to read or parse a research PDF, extract a structured representation, answer questions with source evidence, recover two-column reading order, reconstruct tables, preserve formulas, process scanned pages, or return uncertainty instead of guessing.

## Workflow

1. Read `case.json` and `task.md` before opening the PDF. Locate the actual PDF path and copy the exact `case_id` and `output_contract` field names from the case.
2. Run `scripts/parse_pdf.py` with the case, task, PDF, and output paths:

   ```bash
   python scripts/parse_pdf.py \
     --case /input/case.json \
     --task /input/task.md \
     --out /app/output/result.json
   ```

   Use `--pdf PATH` when `case.json` does not identify one PDF unambiguously. The script writes `result.json`, `document.md`, `pages.json`, `tables.json`, `evidence.jsonl`, and `run.log` beside the requested output.

3. Inspect `status`, `uncertainties`, `runtime.warnings`, page text counts, and table/OCR warnings. A `partial` result is valid only when the incomplete scope is named.
4. Compare low-text or structurally doubtful pages with rendered page images. If the runtime supplies `pdf-render-tool` or `ocr-tool`, read `environment/resources.yaml` and that tool's help before invoking it.
5. For OCR, prefer the runtime tool or a page-level OCR backend. The parser accepts an explicit command template through `PDF_OCR_COMMAND`, using `{input_pdf}`, `{page}`, and `{output_dir}` placeholders. Do not describe a page as fully parsed when OCR failed.
6. Review the task-specific fields. The parser maps common contract keys and also leaves the source fields under `contract_output`; if the task asks for a particular answer, translation, field set, or knowledge graph, build that result from the extracted evidence and keep the originating evidence IDs.
7. Validate the final object once more:

   ```bash
   python scripts/validate_result.py /app/output/result.json --case /input/case.json
   ```

8. Save honest partial outputs early. Never invent unreadable text, table cells, formula symbols, references, software state, or benchmark results.

## Required Output

The top level of `result.json` must contain:

- `case_id`
- every original `output_contract` field
- `status`: `success`, `partial`, `failure`, or a task-specific status if the contract requires one
- `document`, `evidence`, and `uncertainties`
- `change_records` showing what was extracted or corrected

Evidence records use stable IDs such as `p003-l0012` and include page, bounding box, kind, text or structural summary, and locator. Keep those IDs in task-specific answers whenever the answer depends on the source.

## Task-Specific Answers

After the deterministic parser finishes, read the original `task.md` and `case.json` again before editing task-specific fields.

- For extraction, return the requested fields with page and evidence IDs.
- For question answering, answer only what the source supports and cite the evidence ID after each claim.
- For translation, preserve headings, citations, symbols, and paragraph boundaries; do not translate source identifiers.
- For table or formula extraction, prefer the raw extracted representation over an invented semantic interpretation.
- For missing evidence, write `not reported` or `uncertain` and name the page that was checked.
- Copy contract keys exactly. Do not rename, nest, or omit a required field.

## Parsing Rules

- Treat the input PDF, not a filename or domain label, as factual authority.
- Preserve the original Unicode characters. Do not normalize Greek letters, superscripts, minus signs, or equation symbols into approximations.
- Correctly order two-column pages by detecting a central gutter and separating full-width headings from column-local text.
- Exclude repeated headers, footers, and page numbers from the main body while retaining them in page metadata when useful.
- Use table extraction as a structural aid, not proof of semantic correctness. Report merged cells, empty cells, and cross-page continuation as limitations when unresolved.
- Record figures and equations at the structural level required by the task. Do not infer scientific meaning from a caption alone.
- Keep reference entries separate from body prose once a References/Bibliography heading is found.

## Failure and Uncertainty

- `success`: all material text layers and requested structures were recovered with no material unresolved warnings.
- `partial`: the core result exists, but named pages, tables, OCR, formulas, or task-specific fields remain uncertain.
- `failure`: no usable document result can be produced. Preserve the error, PDF identifier, and the exact stage that failed.

Read [references/result-schema.md](references/result-schema.md) when editing the output schema or integrating a new case. Read [references/quality-checklist.md](references/quality-checklist.md) before finalizing a result with tables, equations, scanned pages, or low text coverage.

## Dependencies

The script requires Python 3.10 or newer and `pdfplumber`. `pypdf` is strongly recommended because it repairs missing spaces in LaTeX-generated PDFs; `pypdfium2` enables page rendering when Poppler is unavailable. Tesseract or an equivalent page OCR command is only needed for pages without a usable text layer.

Install the Python packages with:

```bash
python -m pip install "pdfplumber>=0.11,<1" "pypdf>=5,<7" "pypdfium2>=4,<6"
```

The runtime image may already provide `pdf-text-tool`, `pdf-render-tool`, or `ocr-tool`. Inspect `environment/resources.yaml` and the tool help before using those wrappers. Do not hard-code a local machine path.

## Minimal Example

The following is an illustrative contract, not a formal test answer:

```json
{
  "case_id": "example-001",
  "output_contract": {
    "markdown": "Full evidence-linked text",
    "tables": "Structured tables",
    "uncertainties": "Explicit limitations"
  },
  "pdf": "/input/example.pdf"
}
```

Run:

```bash
python scripts/parse_pdf.py \
  --case /input/case.json \
  --task /input/task.md \
  --out /app/output/result.json
```

The top-level result would contain `case_id`, `markdown`, `tables`, and `uncertainties`. A successful run would still be marked `partial` if a detected table has an unresolved merged-cell warning.

## Limits

- Table detection is deterministic but cannot guarantee semantic correctness for every merged or borderless table.
- Equation extraction records visual text and position; it does not claim a verified LaTeX conversion.
- OCR is page-level unless the runtime supplies a layout-aware OCR backend.
- Cross-page table continuation and complex multi-row headers may require visual review.
