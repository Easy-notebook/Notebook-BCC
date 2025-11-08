#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "examples" / "strategy"

GATES = {
    "data_preparation": [
        "processing_pipeline_doc includes random seeds, library versions, and step parameters",
        "data_quality_report includes sections: missing, outliers, dtypes, indexes",
    ],
    "data_analysis": [
        "correlation_matrix shape matches (n_features x n_features)",
        "at least 6 charts generated under ./outputs/eda/",
    ],
    "model_selection": [
        "≥ 3 distinct model families evaluated (e.g., linear/tree/ensemble)",
        "model_comparison_report includes columns: model, rmse, r2, cv_mean, cv_std, train_time",
    ],
    "model_training": [
        "training_logs include CPU/GPU/memory usage and duration",
        "./models/model.pkl loads successfully without errors",
    ],
    "model_evaluation": [
        "cv_std < target_threshold",
        "perturbation_results include ≥ 5 runs with variance summary",
        "pcs_validation_report contains sections: Predictability, Computability, Stability",
    ],
    "model_deployment": [
        "./outputs/predictions.csv exists and row count matches submit/test set",
        "required columns present (e.g., Id, SalePrice for Ames)",
        "model_card includes metrics, usage, limitations, and monitoring triggers",
    ],
}

STAGES = list(GATES.keys())

def inject_acceptance(step_goal_path: Path, stage: str):
    text = step_goal_path.read_text(encoding="utf-8")
    if "ACCEPTANCE CRITERIA:" not in text:
        return False
    # Find acceptance block
    m = re.search(r"(ACCEPTANCE CRITERIA:\n=+\n)(?P<body>(?:.*\n)*?)(\n=+\nDSLC ALIGNMENT:)", text)
    if not m:
        return False
    head = text[:m.start(1)]
    acc_head = m.group(1)
    body = m.group("body")
    tail = text[m.end(3):]

    # Build PCS-GATE lines not already present
    to_add = []
    for line in GATES.get(stage, []):
        if line not in body:
            to_add.append(f"- {line}\n")

    if not to_add:
        return False

    new_body = body.rstrip() + "\n" + "".join(to_add)
    new_text = head + acc_head + new_body + "\n\n==\nDSLC ALIGNMENT:" + tail
    # Fix accidental '==\n' marker replacement of original '====' bar: keep consistent separators
    new_text = new_text.replace("\n==\nDSLC ALIGNMENT:", "\n================================================================================\nDSLC ALIGNMENT:")
    step_goal_path.write_text(new_text, encoding="utf-8")
    return True

def main():
    changed = 0
    for stage in STAGES:
        stage_dir = BASE / stage
        if not stage_dir.exists():
            continue
        for step_dir in stage_dir.glob("step_*"):
            goal = step_dir / "goal.txt"
            if goal.exists() and inject_acceptance(goal, stage):
                changed += 1
    print(f"PCS-GATE enforced in {changed} steps.")

if __name__ == "__main__":
    main()

