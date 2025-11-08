#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATEGY_DIR = ROOT / "docs" / "examples" / "strategy"

STAGE_AGENT = {
    1: ("Define-Agent", ["PCS-Agent"]),
    2: ("Explore-Agent", ["PCS-Agent"]),
    3: ("Explore-Agent", ["PCS-Agent"]),
    4: ("Model-Agent", ["Define-Agent", "Evaluate-Agent", "PCS-Agent"]),
    5: ("Model-Agent", ["PCS-Agent"]),
    6: ("Evaluate-Agent", ["PCS-Agent"]),
    7: ("PCS-Agent", ["Evaluate-Agent", "Model-Agent"]),
    8: ("Define-Agent", ["Evaluate-Agent", "PCS-Agent"]),
}

DSLC_HOOKS_BLOCK = (
    "\n" +
    "================================================================================\n" +
    "DSLC HOOKS:\n" +
    "================================================================================\n" +
    "- Planning First → /planning（进入 Step/Behavior 前）\n" +
    "- Generating → /generating（执行行为时）\n" +
    "- Feedback → /planning（行为完成后目标检查）\n"
)

ACCEPTANCE_BLOCK = (
    "\n" +
    "================================================================================\n" +
    "ACCEPTANCE CRITERIA:\n" +
    "================================================================================\n" +
    "- 所有 OVERALL OUTPUT ARTIFACTS 中列出的工件均已生成且非空\n" +
    "- 工件格式/结构满足该 Step 目标描述的最低要求\n"
)

def infer_stage_agent(stage_dir: Path):
    m = re.search(r"stage_(\d+)_", stage_dir.name)
    if not m:
        return "Define-Agent", ["PCS-Agent"]
    idx = int(m.group(1))
    return STAGE_AGENT.get(idx, ("Define-Agent", ["PCS-Agent"]))

def ensure_behavior_agent_and_hooks(path: Path, primary: str, supporting: list[str]):
    text = path.read_text(encoding="utf-8")

    # Skip non-behavior files
    if not path.name.startswith("behavior_"):
        return False

    changed = False
    # Ensure RECOMMENDED AGENT block exists
    if "RECOMMENDED AGENT:" not in text:
        # Insert after GOAL block if possible, else after header
        insert_pos = -1
        goal_idx = text.find("GOAL:")
        if goal_idx != -1:
            # find the next separator line or ACTIONS
            actions_idx = text.find("ACTIONS:", goal_idx)
            insert_pos = actions_idx if actions_idx != -1 else goal_idx
        else:
            insert_pos = 0
        agent_block = (
            "\nRECOMMENDED AGENT: " + primary + (" (PCS-Agent 监督)" if "PCS-Agent" in supporting and primary != "PCS-Agent" else "") + "\n"
        )
        text = text[:insert_pos] + agent_block + text[insert_pos:]
        changed = True

    # Ensure DSLC HOOKS present
    if "DSLC HOOKS:" not in text:
        text = text.rstrip() + DSLC_HOOKS_BLOCK + "\n"
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed

def ensure_step_acceptance_and_alignment(path: Path, primary: str, supporting: list[str]):
    text = path.read_text(encoding="utf-8")
    if path.name != "goal.txt":
        return False
    changed = False
    # Append Acceptance criteria if missing
    if "ACCEPTANCE CRITERIA:" not in text:
        text = text.rstrip() + ACCEPTANCE_BLOCK + "\n"
        changed = True
    # Append DSLC ALIGNMENT if missing
    if "DSLC ALIGNMENT:" not in text:
        align_block = (
            "\n" +
            "================================================================================\n" +
            "DSLC ALIGNMENT:\n" +
            "================================================================================\n" +
            f"- Primary Agent: {primary}\n" +
            (f"- Supporting Agents: {', '.join(supporting)}\n" if supporting else "") +
            "- DSLC Hooks:\n" +
            "  - Planning First: POST /planning（进入 Step/Behavior 前）\n" +
            "  - Action Generation: POST /generating（执行行为时）\n" +
            "  - Feedback Loop: POST /planning（行为完成后目标检查）\n"
        )
        text = text.rstrip() + align_block + "\n"
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed

def main():
    files_changed = 0
    for stage_dir in sorted((STRATEGY_DIR).glob("stage_*")):
        if not stage_dir.is_dir():
            continue
        primary, supporting = infer_stage_agent(stage_dir)
        for p in stage_dir.rglob("*.txt"):
            if p.name.startswith("behavior_"):
                if ensure_behavior_agent_and_hooks(p, primary, supporting):
                    files_changed += 1
            elif p.name == "goal.txt":
                if ensure_step_acceptance_and_alignment(p, primary, supporting):
                    files_changed += 1
    print(f"Updated {files_changed} files under {STRATEGY_DIR}")

if __name__ == "__main__":
    main()

