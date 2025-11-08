#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "examples" / "strategy"

STAGES = [
    "data_preparation",
    "data_analysis",
    "model_selection",
    "model_training",
    "model_evaluation",
    "model_deployment",
]

CN_RE = re.compile(r"[\u4e00-\u9fff]")

def strip_cn_parentheses(line: str) -> str:
    # remove (...) if contains Chinese, including full-width parentheses
    def repl(m):
        inside = m.group(1)
        return "" if CN_RE.search(inside) else f"({inside})"
    # handle both () and （）
    line = re.sub(r"\(([^)]*)\)", repl, line)
    line = re.sub(r"（([^）]*)）", repl, line)
    return line

def normalize_supervision(line: str) -> str:
    line = line.replace("（监督）", "(oversight)")
    line = line.replace("监督", "oversight")
    line = line.replace("PCS-Agent 监督", "PCS-Agent oversight")
    return line

def english_goal(line: str) -> str:
    # If GOAL line contains Chinese, replace with a generic English directive
    if line.strip().startswith("GOAL:") and CN_RE.search(line):
        return "GOAL: See TASK TEMPLATE and ACTIONS; produce required artifacts and meet acceptance.\n"
    return line

def replace_pcs_considerations(line: str) -> str:
    if line.strip().startswith("- Predictability:") and CN_RE.search(line):
        return "- Predictability: Ensure generalization to unseen data.\n"
    if line.strip().startswith("- Computability:") and CN_RE.search(line):
        return "- Computability: Ensure reproducibility and resource feasibility.\n"
    if line.strip().startswith("- Stability:") and CN_RE.search(line):
        return "- Stability: Ensure robustness under reasonable perturbations.\n"
    return line

def cleanup_output_artifacts(line: str) -> str:
    # For lines like "- key: 中文..." keep only key if value contains Chinese
    if line.strip().startswith("- ") and ":" in line:
        key, val = line.split(":", 1)
        if CN_RE.search(val):
            return key.strip() + "\n"
    return line

def cleanup_actions_bullets(line: str, in_actions: bool) -> str:
    if in_actions and line.strip().startswith("-") and CN_RE.search(line):
        return "- See TASK TEMPLATE above for specifics.\n"
    return line

def cleanup_acceptance_examples(lines: list[str], i: int) -> int:
    # If we are in ACCEPTANCE EXAMPLES block, and body has Chinese, replace body with generic English
    if lines[i].strip().startswith("ACCEPTANCE EXAMPLES:"):
        j = i + 1
        body_has_cn = False
        while j < len(lines) and not lines[j].startswith("===") and not lines[j].strip().startswith("DSLC") and not lines[j].strip().startswith("TASK TEMPLATE:") and not lines[j].strip().startswith("OUTPUT ARTIFACTS:") and not lines[j].strip().startswith("ACTIONS:"):
            if CN_RE.search(lines[j]):
                body_has_cn = True
            j += 1
        if body_has_cn:
            # Replace the block between i+1 and j with a single generic line
            lines[i+1:j] = ["- Follow the step-level Acceptance Criteria for this step's verified artifacts.\n"]
        return j
    return i + 1

def process_file(p: Path) -> bool:
    text = p.read_text(encoding="utf-8")
    orig = text
    # line-wise transforms
    lines = text.splitlines(keepends=True)
    out = []
    in_actions = False
    def replace_common_phrases(s: str) -> str:
        repl = {
            # Acceptance and general phrases
            "且行数与测试集一致": "and row count matches the test set",
            "且行数与测试/提交集一致": "and row count matches the test/submit set",
            "与 测试/提交集一致": "matches the test/submit set",
            "行数与测试/提交集一致": "row count matches the test/submit set",
            "行数与测试集一致": "row count matches the test set",
            "已生成且非空": "exist and are non-empty",
            "已生成": "exist",
            "记录关键处理": "documents key processing",
            "至少 2–3 个不同类型的基线训练与评估完成": "At least 2–3 different baseline types were trained and evaluated",
            "输出扰动设计、结果与稳定性结论": "Provide perturbation design, results, and stability conclusion",
            "输出包含是否需要对数/Box-Cox 等建议与理由": "State whether log/Box‑Cox transforms are recommended and why",
            "管道在训练/验证分离下工作；无目标泄露": "Pipeline fits on training folds and applies to validation folds; no target leakage",
            "df_outlier_processed 的异常指标显著减少": "Outlier indicators in df_outlier_processed are significantly reduced",
            "integrity_check_plan 与 quality_audit_report 均已生成且非空": "integrity_check_plan and quality_audit_report exist and are non-empty",
            "自动化校验脚本可运行并输出通过/失败摘要": "Automated validation scripts run and output pass/fail summary",
            # Validation-and-acceptance behavior phrases
            "收集当前状态中的变量与文件路径": "Collect variables and file paths from the current state",
            "按 Step 的验收条款逐项验证，失败则输出修复建议": "Validate against step acceptance items; on failure, emit remediation suggestions",
            "将结论记录到": "Record conclusions to",
            "或对应报告中": "or the corresponding report",
            "遍历 Step 验收项并逐条断言；失败时报出修复建议": "Iterate acceptance items and assert them; on failure, emit remediation suggestions",
            "使用实际变量名与路径": "Use real variable n and paths",
            "训练日志完整、模型可加载": "Training logs complete; models load successfully",
            "eda_summary、variable_profiles": "eda_summary and variable_profiles",
            "缺失模式与机制分析": "Analyze missingness patterns and mechanisms",
            "执行合适的填充/删除策略": "Apply appropriate imputation/deletion strategies",
            "model_card 包含指标/使用/限制; deployment_report 含示例与依赖": "model_card includes metrics/usage/limitations; deployment_report includes examples and dependencies",
            # Additional phrases
            "统计行列数/文件大小/表数量": "Summarize row/column counts, file sizes, and table counts",
            "验证读取权限、路径稳定性与合规标签": "Validate read permissions, path stability, and compliance labels",
            "data_inventory_report 记录的行列数与实际加载一致": "Row/column counts in data_inventory_report match the actually loaded dataset",
            "维度完整性、索引/外键、记录一致性": "Dimensional integrity; index/foreign keys; record consistency",
            "类型/范围/正则与 schema 验证": "Type/range/regex and schema validation",
            "输出均值/方差与置信估计; 记录随机种子": "Output means/variances and confidence estimates; record random seeds",
            "给出 ≥2 类不同算法的适配分析与取舍理由": "Provide analysis and trade-offs for ≥ 2 algorithm families",
            "correlation_matrix 维度与变量数一致; top_correlated_variables 非空": "correlation_matrix dimensions match variable count; top_correlated_variables is non-empty",
            "测试 ≥3 个模型; 输出 selected_model_name 与充分理由": "Test ≥ 3 models; output selected_model_name with rationale",
            "输出主要指标(RMSE/R²/MAE)与误差分布": "Output core metrics (RMSE/R²/MAE) and error distribution",
            "dr_projection 生成成功; cluster_summary 含簇内/簇间统计": "dr_projection generated successfully; cluster_summary includes within/between-cluster statistics",
            "创建 ./outputs/ 目录": "Create ./outputs/ directory (if not present)",
            "将 df_cleaned 保存为 ./outputs/df_cleaned.csv": "Save df_cleaned as ./outputs/df_cleaned.csv",
            "在 processing_pipeline_doc 增记保存路径与行列数": "Append save path and shape to processing_pipeline_doc",
            " 非空": " non-empty",
            " 均": " ",
            " 使用 ": " use ",
            " 指定 ": " specifying ",
            " 与": " and",
            "与": " and",
            "或 满足“剩余缺失列清单+业务豁免”": "OR meets \"remaining-missing columns list + business exemptions\"",
            "“剩余缺失列清单+业务豁免”": "\"remaining-missing columns list + business exemptions\"",
            "andCV": "and CV",
            "维度 and测试集一致": "dimensions match the test set",
            "and测试集一致": "match the test set",
            "读取": "read",
            "列名非空且数量>1": "column n non-empty and count>1",
            "校验 ": "Validate ",
            "列举候选来源/接口 and权限": "Enumerate candidate sources, interfaces, and permissions",
            "列举候选来源": "Enumerate candidate sources",
            "权限": "permissions",
            "参数": "parameters",
            "建议": "recommendations",
            "CV结果": "CV results",
            "包含指标/使用/限制": "includes metrics/usage/limitations",
            "含示例与依赖": "includes examples and dependencies",
            "无缺失/NaN": "no missing/NaN",
            "从 state.variables 解析 file_path": "Resolve file_path from state.variables",
            "推断策略": "inference policy",
            "记录形状到": "log shape to ",
            "明确来源/接口/刷新策略并完成获取": "Define sources/interfaces/refresh strategy and complete acquisition",
            "合规性": "compliance",
            " 生成成功": " generated successfully",
            "andparameters": " and parameters",
            " andrecommendations": " and recommendations",
            "且可加载": "and loads successfully",
            "- 缺失模式与机制分析": "- Analyze missingness patterns and mechanisms",
            "- 执行合适的填充/删除策略": "- Apply appropriate imputation/deletion strategies",
            "列举候选来源/接口": "Enumerate candidate sources/interfaces",
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        # replace Chinese punctuation
        s = s.replace("；", "; ").replace("，", ", ")
        s = s.replace("。", ". ")
        s = s.replace("、", "/")
        # specific whole-line fixes
        s = s.replace("使用 pandas 读取, 指定 encoding、dtype 推断策略与 na_values", "Read with pandas, specifying encoding, dtype inference policy, and na_values")
        return s

    for i, line in enumerate(lines):
        line = normalize_supervision(line)
        line = strip_cn_parentheses(line)
        line = english_goal(line)
        line = replace_pcs_considerations(line)
        line = replace_common_phrases(line)
        # track ACTIONS block
        if line.strip() == "ACTIONS:" or line.strip() == "ACTIONS:\n":
            in_actions = True
        if line.strip().startswith("OUTPUT ARTIFACTS:"):
            in_actions = False
        if line.strip().startswith("DSLC HOOKS:") or line.strip().startswith("ACCEPTANCE:") or line.strip().startswith("TASK TEMPLATE:"):
            in_actions = False
        # cleanup bullets with CN inside actions
        line = cleanup_actions_bullets(line, in_actions)
        # cleanup output artifacts colon Chinese descriptions
        line = cleanup_output_artifacts(line)
        out.append(line)

    # second pass for acceptance examples blocks
    i = 0
    while i < len(out):
        prev_i = i
        i = cleanup_acceptance_examples(out, i)
        if i == prev_i:
            i += 1

    text = "".join(out)
    changed = text != orig
    if changed:
        p.write_text(text, encoding="utf-8")
    return changed

def main():
    changed_count = 0
    targets = []
    for stage in STAGES:
        for p in (BASE / stage).rglob("*.txt"):
            targets.append(p)
    for p in targets:
        if process_file(p):
            changed_count += 1
    print(f"Englishified {changed_count} files under DSLC strategy.")

if __name__ == "__main__":
    main()
