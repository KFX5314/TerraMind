# 3-minute pitch outline

| Time | Content |
|---|---|
| 0:00-0:20 | Problem: engineers read hundreds of pages per regulation to find the few paragraphs that apply to their part; a missed obligation means a non-compliant product. |
| 0:20-1:10 | Live demo: front bumper spec + exploded view → product profile (spec-stated / observed / inferred / unknown) → all 56 regulations screened with reasons → requirements grouped by regulation → click one → exact page of the base PDF with the passage highlighted, plus "why applicable" and a proposed test. |
| 1:10-1:40 | Open facts: conditional requirements (e.g. replaceable light-source modules) are flagged, not invented; open questions listed on the Product tab. |
| 1:40-2:15 | Update impact: UN R175 0.1.0 → 1.0.0. 94 old requirements → 6 modified, 1 removed, ~17 added, each with the word diff and the reason; renumbered paragraphs ("6.5.2, formerly 6.5") are tracked, editorial changes ("6 seconds" → "6 s") are ignored. |
| 2:15-2:45 | Proof (measured, see docs/results.md): regulation level 4/4 with no extra regulation on the worked example; page-level recall ≈ 0.94; requirement-level F2 ≈ 0.69 (internal judge) / platform score; sub-goal flags 7/7 with the right change type. What we measured and turned off: the second-pass "omission auditor" added 63 items, 3 correct, so it is off by default. Weakness: precision ≈ 0.45, mostly real obligations the expert list leaves out; table rows are sometimes bundled. |
| 2:45-3:00 | Fit for Certivity: runs on Certivity's paragraph-level corpus, the citation is resolved by code (never by the model), it uses the same UI language as the Certivity app, and the ReqIF/export and update inbox are natural integration points. |

Closing line: "We turn a product specification into traceable engineering obligations, and when the rules change, we show
engineers exactly what to revisit."
