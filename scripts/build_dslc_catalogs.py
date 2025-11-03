#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "examples" / "strategy"
OUT = BASE / "prompts"

STAGES = [
    "data_preparation",
    "data_analysis",
    "model_selection",
    "model_training",
    "model_evaluation",
    "model_deployment",
]

def extract(title_path: Path):
    text = title_path.read_text(encoding="utf-8")
    # Extract GOAL
    m_goal = re.search(r"GOAL:\s*(.*)\n", text)
    goal = m_goal.group(1).strip() if m_goal else ""
    # Extract OVERALL OUTPUT ARTIFACTS
    outputs = []
    m_out = re.search(r"OVERALL OUTPUT ARTIFACTS:\n=+\n(?P<body>(?:.*\n)+?)\n=+\nACCEPTANCE", text)
    if m_out:
        body = m_out.group("body")
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("- "):
                outputs.append(line[2:])
    # Extract ACCEPTANCE CRITERIA
    acceptance = []
    m_acc = re.search(r"ACCEPTANCE CRITERIA:\n=+\n(?P<body>(?:.*\n)+?)\n=+\nDSLC ALIGNMENT:", text)
    if m_acc:
        body = m_acc.group("body")
        for line in body.splitlines():
            line = line.strip()
            if line and not line.startswith("="):
                acceptance.append(line)
    return goal, outputs, acceptance

def build_catalog(stage: str):
    stage_dir = BASE / stage
    if not stage_dir.exists():
        return None
    lines = [f"# {stage} Step Catalog\n"]
    for step_dir in sorted(stage_dir.glob("step_*")):
        goal_file = step_dir / "goal.txt"
        if not goal_file.exists():
            continue
        goal, outputs, acceptance = extract(goal_file)
        lines.append(f"## {step_dir.name}\n")
        lines.append(f"Goal: {goal}\n")
        if outputs:
            lines.append("Verified Artifacts:")
            for o in outputs:
                lines.append(f"- {o}")
        if acceptance:
            lines.append("Acceptance:")
            for a in acceptance:
                lines.append(f"- {a}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stage in STAGES:
        content = build_catalog(stage)
        if content:
            (OUT / f"{stage}_catalog.txt").write_text(content, encoding="utf-8")
    print(f"Catalogs written to {OUT}")

if __name__ == "__main__":
    main()

