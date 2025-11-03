#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRAT_DIR = ROOT / "docs" / "examples" / "strategy"

STAGES = [
    STRAT_DIR / "data_preparation",
    STRAT_DIR / "data_analysis",
    STRAT_DIR / "model_selection",
    STRAT_DIR / "model_training",
    STRAT_DIR / "model_evaluation",
    STRAT_DIR / "model_deployment",
]

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def write_text(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def parse_outputs_and_acceptance(step_goal_text: str):
    outputs = []
    acceptance_lines = []
    # OVERALL OUTPUT ARTIFACTS block
    m = re.search(r"OVERALL OUTPUT ARTIFACTS:\n=+\n(?P<body>(?:.*\n)+?)\n=+\nACCEPTANCE", step_goal_text)
    if m:
        body = m.group("body")
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("- "):
                key = line[2:].split(":")[0].strip()
                if key:
                    outputs.append(key)
    # ACCEPTANCE CRITERIA block
    m2 = re.search(r"ACCEPTANCE CRITERIA:\n=+\n(?P<body>(?:.*\n)+?)\n=+\nDSLC ALIGNMENT:", step_goal_text)
    if m2:
        body2 = m2.group("body")
        for line in body2.splitlines():
            line = line.strip()
            if line and not line.startswith(("=","#")):
                acceptance_lines.append(line)
    return outputs, acceptance_lines

def append_task_templates(behavior_path: Path, step_outputs, step_acceptance):
    text = read_text(behavior_path)
    changed = False
    if "TASK TEMPLATE:" not in text:
        tasks = []
        if step_outputs:
            tasks.append(f"Produce/Update artifacts: {', '.join(step_outputs)}")
        tasks.append("Use variables from state (e.g., df_raw/df_cleaned) when available")
        tasks.append("Persist figures under ./outputs/<stage>/<step>/ if applicable")
        task_block = (
            "\n================================================================================\n"
            "TASK TEMPLATE:\n"
            "================================================================================\n"
            "- Describe exact operation with variable/file n (e.g., df_raw, ./outputs/eda/...)\n"
            "- Ensure deterministic seeds and document parameters\n"
            "- " + "\n- ".join(tasks) + "\n"
        )
        text = text.rstrip() + task_block + "\n"
        changed = True
    if step_acceptance and "ACCEPTANCE EXAMPLES:" not in text:
        acc_block = (
            "\n================================================================================\n"
            "ACCEPTANCE EXAMPLES:\n"
            "================================================================================\n"
            "- " + "\n- ".join(step_acceptance) + "\n"
        )
        text = text.rstrip() + acc_block + "\n"
        changed = True
    if changed:
        write_text(behavior_path, text)
    return changed

def ensure_third_behavior(step_dir: Path, step_outputs, step_acceptance):
    behaviors = sorted(step_dir.glob("behavior_*.txt"))
    if len(behaviors) >= 3:
        return False
    target_out = step_outputs[0] if step_outputs else "step_validation_report"
    acc_list = "\n".join(f"- {a}" for a in (step_acceptance or ["所有 Step 产物均非空且可加载"]))
    content = f"""================================================================================
BEHAVIOR AUTO.3: VALIDATION AND ACCEPTANCE (验收与记录)
================================================================================

GOAL: 按 Step 的 ACCEPTANCE CRITERIA 验证产物并记录结果

RECOMMENDED AGENT: PCS-Agent

================================================================================
ACTIONS:
================================================================================

ACTION AUTO.3.1: Collect Artifacts
  收集当前状态中的变量与文件路径

ACTION AUTO.3.2: Validate Against Acceptance
  按 Step 的验收条款逐项验证，失败则输出修复建议

ACTION AUTO.3.3: Record Conclusions
  将结论记录到 {target_out} 或对应报告中

================================================================================
OUTPUT ARTIFACTS:
================================================================================
- {target_out}

================================================================================
DSLC HOOKS:
================================================================================
- Planning → /planning; Generating → /generating; Feedback → /planning

================================================================================
TASK TEMPLATE:
================================================================================
- 遍历 Step 验收项并逐条断言；失败时报出修复建议
- 使用实际变量名（如 df_cleaned/correlation_matrix）与路径（./outputs/...）

================================================================================
ACCEPTANCE EXAMPLES:
================================================================================
{acc_list}
"""
    target = step_dir / "behavior_3_validation_and_acceptance.txt"
    write_text(target, content)
    return True

def main():
    total_changed = 0
    total_added = 0
    for stage_dir in STAGES:
        for step_dir in sorted(stage_dir.glob("step_*")):
            goal = step_dir / "goal.txt"
            if not goal.exists():
                continue
            outputs, acceptance = parse_outputs_and_acceptance(read_text(goal))
            for b in sorted(step_dir.glob("behavior_*.txt")):
                if append_task_templates(b, outputs, acceptance):
                    total_changed += 1
            if ensure_third_behavior(step_dir, outputs, acceptance):
                total_added += 1
    print(f"Enriched {total_changed} behaviors; added {total_added} validation behaviors.")

if __name__ == "__main__":
    main()
