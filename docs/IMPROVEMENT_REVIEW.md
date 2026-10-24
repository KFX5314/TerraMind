# Metrics and generalization review

Reviewed October 24, 2026, against commit `b7d86c8` and the existing local run artifacts. This is an analysis report; application code, prompts, `.env`, submissions, and evaluation artifacts were not changed. No paid model calls or leaderboard uploads were made. Existing deterministic tests: **7 passed**.

## 1. Recommendation

Fix information lost by postprocessing and context assembly before spending on larger models or more generic review passes. The highest-confidence improvement is deduplication: distinct obligations are already extracted and then discarded because their wording is similar.

The current application uses `claude-opus-5-5`, with `effort="high"` for extraction. The existing API ledger contains 848 completed calls, all recorded as `end_turn`, and about USD 79.43 in recorded usage. This is not an account balance or necessarily all event spending. There is no observed output-limit truncation in that ledger to justify raising `max_tokens` as the first change.

Use `dev-v6-newimg` as the reproducible current baseline. The repository's results document reports platform precision 42.7%, recall 77.9%, and F2 66.8% for its 347 requirements. Those platform numbers were read from the team's saved report, not independently retrieved from the platform.

The same run currently scores precision 36.60%, recall 66.84%, and F2 57.36% under the local lexical proxy. This discrepancy matters: a proxy calibrated on an earlier run is not a reliable numerical predictor of the latest platform score.

## 2. First priority: stop merging distinct obligations

Location: `certi/pipeline.py`, `dedupe()`, around lines 290-307.

The current rule merges any two texts in the same regulation when character-level `SequenceMatcher` similarity exceeds 0.9. It does not require the same paragraph, subject, test mode, condition, limits, units, or references.

Measured on `dev-v6-newimg`:

- 653 raw candidates become 592 retained candidates.
- 61 candidates are merged away.
- 26 dropped candidates meet the current export threshold of 0.5.
- 12 of those 26 have different numeric content from the retained candidate.
- 17 of those 26 come from a different paragraph than the retained candidate.

These counts identify review candidates, not 26 guaranteed additional golden matches. Some near-duplicates can be legitimate merges. However, source inspection confirmed several materially different obligations are merged:

| Retained obligation | Dropped obligation | Why they differ |
|---|---|---|
| UN R10 pulse 1, -75 V / -450 V, 500 pulses | Pulse 2a, +37 V / +37 V, 500 pulses | Different test pulse, limits, and performance classes |
| UN R10 pulse 1 | Pulse 2b and pulse 3b | Different pulse, voltage, duration/count, and performance classes |
| UN R10 measurement according to Annex 7 | Measurement according to Annex 8 | Separate measurement methods/provisions |
| UN R10 Annex 7 limit remains 63 dB microvolts/m | Annex 8 limit remains 53 dB microvolts/m | Different method and numeric limit |
| UN R150 post-test colour requirement | Post-test RI requirement | Different measured property and reference |

A synthetic pair differing only in `100 N` versus `200 N` also becomes one requirement, at approximately 0.990 similarity. This demonstrates a product-independent defect.

### Offline experiment

I compared the saved candidates under the same 0.5 export threshold. No model generation was rerun and no submission was overwritten.

| Postprocessing | Exported | Proxy matches | Proxy precision | Proxy recall | Proxy F2 |
|---|---:|---:|---:|---:|---:|
| Current fuzzy dedupe | 347 | 127 | 36.60% | 66.84% | 57.36% |
| Exact normalized text + paragraph only | 373 | 135 | 36.19% | 71.05% | 59.58% |
| Fuzzy merge requiring same paragraph, numeric sequence, and condition | 372 | 135 | 36.29% | 71.05% | 59.63% |

The guarded variant is a diagnostic, not a complete production semantic equivalence checker. It still does not fully distinguish all subjects, units, polarity, or scope. These are proxy gains of roughly 2.2 percentage points, not a measured platform gain and not something to add to the reported platform F2.

### Implementation recommendation

Start with exact-duplicate removal using carefully normalized whitespace while preserving numeric signs, comparison operators, units, negation, subjects, and references. Include source identity/paragraph in the equivalence key. Keep near-duplicate pairs as review suggestions.

For optional semantic merging, require equivalent structured obligations: subject, action, applicability, conditions, exceptions, quantity/unit/comparison operator, and referenced test. Different table-row identities or modalities should block an automatic merge. Text similarity should discover candidates for checking, not decide equivalence.

Test on synthetic force/voltage/temperature/time limits, separate vehicle classes, separate functions, positive versus negative obligations, and differing annex references. Re-export to a new candidate artifact and compare with the baseline. Keep the current final submission intact until a new one is deliberately selected.

## 3. Second priority: provide complete context around each extraction target

Location: `certi/pipeline.py`, `chunks_for()`, around lines 159-201.

Current behavior:

- Groups mostly by main body versus annex, then by 8,000-character size.
- Splits overlong paragraph text by raw character positions.
- Drops definition sections entirely from extraction inputs.
- Does not attach ancestor paragraphs despite the parser already storing parent IDs.
- Does not resolve cross-references into context.
- Appends Markdown tables to paragraph text, which can then be split by the same character rule.

Thus a section may begin with a child paragraph whose governing condition was in the preceding chunk. A definition can be excluded from the whole pipeline even when a retained obligation depends on it. Smaller chunks alone can worsen these issues.

A structural diagnostic of the four currently selected sources found:

| Regulation | Current chunks | Parent links with parent outside the chunk | Explicit paragraph references outside chunk |
|---|---:|---:|---:|
| UN R10 | 44 | 81 | 100 |
| UN R148 | 18 | 64 | 59 |
| UN R150 | 25 | 48 | 59 |
| UN R48 | 38 | 199 | 223 |

These are occurrence counts from a structural/reference heuristic, not distinct missed obligations. Some missing parents are merely headings and some references need no expansion. They demonstrate unprovided context that deserves targeted treatment.

### Recommended chunk shape

Separate **target material**, for which obligations must be extracted, from **supporting context**, which informs interpretation:

```text
source identity + full hierarchical heading path
relevant product facts, with uncertainty

context:
  ancestor clauses and inherited conditions
  relevant definitions
  directly referenced clauses, table headers, and footnotes
  prior/following sentence where a boundary requires it

targets:
  enumerated atomic clauses/list items/table rows, each with stable IDs
```

Extract obligations from target IDs. Context records remain citeable as supporting evidence but are not independently re-extracted in every chunk. Preserve the ability to enumerate their own obligations when they become targets elsewhere.

Use paragraph/list/sentence boundaries rather than cutting at arbitrary characters. Split tables by logical rows or row groups, repeating multi-level headers, units, scope, and footnotes. Give rows/cells source identities. Avoid concatenating both flattened table noise and structured table text without labelling their relationship.

Plan batches by actual token count plus normative density. An 8,000-character batch is not an 8,000-token batch. A table with many independently assessable constraints should receive a smaller target batch and a specialist extraction pass.

A reasonable experiment is target bodies around 1,500-2,500 tokens, with separately bounded context; these are proposed test ranges, not an established optimum. Retain the existing 8,000-character approach as the control. Verify target-ID coverage under every packing scheme.

### Protect recall at the regulation gate

In `screen()` around lines 132-134, a missing model decision becomes `potentially_applicable` at probability 0.3, with a message saying it is kept for review. `selected_regulations()` around lines 141-144 then drops it at the 0.5 threshold. There is no subsequent review of that missing decision. The synthetic missing-decision check therefore selects no regulation. This was not an observed missing decision in the latest run, but is a clear failure-handling gap for new cases.

Retry missing decisions and perform targeted scope review for uncertain exclusions. Do not indiscriminately include every possible regulation; preserve an explicit, evidence-backed decision. The screening input also clips scope to 2,500 characters and transitional provisions to 600, so ambiguous decisions should be revisited with their complete governing context.

## 4. Third priority: replace generic auditing with a coverage-driven repair pass

Locations: `certi/pipeline.py` around lines 219-251 and 359-381; `certi/prompts.py` around lines 115-122; `certi/extract_prompt.py` around lines 82-97.

All 125 chunks in the latest run are marked `done`, but the response schema only returns a list of requirements. It does not account for each clause, sentence, list item, or table row. An empty or incomplete list can still make a chunk complete.

The current audit receives the first result before rereading the same chunk, uses the same underlying extraction prompt and model, and only asks for additions. It is susceptible to the same missing context and to anchoring on the first result. It also cannot reject wrong existing candidates.

The saved report says the older audit added 63 candidates with only three correct under the internal evaluation and approximately 40% extra cost. That is evidence against blindly enabling the current `--audit` implementation. It does not establish that a different targeted audit will be ineffective on the current pipeline.

### Recommended specialist roles

| Role | Input and output | Routing |
|---|---|---|
| Obligation census | Enumerate target clauses, normative predicates, list items, table rows; mark obligation/context/non-applicable/uncertain with evidence | Deterministic enumeration plus a model where semantics require it |
| Primary extractor | Produce atomic, scoped obligations for target IDs | Keep current Opus baseline until a cheaper model is evaluated |
| Table specialist | Reconcile rows/cells with headers, units, footnotes, and page crop | Opus on difficult tables; compare Sonnet for simpler ones |
| Omission specialist | Inspect uncovered or suspicious target IDs with complete context; independently extract before comparing with draft | High effort; test higher effort only on difficult cases |
| Evidence/applicability verifier | Check support, scope, conditions, numbers, negation, and duplicate equivalence | Sonnet/Opus comparison on fixed labelled cases |

Use narrow specialist tasks rather than multiple full-document rereads. Assign a disposition to every target ID, then schedule missing/uncertain IDs, unexplained empty sections, or obligation-density discrepancies. A count of `shall` is a useful anomaly signal, not ground truth: normative tables and implicit conditions also matter.

Bound repair rounds and spend. Measure how many source-grounded obligations were recovered, how many extras were added, and what they cost. A second model's agreement is not a calibrated confidence measure.

## 5. Evidence verification is currently incomplete

Locations: `certi/pipeline.py`, `resolve_page()` around lines 259-276 and `fidelity()` around lines 279-287.

Two deterministic reproductions:

1. `resolve_page("UN R10", "6.9.1", "This entirely fictional sentence is not in any regulation.")` returns page 12 because the function falls back to the paragraph's first page when a quote does not match.
2. Source `The lamp shall not emit white light.` and generated text `The lamp shall emit white light.` produce fidelity **1.0**, because `not` is removed from the content-word comparison.

Page fallback is acceptable as a navigation hint if labelled accordingly. It must not be interpreted as evidence verification. Word retention is not entailment, and the score is not currently an export-quality gate.

Add separate fields for source-location resolution and semantic evidence status. Resolve source spans using normalization that preserves legal/engineering meaning. Check polarity, quantities, operators, units, scope and conditions. Let an evidence review repair or mark unresolved candidates; do not automatically discard every imperfect OCR/text match.

The latest export also contains 101 conditional requirements, while 82 retained candidates labelled `applies` fall below the export probability threshold. This is not automatically wrong, but shows that one predicted probability conflates applicability and likelihood of appearing in the expert list. Split evidence quality, applicability, and reviewer confidence rather than interpreting the current probability as objective correctness.

The export truncates text with `[:2000]`. None of the current exported candidates exceeds the limit (maximum 877 characters), so this is not an observed cause of current score loss. It is a transfer risk for longer obligations; replace truncation with explicit validation and meaning-preserving repair.

## 6. Overfitting controls need strengthening

Locations: `prompts/granularity_examples.md`; loading in `certi/prompts.py` around lines 9 and 112; `docs/results.md` around lines 8-20 and 104.

All **25** requirement-example texts in the current few-shot file exactly match development golden requirement texts after case/whitespace/punctuation normalization. The runtime does not open `expected.json`, but equivalent answer content is already embedded in the prompt. This does not establish misconduct or violate a rule that was checked here; it changes what the development results can demonstrate.

The examples are labelled R150/R10, but absence of R148-specific examples would not make R148 an independent test after repeated R148-driven prompt/chunk tuning. One generic example sentence also matches a golden R148 marking requirement. More importantly, the documented tuning repeatedly uses R148 outcomes. Call all these results development results.

Recommended process:

- Freeze the existing configuration and output as an incumbent baseline.
- Replace answer-derived examples with synthetic, source-grounded examples from unrelated products; vary subject, numeric values, scope, and exception structures while preserving correct semantics.
- Keep examples as demonstrations of transformations, not a copied catalogue of development obligations.
- Add independent cases for polarity, units, references, table rows, nested conditions, and new product categories.
- Paraphrase/reorder specifications while preserving meaning; change one relevant product fact and require a justified applicability change.
- Inspect new fixtures before viewing their system outputs. Use human/source-grounded expectations where practical.
- Select changes on consistent improvements across fixture families, not the highest single rear-lamp score.
- Retain a first-run snapshot on the official held-out product. Later improvements using its leaderboard feedback are feedback-guided development.

Do not remove actual engineering qualifiers merely because their wording matches the local proxy less well. Conversely, do not assume every unmatched extra is valid or out of scope for the gold without inspecting its supporting evidence.

## 7. The local proxy should not decide architecture by itself

Location: `certi/proxy.py`.

The proxy matches by word-sequence similarity, within a regulation, with a threshold tuned to earlier platform numbers. It does not independently verify source version, semantic equivalence, subject, conditions, polarity, or numeric constraints. Its greedy matching can also select a locally good pair that prevents a better overall assignment.

For the latest run, the proxy reports 127 matches while the saved platform precision/recall correspond to approximately 148. Agreement on an earlier aggregate result does not establish reliable ranking of future approaches.

Retain it as a cheap diagnostic and clearly label it. Use typed semantic checks for quantities, polarity and scope before candidate matches, then one-to-one matching with a principled assignment strategy. Independently review sampled pairs, especially changed numbers/negation and reordered clauses. An LLM judge also needs validation and is still not the official platform scorer.

For each candidate improvement, report official scores when obtained, local proxy scores separately, and source-inspected failure examples. Do not invent a conversion from proxy F2 to platform F2.

## 8. Configuration: what changing `.env` can actually do

Only nonsensitive values were inspected. No API key or team ID was printed.

| Setting | Effective current value | Recommendation |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5-5` | Keep as the quality baseline. Global switching changes every default model call, including extraction and judging. Add role-specific configuration before model-routing experiments. |
| `CERTI_CHUNK_CHARS` | Unset; default 8000 | Keep baseline. Smaller values alone cannot fix lost ancestors/definitions. Compare structural/token-based packing before broad numerical sweeps. |
| `MAX_MODEL_CONCURRENCY` | 8 | Controls throughput, not reasoning depth. No evidence that increasing it raises recall. Reduce only for rate/reliability issues. |
| `MAX_RUN_USD` | 40 | Budget control, not quality. Its current implementation does not safely enforce a per-run cap. Repair before trusting it. |
| `CLAUDE_FALLBACKS` | Unset; default enabled | For controlled model comparisons, disable fallback or record the actual responding model and fallback metadata. Currently the ledger attributes the call to the requested model. |

Extraction effort is hard-coded to `high`; it is not controlled by an effort variable in `.env`. `--deep` increases effort for product-image understanding only; it does not raise regulatory-extraction effort. `--audit` enables the generic pass discussed above. Export threshold is a CLI option or UI request, not a supported `.env` key.

The wrapper already accepts an optional `model` argument. Add explicit role wiring for primary extraction and review rather than changing the global setting to make a specialist experiment. Proposed keys such as `CLAUDE_EXTRACT_MODEL`, `CLAUDE_REVIEW_MODEL`, and `CLAUDE_EXTRACT_EFFORT` need code changes before they have any effect.

Test Sonnet on routing, simple extraction, or verification to free budget for targeted Opus work. This is a cost/quality hypothesis, not a proven upgrade. More powerful or higher-effort calls should receive the same fixed snippets and evaluation protocol. Official Anthropic guidance recommends measuring effort on the actual workload; higher effort can cost more without fixing missing input context.

### Budget and reproducibility issues

Locations: `certi/llm.py` around lines 105-125 and 160-164; `certi/pipeline.py` around lines 340-349.

- Budget is checked before semaphore acquisition; many scheduled calls can all pass against the same old spend before any completes.
- `_spent` is process-global and is not reset or isolated by run. In the web server, later runs can inherit earlier spending and concurrent runs can share unsafe state.
- There is no atomic reservation for pending calls or global remaining-credit cap.
- The API cache key omits `max_tokens`; output-limit experiments can hit an old cached response.
- Reusing a run ID reuses saved `profile.json` and `screening.json` even if inputs or models changed. Use new run IDs for experiments until invalidation is fixed.
- Parsed-document and table caches primarily check parser/table versions, not the current source hash; source replacements can leave stale parsed data.

Use per-run contexts, atomic reservations, complete request/config hashes, actual returned model IDs, and frozen input/source hashes. These are necessary to interpret model/chunk experiments and preserve the remaining credits.

## 9. Sub-goal: several general failure modes remain

The saved report gives flag recall 83.3% and change accuracy 68.4% for the latest sub-goal upload, so this is also a worthwhile improvement area.

### Preserve numerical meaning

Location: `certi/subgoal.py`, `words()`, around lines 30-34. The tokenizer removes unary minus and Unicode inequalities. Deterministic reproductions produce identical tokens for:

- `The voltage shall be at least -10 V.` and `The voltage shall be at least 10 V.`
- `The force shall be ≤10 N.` and `The force shall be ≥10 N.`

That can turn a substantive amendment into `unchanged`. The lexical proxy imports the same tokenizer, so its judgments inherit these weaknesses. Fix tokenization and add independent fixtures before relying on semantic sameness.

### Scan all new content, with scope assessment

Location: `certi/subgoal.py`, around lines 300-319.

New obligations are searched only in scopes/top-level sections represented by old requirements. Entire new sections can be missed. Additionally, every paragraph mapped to a modified requirement is skipped for addition detection, potentially hiding a new independent obligation in the same paragraph. A fixed lexical-similarity cutoff can also discard a new obligation that happens to resemble an old one.

Align old/new clauses globally, then examine all inserted or semantically changed spans. Distinguish genuinely new obligations from modifications at obligation level. Apply scope/product context separately; do not use old section membership as the only admissibility gate.

### Resolve indirect impact and alignment uncertainty

The current algorithm primarily compares a requirement's own source sentence. If a referenced definition, table, or exception changes, the sentence may be unchanged while the requirement's meaning changes. Add source dependencies and follow them during comparison.

Failure to find an old/new source is not sufficient evidence that an obligation was removed. Route low-confidence alignments and unanchored changes for semantic review. Preserve explicit unresolved statuses instead of guessing a removal.

## 10. Ordered experiment plan

Keep the same source/input hashes and fresh run/output IDs. Change one mechanism at a time. Most initial work is deterministic and needs no new generation budget.

| Order | Experiment | Why it comes first | Success criterion |
|---|---|---|---|
| 1 | Replace unsafe fuzzy merges; re-export saved candidates | Confirmed loss of already-extracted obligations; cheapest improvement | Distinct limit/condition/subject fixtures survive; no duplicate explosion; inspect offline and eventual platform delta |
| 2 | Fix semantic token normalization and verify evidence spans | Confirmed polarity/sign/operator counterexamples | Negation and numeric-change fixtures fail safely or produce correct changes |
| 3 | Add ancestor/definition/reference context with target IDs | General source of lost scope and missed conditional obligations | Same target coverage; improved correctness on nested-condition/reference fixtures and dev results |
| 4 | Add table row identities and targeted table extraction | Dense tables carry many similar-but-distinct obligations | Correct row/header/footnote association and no merge loss |
| 5 | Replace generic audit with uncovered-ID repair | Concentrates additional calls on measurable gaps | More verified recoveries per dollar with controlled extras |
| 6 | Evaluate per-role Sonnet/Opus and high/xhigh effort | Model changes become interpretable after context/postprocessing fixes | Improved measured quality/cost frontier on independent fixtures |
| 7 | Extend sub-goal diff/dependency handling | Separate scored feature with remaining headroom | Correct additions in new/modified sections; indirect change and alignment fixtures pass |

Keep the current threshold as an incumbent during these tests rather than repeatedly searching for the rear-lamp optimum. After evidence/applicability states improve, evaluate a new export policy across fixture families. Benchmark membership probabilities are not calibrated general correctness probabilities.

Do not discard a source-supported architectural fix just because a weak lexical proxy dislikes its wording. Conversely, do not claim a quality improvement based only on additional requirements, a perfect processing percentage, or a stronger model name.

## 11. Review scope and references

Inspected the main pipeline, parser, table extraction, prompts/examples, model wrapper, CLI, evaluation/proxy, sub-goal alignment and diff code, existing deterministic tests, safe configuration fields, and saved runs/usage. Existing tests passed, but their seven cases do not cover the general counterexamples above. The review did not run fresh inference, change a submission, or independently verify live leaderboard numbers.

Read-only diagnostic script: `tmp/review_metrics.py` (local ignored scratch file). It compares existing data and performs synthetic checks; it makes no model calls. Some exploratory console commands required reruns because the Windows default text encoding could not print all symbols; final counterexamples were reproduced using escaped Unicode.

External primary references:

- [Anthropic effort guidance](https://platform.claude.com/docs/en/build-with-claude/effort): effort is a measurable quality/cost control, with model-specific recommendations.
- [Anthropic model overview](https://platform.claude.com/docs/en/models/overview): current model lineup and model IDs.
- [Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): document structure, source metadata, and grounding in source quotations.

All numeric experiment results in this report are either labelled saved platform reports or reproduced local diagnostics. Proposed improvements beyond the dedupe diagnostic have not yet been measured as an end-to-end score change.
