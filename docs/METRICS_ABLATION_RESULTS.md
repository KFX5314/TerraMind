# Local metrics experiment: 24 October 2026

Branch: `codex/metrics-ablation`. Baseline commit: `b7d86c8af94997e2162b43631470c410c293fcc9`.

The deterministic main-goal repair improves both local metrics. The sub-goal repair recovers one correct additional test step, but several replacement-text and granularity problems remain. These results justify testing the generated files on the development leaderboard; they do not establish a new platform score or held-out improvement.

## Changes tested

- Main goal: replace cross-paragraph fuzzy deduplication with exact, source-aware deduplication. Keep different numbers, polarity, source occurrences, conditions, and test cases distinct. Keep the highest-confidence exact copy without mutating the input.
- Sub-goal: disambiguate repeated exact sentences using their surrounding procedure; recognize additional occurrences in a new aligned scope.
- Sub-goal: recover the complete context of long amended provisions, rather than using only a similar prefix.
- Sub-goal: route long or malformed deterministic patches through a model rewrite; enforce replacement length at runtime, with bounded shortening and an error rather than a truncated export if the limit cannot be met.
- Evaluation: use explicit candidate IDs, a shared anonymous candidate pool, and maximum-cardinality one-to-one assignment for the sub-goal. Identical outputs receive the same semantic judgment.

No chunk-size, export-threshold, product-profile, or `.env` change was made. General granularity changes and broader extraction passes were intentionally left for separate experiments.

## Main goal: paired frozen-candidate replay

Both variants start from the same 653 candidates in `artifacts/runs/dev-v6-newimg/candidates.json`. Product understanding and requirement extraction were not regenerated. This isolates postprocessing from model/image variability. The existing source resolver and 0.5 export threshold were retained.

| Evaluation | Baseline P | Patched P | Baseline R | Patched R | Baseline F2 | Patched F2 |
|---|---:|---:|---:|---:|---:|---:|
| Deterministic lexical proxy | 36.60% | 36.19% | 66.84% | 71.05% | 57.36% | 59.58% |
| Sonnet semantic judge | 35.45% | 36.46% | 64.74% | 71.58% | 55.56% | 60.02% |

The export grows from 347 to 373 requirements. All 347 original requirement texts/source occurrences survive; the patch restores 26 additional candidates. Proxy matches increase from 127 to 135 out of 190. Sonnet matches increase from 123 to 136.

The Sonnet judge credits nine restored candidates: six from R10, two from R148, and one from R48. It also changes some judgments on existing candidates: 18 expected IDs gain matches and five lose matches, despite the baseline being a subset of the patched output. Therefore, the entire 13-match semantic difference must not be attributed to the patch. The deterministic proxy increase and direct recovery of distinct source obligations are stronger evidence than the exact semantic-judge delta.

The small proxy precision decline is real: these are additional candidates, and some remain unmatched. The local F2 improvement survives that tradeoff. This does not justify blanket lowering of thresholds or adding all historical candidates.

The saved platform baseline is still TerraMind's 66.8% F2 / 77.9% recall. Neither local evaluator can be substituted for that score, and the experiment does not predict that the leaderboard will reach the local patched percentages.

## Sub-goal: same-model generation comparison

The baseline implementation was loaded from the pinned commit. Both pipelines used `claude-sonnet-5-5`, the same old requirements and version pair, and cached identical requests. Expected outputs were read only after generation and in evaluation calls. A fresh baseline was necessary because comparing patched Sonnet output only with historic Opus output would confound the code change with model choice.

| Evaluation | Baseline | Patched |
|---|---:|---:|
| Exported changes | 26 | 27 |
| Legacy local matches / 24 | 22 | 23 |
| Legacy local recall | 91.67% | 95.83% |
| Shared semantic matches / 24 | 14 | 15 |
| Shared semantic recall | 58.33% | 62.50% |
| Shared semantic precision | 53.85% | 55.56% |
| Semantic modified/removed matches | 3 | 3 |
| Semantic added-obligation matches | 11 | 12 |

The confirmed recovery is the "hold stationary and select driving direction" step in the newly added creeping-vehicle procedure. The original algorithm could align the same old sentence with the wrong new procedure and suppress the new occurrence. The context-based tie resolution plus occurrence accounting fixes that structural error.

R-018's punctuation is repaired. R-021 now receives complete new source context, and its final replacement is 1,830 characters rather than a 2,000-character fragment. However, the semantic judge still rejects R-021 against the expected replacement because the generated text carries additional conditions. Its output is structurally safer and source-informed, but this experiment establishes no additional metric credit for that rewrite.

The judge also rejects three other modified texts over scope/qualifier differences, and some additions remain split more finely than the combined expected obligations. Judge explanations are diagnostic leads rather than proof of regulatory invalidity; gold omission alone is not a reason to delete a source-supported condition.

The sub-goal semantic percentages are deliberately stricter estimates of fully correct changes, not the platform's flag-recall/change-accuracy definitions. They should be used to compare the paired local variants, not to claim a regression from the saved platform score of 83.3% / 68.4%.

## Reliability checks and cost

- 16 tests pass, including product-independent fixtures for distinct limits/polarity, separate source occurrences, repeated steps in different procedures, amended tails, and providers ignoring schema length constraints.
- Both final patched JSON files pass the organizer's strict validator, including old-ID checks for the sub-goal.
- Model fallbacks were disabled. A conservative aggregate USD 3 allowance was enforced for the experiment using the repository's configured price estimates.
- Recorded new usage: **USD 0.48769 estimated**, across 19 billed ledger entries, all Sonnet. This is a local estimate, not an independently verified credit balance or provider invoice.
- Private outputs and intermediate judgments are under an ignored experiment directory. Earlier run outputs remain untouched.

One exploratory sub-goal judge used ambiguous integer offsets and produced inconsistent indexing. Those preliminary scores were discarded. The reported comparison uses explicit string IDs and a single shared judgment pool. Earlier intermediate rewrite files can exceed the schema length limit; only the validated final directory below is a candidate submission.

## Files and reproduction

Experiment root: `artifacts/experiments/metrics-ablation-20261024/`.

Candidate development submissions:

- Main: `main-patched/submission.json`.
- Sub-goal: `subgoal-patched-validated-v3/changes.json`.

Metrics: `main-metrics.json`, `main-semantic-metrics.json`, `subgoal-legacy-metrics.json`, `subgoal-shared-metrics.json`. Full judge responses and the shared candidate membership map are preserved alongside them. `*-usage.json` records the experiment's costs.

Run `scripts/metrics_ablation.py main`, `subgoal`, `judge`, and `main-judge` with the project virtual environment. Paid phases contact the configured Claude API. The default directory reuses frozen artifacts/cached requests; pass `--output <fresh-directory>` to start a new experiment. The baseline source remains pinned after this branch is committed.

Recommendation: keep the main dedupe repair as the strongest candidate for a development leaderboard check. Treat the sub-goal scope recovery as a modest improvement; continue investigating replacement scope and granularity before claiming a substantial change-accuracy gain. Do not switch the whole application's extraction model to Sonnet based on this experiment: main extraction quality under Sonnet was not tested.
