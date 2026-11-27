# Scientific PDF Quality Checklist

## Reading Order

- Confirm that title, authors, abstract, and full-width section headings stay above or between the correct column blocks.
- Check that left-column text does not jump into the right column before the left column ends.
- Check that page headers, footers, line numbers, and page numbers are excluded from body paragraphs.
- Check hyphenated line endings and multi-page continuation paragraphs.

## Tables

- Compare every table bbox and row count with the rendered page.
- Check merged cells, repeated text from merged cells, empty cells, multi-level headers, units, and footnotes.
- Check cross-page tables before claiming they are complete.

## Equations and Symbols

- Compare the raw extracted line, page, and bbox with the rendered equation.
- Preserve uppercase/lowercase Greek letters, superscripts, subscripts, primes, minus signs, roots, fractions, and units.
- Do not convert a visual equation into LaTeX unless the conversion can be checked.

## Scanned Pages

- Verify that the page had little or no text layer before OCR.
- Keep the OCR language, engine, image resolution, and page number.
- Mark OCR text as uncertain when symbols, columns, tables, or language detection fail.

## Final Review

- Every key conclusion has an evidence ID or is explicitly marked unverified.
- `status` matches the actual unresolved issues.
- `uncertainties` identifies the page and impact, not only a generic warning.
- No prepared test answer, invented score, or fabricated source location is present.
