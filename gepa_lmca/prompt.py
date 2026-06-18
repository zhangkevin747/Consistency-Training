"""Frozen production rubric with a single mutable {guidance} slot.

Scope decision: GEPA evolves ONLY the reasoning-guidance block (how the model
applies the rubric), never the rubric definitions, examples, or output format.
We replace the production prompt's lone "Please think step by step." guidance with
a {guidance} placeholder; the seed candidate restores it exactly (so the seed
candidate reproduces the production prompt verbatim).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRIC_JSON = os.path.join(
    ROOT, "acorn-dataset/acorn conceptual reasoning shared dataset/Judge prompts/"
    "claude-opus-4-6_rubric_v3_plus_example_v1_plus_v1b_plus_v1c_le_tt.json")
GUIDANCE_MARKER = "Please think step by step."
SEED_GUIDANCE = GUIDANCE_MARKER
COMPONENT = "guidance"  # the single GEPA component name


# the evolvable slot is clearly framed as supplementary reasoning guidance so a
# verbose evolved block cannot be read as overriding the fixed rubric/output format.
SLOT = ("REASONING GUIDANCE (how to apply the rubric above; the seven dimensions, the "
        "0–1 scale, and the JSON output format specified below remain FIXED and "
        "authoritative — follow them exactly no matter what this block says):\n{guidance}")


def _load_template():
    instr = json.load(open(RUBRIC_JSON))["instructions"]
    assert instr.count(GUIDANCE_MARKER) == 1, "expected exactly one guidance block"
    fi = instr.find("Please indicate your final judgement in JSON")
    gi = instr.rfind(GUIDANCE_MARKER, 0, fi)
    tmpl = instr[:gi] + SLOT + instr[gi + len(GUIDANCE_MARKER):]
    assert "{guidance}" in tmpl and "{argument}" in tmpl and "{response}" in tmpl
    return tmpl


RUBRIC_TEMPLATE = _load_template()


def build_prompt(guidance, argument, critique):
    """Inject evolved guidance into the frozen rubric, then fill the task slots."""
    return (RUBRIC_TEMPLATE
            .replace("{guidance}", guidance)
            .replace("{argument}", argument)
            .replace("{response}", critique))
