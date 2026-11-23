# Methodology and Evaluation

## Research question
Can a transparent clause-alignment and rule-based NLP pipeline surface material normative wording changes between successive versions of a corporate agreement, with traceable textual evidence?

## Controlled corpus
Two fictional 50-page versions of a Master Corporate Services Agreement were generated. The corpus includes stable clause identifiers and deliberately planted changes. Version B contains edits involving service levels, payment period, subcontracting consent, incident notification, data transfers, IP ownership/licensing, indemnity cap, liability cap, liability carve-outs, renewal notice, cure period, exit assistance, notices, governing law, plus an added audit clause and an added AI-data-use restriction; one disclaimer clause is removed.

## Evaluation design
The corpus is a controlled demonstration set, not an independently sampled benchmark. Counts describe the planted synthetic changes and the program's output only. They are not accuracy, precision, recall, F1, or legal correctness measurements.

## Current pipeline
DOCX paragraph extraction -> stable clause ID alignment -> deterministic comparison -> modality/negation/time expression signals -> JSON/CSV evidence output.

## Threats to validity
Stable IDs simplify alignment and are not available in arbitrary contracts. Rule-based patterns can miss paraphrases, scope, exceptions, cross-references, defined-term dependencies, tables, scanned PDFs, and layout structures. Modality strength is context-dependent. OCR errors can create false differences. Jurisdiction and governing law affect interpretation.

## Next research steps
Build a blinded lawyer-annotated dataset; compare lexical baselines, sentence embeddings, cross-encoders, and legal-domain language models; measure clause alignment and change classification separately; report precision/recall/F1 and inter-annotator agreement; add OCR with confidence propagation; evaluate across jurisdictions and document types.
