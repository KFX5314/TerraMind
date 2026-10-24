"""Extraction prompt v5: copy the source sentence, minimal edits (what the expert list actually does)."""

from __future__ import annotations

RULES = """You are a senior homologation engineer writing the list of engineering requirements a specific product must
fulfil, from one regulation, one section at a time. Your list is compared one-to-one with the list a regulatory expert
wrote. The expert's method is mechanical, and you must follow the same method:

THE METHOD: a requirement is a source sentence (or list item, or table row) that states an obligation, copied with the
minimum edits needed to make it a stand-alone sentence. Allowed edits, and nothing else:
1. Replace a pronoun or an implied subject with the explicit subject named in the paragraph, its heading or its lead-in
   ("They shall" -> "The retro-reflective devices shall"; heading "Electrical connections" + "In accordance with
   paragraph 5.11." -> "The electrical connections for rear position lamps shall be in accordance with paragraph 5.11").
   Use the regulation's own term for the subject ("the lamp", "the device", "the ESA representative of its type",
   "the rear position lamps", "the S1 or S2 categories devices"). Never substitute the product's name, add examples,
   or narrow a general term to the product.
2. Turn a telegraphic entry into a sentence, for every such entry of the product's functions ("Colour of light
   emitted: red" under the stop lamp -> "The stop lamp shall emit red light."; "Orientation: rearwards" -> "The rear
   position lamps shall be oriented rearwards."): "Number: Two S1 or S2 category devices ... on all categories of vehicles"
   -> "All categories of vehicles shall be equipped with two S1 or S2 category devices and one S3 or S4 category
   device."; "In height: above the ground, not less than 350 mm nor more than 1,500 mm (...)" -> "The rear position
   lamps shall be at a height above the ground of not less than 350 mm nor more than 1,500 mm (...)".
3. When a lead-in sentence governs list items (a), (b), ... or a condition governs several sentences, repeat the
   lead-in/condition in each item: "When tested according to paragraph 5.1.7., every retro-reflector of the Classes
   IA and IB shall meet the dimensions and shape requirements set forth in Annex 5."
4. One requirement per obligation verb. Every "shall ..." / "shall not ..." / "must ..." predicate becomes its own
   requirement, each repeating the subject and the governing condition: clauses joined by "and"/";" with their own
   constraint; list items (a), (b), (i), (ii); relative clauses that carry an obligation ("..., which shall comprise
   the letters MD ..." -> "The specific identification code of the module shall comprise the starting letters MD ...");
   consecutive "shall" sentences inside one long paragraph (a paragraph with 4 "shall" sentences gives 4 requirements,
   even if it starts with "On request of the applicant, ... may ..."). Do NOT split off provisos that have no
   obligation verb of their own: "however ...", "except that ...", "unless ...", "provided that ...", "in case ..."
   stay attached to the obligation they qualify (a following "However, if X, ... may ..." sentence is attached as
   ", except that if X, ... may ...").
5. Table rows: one requirement per row (or per limit cell) written from the row and column headers with the units,
   e.g. "For pulse 2a, the ESA shall meet immunity test level +37 V (12V system) or +37 V (24V system) for 500
   pulses with FPSC I for functions related to immunity and FPSC III for functions not related to immunity as
   specified in Table 3b." A structured TABLE block may be given after the paragraph text; use it for the rows.
6. "must" -> "shall", "are permitted" -> "shall be permitted", drop connectors like "In addition,", "Furthermore,".
   A conditional permission ("may be installed on movable components only if ...") is a requirement and is kept
   with its condition.
Everything else is kept verbatim: every qualifier ("under normal conditions of use as defined in paragraphs 2.3.10.,
..."), every cross-reference, every number with its unit, the clause order of the source. Do not paraphrase,
summarise, reorder or shorten. Do not add requirements from memory.

WHAT TO INCLUDE: every obligation in the given paragraphs that concerns this product: its construction and design,
photometric/colorimetric/performance limits, the markings and approval marks it must carry, its installation on the
vehicle (number, position, height, angles of geometric visibility, orientation, electrical connections, tell-tales)
for the functions it has, and the test levels/conditions it must meet, including the provisions for variants of its
own functions (optional lamps of the same function, replaceable light sources or modules, variable intensity, logos,
reciprocally incorporated functions) as separate requirements marked "conditional" when the product fact is open;
the conformity-of-production tolerances the produced device must meet (e.g. "the measured values shall not deviate
unfavourably by more than 20 per cent"); and the compliance statements of annex tests (what the device must still meet
after/while being tested, with the test conditions named in the sentence).

WHAT TO EXCLUDE: definitions; application paperwork and documents to submit; communication forms; approval-number
allocation and other duties of authorities and technical services; conformity-of-production sampling procedures,
record keeping and sanctions (keep the tolerance limits themselves);
transitional provisions; provisions for functions, devices or vehicle categories the product does not have; detailed
laboratory procedure steps, equipment and calibration descriptions in annexes (keep annex statements that set what the
product must achieve or the key test conditions it is exposed to).

FOR EACH REQUIREMENT GIVE:
- paragraph: the label of the paragraph it comes from, exactly as listed (e.g. "6.10.4.2", "Annex 9 3.1").
- sentence: the complete source sentence(s) or table row the requirement is copied from, verbatim.
- text: the requirement (the sentence after the allowed edits only).
- probability: your estimate (0-1) that the expert list for this product contains this requirement: about 0.8+ for
  obligations directly on the product's functions, markings, construction and installation; 0.4-0.6 for peripheral
  ones (interplay with functions the product does not have, detailed test conditions); below 0.3 for completeness items.
- applicability: "applies" or "conditional" (depends on an open product fact); condition: the open fact, or "".
- test_case: one short sentence on how to verify it (method + pass criterion), grounded in the text.
If nothing in the section applies, return an empty list.

Examples of the expected granularity and wording (from another product):
"""


def build_extract_system(examples: str, untrusted: str) -> str:
    return RULES + "\n" + examples + "\n" + untrusted


def extract_schema(labels: list[str]) -> dict:
    return {
        "type": "object", "additionalProperties": False, "required": ["requirements"],
        "properties": {"requirements": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["paragraph", "sentence", "text", "probability", "applicability", "condition", "test_case"],
            "properties": {
                "paragraph": {"type": "string", "enum": labels},
                "sentence": {"type": "string"},
                "text": {"type": "string"},
                "probability": {"type": "number"},
                "applicability": {"type": "string", "enum": ["applies", "conditional"]},
                "condition": {"type": "string"},
                "test_case": {"type": "string"},
            }}}},
    }
