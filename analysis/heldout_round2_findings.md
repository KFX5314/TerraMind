# Held-out front-bumper round 2: official feedback and offline candidates

## Official feedback (user screenshots, 25 October 2026)

The uploaded 479-requirement, 259.3 KiB file matches the saved `verified-recovery.json` byte size and requirement count. Its SHA-256 is `7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2`. The official score is requirement F2 **59.1%**, recall **74.5%**, precision **32.4%**; page precision/recall **48.6%/94.3%**; regulation precision/recall **87.5%/100%**. It ranks seventh at 09:55:44 CEST. The earlier user-reported score was F2 **54.6%**, recall **60.6%**, precision about **39.3–39.4%**. The earlier upload's requirement count and hash remain unknown, so the score change cannot be attributed causally to the nine additions alone.

At eight cited regulations, 87.5% regulation precision and 100% recall are consistent with seven relevant regulations and one extra citation. Which one is extra is unknown. R94 and GTR9 warrant review because both are vehicle-level or overlapping with R127, but no regulation was removed without evidence.

At fixed recall 74.5%, reaching F2 64.1–65.1% would require precision of roughly 41–43%. At fixed precision 32.4%, it would require recall roughly 85–87%. A mix of both improvements is more plausible. These are arithmetic scenarios, not score predictions.

## Confirmed issues and scope review

The saved extraction marked **284 of 470 exported baseline requirements conditional**. `finalize()` does not export its `condition` field, and many requirement texts lack that condition. The impact on platform judging is unknown, but variant assumptions are a concrete precision risk.

The current 479-item submission contains **39** R48 requirements from functions not identified in the written spec or drawing: front fog (9), front retro-reflectors (7), side retro-reflectors (6), cornering lamps (11), and manoeuvring lamps (6). Their saved applicability conditions depend on those devices being present. The drawing identifies decorative and side-signalling lighting, but none of those five functions. No requirements for the stated side-signalling lamp were removed.

Other possible precision costs remain deliberately unresolved: R48 daytime running lamps (14), answer-back signals (4), R148 optional lamp/module marking variants, R94 occupant-crash outcomes (14), and GTR9 overlap with R127 (30). `functional lighting` and the exact side-signal category are unspecified, so blanket removal would risk recall. The R148 marks include mandatory engineering markings and were kept. R10 includes detailed EMC laboratory steps; whether the platform counts them as requirements is unverified.

The previously identified R127 lower-legform horizontal **and** vertical impact tolerance of ±10 mm (Annex 5 paragraph 1.10, PDF page 33) is absent from the scored 479. It is source-verified and distinct from the 9 already recovered requirements. Its saved probability was 0.3; the low probability was the only export barrier.

## Candidate files (none uploaded)

| File | Requirements | Difference from scored 479 | Strict validation | SHA-256 |
|---|---:|---|---|---|
| `scored-479.json` | 479 | Byte-identical copy | OK | `7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2` |
| `feature-scope-440.json` | 440 | Remove 39 unconfirmed R48 function requirements | OK | `92b9d9a7fb34a17a649f7c9f15a4684f89ecf71c207fa46aad0c4a458d9229fc` |
| `focused-recovery-441.json` | 441 | Same 39 removals, add R127 ±10 mm test tolerance | OK | `95b36698730a1f46b009c394df9fd19d4de8c1c922493a90f8fa963e4f473212` |
| `scope-screened-418.json` | 418 | Remove 43 unconfirmed functions plus 18 lab/sampling procedures | OK | `cd70f71bfa2ad144bd527af1180e9ef861692b052d813321ffe322d9bfdb799b` |
| `balanced-423.json` | 423 | Same 61 removals plus five R127 test details | OK | `afc1c62d3c8277ec40c61e3bd61d1085a883afc12e934e22ca93e42c03978cdf` |

The 418 and 423 variants are more aggressive. Some removed lab test details could be counted by the expert list. The five R127 additions in 423 overlap GTR9 procedures, so their marginal recall is uncertain. The 441 variant has the clearest scope evidence and preserves the technical annexes and mandatory markings. All candidate submission files are read-only. Change ledgers in their respective directories give every addition/removal ID, source, and reason. No official improvement is claimed.

Because the platform counts the last valid upload, preserve the `scored-479.json` copy for possible manual rollback. If choosing one next manual test, `focused-recovery-441.json` has the narrowest evidence-based precision correction and one independently testable recovery. The possible recall loss from the 39 removed conditional functions remains the principal risk.
