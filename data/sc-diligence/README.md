# Diligence agent materials

These are the inputs for the extended task. The brief (PDF) explains the task; this file explains the data.

## Contents

| Path | What it is |
|---|---|
| `filings/msft-20260630.htm` | Microsoft Form 10-K, fiscal year ended 30 June 2026, as filed on EDGAR (accession 0001193125-26-323660) |
| `filings/aapl-20260926.htm` | Apple Form 10-K, fiscal year ended 26 September 2026, as filed on EDGAR (accession 0000320193-26-000026) |
| `questions.json` | 24 questions. 16 are in the learning split, 8 are held out |
| `feedback.jsonl` | 48 analyst corrections on learning-split questions, in four rounds of 12 |
| `examples/` | The answer format we expect from your system |

## Questions

Each question has `id`, `company`, `split` (`learn` or `held_out`), `question`, `reference_answer` and `reference_citations`.

The reference answers were written by people. Treat them the way you would treat a colleague's work.

## Feedback

Each line is one correction:

```json
{"id": "FB-001", "round": 1, "analyst": "AN-01", "question_id": "MSFT-L02",
 "correction": "...", "citations": [ ... ]}
```

- There are three analysts: `AN-01`, `AN-02` and `AN-03`. Their reliability differs, and we don't say how.
- Feedback arrives in rounds. In round *n*, you may use rounds 1 to *n* only.
- Some corrections are wrong. Not all of them can be caught by checking whether the quoted text exists.

## Citations

There are two citation types, and both point into the original filing:

```json
{"type": "sentence", "quote": "Azure and other cloud services revenue increased 41%."}
{"type": "cell", "table_row": "Total net sales", "column": "2026", "value": "478,834"}
```

- A `sentence` quote must appear verbatim in the filing's visible text. We compare after collapsing whitespace.
- A `cell` must name the row label, the column header and the value exactly as printed. Add the table name in brackets when a row label is ambiguous, for example `Services (gross margin)`.
- We check every citation your system produces.

## How we will run your system

```bash
./run.sh --filing path/to/10-K.htm --questions path/to/questions.json --out answers.jsonl
```

- The questions file has the same shape as `questions.json`, without the reference fields.
- Write one JSON object per line to the output file, in the format in `examples/`.
- The command must run from a clean clone, after one documented setup step.
- It must not need a paid API key. If it uses a local model, the setup step pulls it (for example `ollama pull <model>`). If it uses a free tier, read the key from an environment variable and tell us which one.
