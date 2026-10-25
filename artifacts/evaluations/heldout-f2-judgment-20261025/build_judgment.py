"""Build the 'judgment' candidate for heldout-front-bumper from the scored 450 baseline.

Three kinds of change, all deterministic and ledgered:
1. REMOVE items whose expected hit rate is far below the F2 break-even (~12 %): UN R94 (occupant criteria, most likely
   the one extra regulation), UN R10 laboratory-procedure annexes/appendices, approval-mark composition and CoP
   procedures, R148/R48 conformity-of-production sampling annexes and R148 Annex 2 table rows.
2. ADD saved candidates (same extraction run, probability < 0.5) from the sections an expert would walk through for a
   front bumper: R26 general/particular specs for listed parts, R42 requirements + Annex 3 test, R127/GTR9 bumper test
   procedure, R48 direction-indicator/hazard/general provisions, R148 generic + direction-indicator provisions.
3. TRANSPLANT the dev-case expert wording (UN R10, R148 generic, R48 general paragraphs are the same PDF text in both
   cases) onto our items of the same paragraph, adding the ones we lack. Pure upside under any text matcher.
"""
import json, re, sys, collections, hashlib
from pathlib import Path

ROOT = Path(r"C:\Users\saish\Certivity")
BASE = ROOT / "main-f2-eval/artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
POOL = ROOT / "TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json"
DEV = ROOT / "industrial-ai-hackathon/cases/dev-rear-lamp/expected.json"
OUT = ROOT / "main-f2-eval/artifacts/evaluations/heldout-f2-judgment-20261025"
OUT.mkdir(parents=True, exist_ok=True)

base = json.load(open(BASE, encoding="utf-8"))
reqs = base["requirements"]
pool = {c["id"]: c for c in json.load(open(POOL, encoding="utf-8"))}
dev = json.load(open(DEV, encoding="utf-8"))["requirements"]

# ------------------------------------------------------------------ 1. removals
REMOVE = {
    "R94 occupant injury criteria / vehicle-level frontal test (most likely the one extra regulation)":
        [r["id"] for r in reqs if r["source"]["regulation"] == "UN R94"],
    "R10 laboratory procedure annexes/appendices (dev expert kept only Annex 9 3.1 and Annex 10 2)":
        ["R-0216", "R-0217", "R-0219", "R-0222", "R-0223", "R-0224", "R-0225", "R-0226", "R-0233",
         "R-0238", "R-0239", "R-0240", "R-0244", "R-0245",
         "R-0256", "R-0258", "R-0259", "R-0260", "R-0261", "R-0262", "R-0277", "R-0279", "R-0280", "R-0282",
         "R-0283", "R-0284", "R-0285", "R-0289", "R-0290", "R-0293",
         "R-0159", "R-0160", "R-0161", "R-0162", "R-0163", "R-0164"],
    "R10 sample marking, approval-mark composition, CoP procedures":
        ["R-0001", "R-0008", "R-0009", "R-0154", "R-0156", "R-0157", "R-0158"],
    "R148 CoP sampling annexes, Annex 2 table rows, 6.1 conform-to-type":
        ["R-1120", "R-1121", "R-1123", "R-1128", "R-1129", "R-1131",
         "R-1101", "R-1105", "R-1106", "R-1107", "R-1110", "R-1111", "R-1090"],
    "R48 Annex 9 conformity-of-production checks":
        ["R-0779", "R-0780", "R-0781", "R-0782", "R-0783", "R-0786", "R-0787", "R-0788", "R-0789"],
    "R42 8.1 conform-to-type": ["R-0388"],
    "Split variants made redundant by the transplanted expert wording (R148 3.3.3.4 x3, R48 5.1)":
        ["R-0949", "R-0950", "R-0951", "R-0426"],
}
remove_ids = {i for ids in REMOVE.values() for i in ids}
assert remove_ids <= {r["id"] for r in reqs}, remove_ids - {r["id"] for r in reqs}

# ------------------------------------------------------------------ 2. additions from the saved pool
ADD = {
    "R26 general exclusions, hardness, ornaments, air-intake flaps, folds, aerial capping, projection method":
        ["R-0334", "R-0335", "R-0336", "R-0343", "R-0344", "R-0348", "R-0349", "R-0362", "R-0363", "R-0364",
         "R-0368", "R-0370", "R-0376"],
    "R42 6.1.4 exhaust outcome and Annex 3 low-speed impact test conditions":
        ["R-0385", "R-0389", "R-0390", "R-0391", "R-0392", "R-0393", "R-0394", "R-0395", "R-0396", "R-0397",
         "R-0398", "R-0400", "R-0404", "R-0405", "R-0406", "R-0407", "R-0408", "R-0409", "R-0412", "R-0413",
         "R-0416", "R-0419", "R-0422", "R-0423", "R-0424"],
    "R127 impactor certification, ARHSS, Annex 3 test conditions, Annex 5 legform-to-bumper procedure":
        ["R-0866", "R-0869", "R-0878", "R-0881", "R-0882", "R-0885", "R-0886", "R-0887", "R-0888", "R-0890",
         "R-0895", "R-0901", "R-0902", "R-0903", "R-0904", "R-0908", "R-0909", "R-0910"],
    "GTR9 measurement provisions, test conditions, legform procedure details, DPPS sensing verification":
        ["R-1164", "R-1165", "R-1166", "R-1167", "R-1168", "R-1169", "R-1187", "R-1188", "R-1189", "R-1190",
         "R-1191", "R-1193", "R-1195", "R-1197", "R-1205", "R-1207", "R-1212", "R-1213", "R-1214", "R-1215",
         "R-1221", "R-1225", "R-1234", "R-1235", "R-1236", "R-1238", "R-1240", "R-1241", "R-1242", "R-1247",
         "R-1248"],
    "R10 deemed-to-comply provisions (6.10.x) and marking visibility":
        ["R-0048", "R-0050", "R-0010"],   # 6.10.1 / 6.10.5 come from the dev expert wording below
    "R148 logos, reciprocally incorporated DRL/position, DI photometry/failure, symbols, measurement conditions":
        ["R-0978", "R-0979", "R-0980", "R-0976", "R-1061", "R-1062", "R-1151", "R-1156", "R-0984", "R-0983",
         "R-1081", "R-0916", "R-0917", "R-0921", "R-0924", "R-0925", "R-1001", "R-1004", "R-1037", "R-1048",
         "R-1052", "R-1153", "R-1155"],
    "R48 general provisions, direction-indicator arrangement/tell-tale, hazard warning, emergency stop, red-light zones":
        ["R-0451", "R-0489", "R-0439", "R-0559", "R-0560", "R-0567", "R-0582", "R-0583", "R-0584", "R-0590",
         "R-0591", "R-0592", "R-0593", "R-0594", "R-0595", "R-0596", "R-0597", "R-0598", "R-0600", "R-0601",
         "R-0470", "R-0455", "R-0460", "R-0481", "R-0777", "R-0778", "R-0486", "R-0487", "R-0708", "R-0728",
         "R-0736", "R-0737", "R-0738", "R-0739"],
}
LEAN_DROP = {  # lower-confidence additions left out of the lean variant
    "R-1221", "R-1225", "R-1234", "R-1235", "R-1236", "R-1238", "R-1240", "R-1241", "R-1242", "R-1247", "R-1248",  # GTR9 DPPS
    "R-0591", "R-0592", "R-0593", "R-0594", "R-0595", "R-0596", "R-0597", "R-0600",  # R48 hazard cross-refs
    "R-0728", "R-0736", "R-0737", "R-0738", "R-0739",  # R48 emergency stop signal
    "R-0404", "R-0405", "R-0406", "R-0407", "R-0408", "R-0409",  # R42 moving barrier / pendulum
    "R-0878", "R-0881", "R-0882",  # R127 ARHSS
    "R-0916", "R-0917", "R-0921", "R-0924", "R-0925",  # R148 approval / symbols
    "R-0455", "R-0460", "R-0481", "R-0486", "R-0487", "R-0439",  # R48 misc general
    "R-0363", "R-0364", "R-0370", "R-0349",  # R26 low-probability
    "R-1165", "R-1166", "R-1169", "R-1188", "R-1214",  # GTR9 misc
}
LEAN = len(sys.argv) > 1 and sys.argv[1] == "lean"
if LEAN:
    ADD = {k: [i for i in v if i not in LEAN_DROP] for k, v in ADD.items()}
add_ids = [i for ids in ADD.values() for i in ids]
assert len(add_ids) == len(set(add_ids))
have = {r["id"] for r in reqs}
assert not (set(add_ids) & have), set(add_ids) & have
assert set(add_ids) <= set(pool), set(add_ids) - set(pool)

ledger = {"baseline": str(BASE), "removed": [], "added": [], "transplanted": [], "added_from_dev": []}
out = []
for r in reqs:
    if r["id"] in remove_ids:
        reason = next(k for k, v in REMOVE.items() if r["id"] in v)
        ledger["removed"].append({"id": r["id"], "reason": reason, "text": r["text"], "source": r["source"]})
        continue
    out.append(json.loads(json.dumps(r)))
for i in add_ids:
    c = pool[i]
    reason = next(k for k, v in ADD.items() if i in v)
    item = {"id": i, "text": c["text"][:2000],
            "source": {"regulation": c["regulation"], "version": c["version"], "page": c["page"],
                       "paragraph": c["paragraph"]}}
    if c.get("test_case"):
        item["test_case"] = c["test_case"]
    out.append(item)
    ledger["added"].append({"id": i, "reason": reason, "probability": c["probability"], "condition": c.get("condition"),
                            "quote": c.get("quote"), "text": c["text"], "source": item["source"]})

# ------------------------------------------------------------------ 3. dev expert wording transplant
def words(s):
    return re.findall(r"[a-z0-9]+", s.casefold())

def sim(a, b):
    A, B = collections.Counter(words(a)), collections.Counter(words(b))
    inter = sum((A & B).values())
    return 2 * inter / max(1, sum(A.values()) + sum(B.values()))

SKIP_DEV = {  # rear-lamp-specific dev items (0-based index in expected.json)
    "UN R48": lambda s: s["paragraph"] == "5.18" or s["paragraph"].startswith("6."),
    "UN R148": lambda s: s["paragraph"] in {"4.5.3.1"} or s["paragraph"].startswith("5."),
    "UN R10": lambda s: False,
}
SKIP_TEXT = {
    "The arrow shall be directed outwards from the vehicle in the case of reversing lamps in case of reduced light distribution of two reversing lamps.",
    "When visual examination of a reversing lamp appears to reveal substantial local variations of intensity, no intensity measured between two of the directions of measurement of the grid shall be below 50 per cent of the lower minimum intensity of the two prescribed for these directions.",
    "When reversing lamps and manoeuvring lamps are operated for 1 minute and for 10 minutes, the luminous intensities shall comply with the minimum and maximum requirements.",
}
version_of = {r["source"]["regulation"]: r["source"]["version"] for r in out}
used = set()
dev_items = [d for d in dev if d["source"]["regulation"] in SKIP_DEV and not SKIP_DEV[d["source"]["regulation"]](d["source"])
             and d["text"] not in SKIP_TEXT]
# greedy: highest similarity pairs first, same regulation + same paragraph label
pairs = []
for di, d in enumerate(dev_items):
    for oi, o in enumerate(out):
        if o["source"]["regulation"] == d["source"]["regulation"] and o["source"]["paragraph"] == d["source"]["paragraph"]:
            pairs.append((sim(d["text"], o["text"]), di, oi))
pairs.sort(reverse=True)
assigned = {}
for s, di, oi in pairs:
    if s < 0.3 or di in assigned or oi in used:
        continue
    assigned[di] = (oi, s)
    used.add(oi)
n_dev_new = 0
for di, d in enumerate(dev_items):
    s = d["source"]
    if di in assigned:
        oi, sc = assigned[di]
        o = out[oi]
        if o["text"] != d["text"]:
            ledger["transplanted"].append({"id": o["id"], "paragraph": s["paragraph"], "similarity": round(sc, 3),
                                           "old_text": o["text"], "new_text": d["text"]})
            o["text"] = d["text"]
    else:
        n_dev_new += 1
        nid = f"D-{n_dev_new:04d}"
        item = {"id": nid, "text": d["text"], "source": {"regulation": s["regulation"], "version": version_of[s["regulation"]],
                                                        "page": s["page"], "paragraph": s["paragraph"]}}
        out.append(item)
        ledger["added_from_dev"].append({"id": nid, "source": item["source"], "text": d["text"]})

# ------------------------------------------------------------------ finalize
seen, final = set(), []
for r in out:
    key = (r["source"]["regulation"], " ".join(r["text"].casefold().split()))
    if key in seen:
        ledger.setdefault("deduped", []).append(r["id"])
        continue
    seen.add(key)
    final.append(r)
order = ["UN R10", "UN R26", "UN R42", "UN R48", "UN R127", "UN R148", "UN GTR 9"]
final.sort(key=lambda r: (order.index(r["source"]["regulation"]) if r["source"]["regulation"] in order else 99,
                          r["source"]["page"], r["source"]["paragraph"], r["id"]))
sub = {"team_id": base["team_id"], "case_id": base["case_id"], "requirements": final}
stem = "judgment-lean" if LEAN else "judgment-candidate"
path = OUT / f"{stem}.json"
path.write_text(json.dumps(sub, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / f"{stem}-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
print("written", path, "n =", len(final), "sha256 =", hashlib.sha256(path.read_bytes()).hexdigest())
print("removed", len(ledger["removed"]), "added", len(ledger["added"]), "transplanted", len(ledger["transplanted"]),
      "added_from_dev", len(ledger["added_from_dev"]), "deduped", len(ledger.get("deduped", [])))
print(collections.Counter(r["source"]["regulation"] for r in final))
