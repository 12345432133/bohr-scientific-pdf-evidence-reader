# Result Schema

## Top Level

`result.json` is one UTF-8 JSON object.

| Field | Requirement |
|---|---|
| `schema_version` | Parser schema version |
| `case_id` | Exact value from the case input |
| Contract fields | Copy every key from the original `output_contract` at top level |
| `status` | Honest run state |
| `input_identifier` | Filename, SHA-256, and page count |
| `task` | Case path, task path, and task Markdown |
| `document` | Full extracted document model |
| `contract_output` | Convenience copy of the contract-field mapping |
| `evidence` | Page- and bbox-linked source records |
| `uncertainties` | Named limitations and their impact |
| `change_records` | Time-stamped extraction and correction steps |
| `runtime` | Parser, metadata, OCR policy, and warnings |

## Document Model

`document.metadata` contains the detected title, abstract, DOI, arXiv identifier, and heading outline.

`document.pages[]` contains:

- physical page number, width, and height
- text character count and OCR state
- column-layout decision
- ordered text lines with `evidence_id`, bbox, font, size, and kind
- tables with cell rows, Markdown, bbox, caption, and status
- figures with bbox and nearest caption
- formulas with raw text, bbox, and structural status
- page-local warnings

`document.full_markdown` is a readable rendering, not a replacement for the evidence-rich page model.

## Contract Mapping

The parser uses semantic key matching for common fields:

- text, body, content, transcription, 正文, 全文 -> `document.full_markdown`
- pages, 页 -> page model
- tables, 表格 -> structured tables
- figures, images, 图 -> figure boxes and captions
- formulas, equations, 公式 -> formula text and bbox
- headings, sections, 章节, 标题 -> heading outline
- references, bibliography, 参考文献 -> reference records
- evidence, sources, citations -> evidence list
- metadata, title, author, abstract -> metadata
- status, uncertainties -> run state and limitations

Unknown fields must remain present. The parser maps them to the full Markdown with `mapping_note`; use `task.md` to replace that value with the requested task-specific structure.
