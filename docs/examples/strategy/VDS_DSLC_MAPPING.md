# VDS × DSLC Mapping (Strategy Directory)

## Overview

This document maps DSLC stages in `docs/examples/strategy` to the VDSAgents roles and highlights the PCS (Predictability-Computability-Stability) emphasis per stage. Use this as a quick reference when wiring strategy steps to the DSLC APIs (`/planning`, `/generating`).

## Stage → Agent Mapping

1) Stage 1: Data Existence Establishment (数据存在性建立)
- Primary Agent: Define-Agent
- Supporting: PCS-Agent (oversight)
- PCS Emphasis: Computability (sources/formats), Stability (provenance), Predictability (signal presence)

2) Stage 2: Data Integrity Assurance (数据完整性保证)
- Primary Agent: Explore-Agent
- Supporting: PCS-Agent (oversight)
- PCS Emphasis: Stability (quality invariants), Computability (clean pipelines)

3) Stage 3: Exploratory Data Analysis (探索性数据分析)
- Primary Agent: Explore-Agent
- Supporting: PCS-Agent (oversight)
- PCS Emphasis: Predictability (signal discovery), Stability (robust insights)

4) Stage 4: Methodology Strategy Formulation (方法策略制定)
- Primary Agent: Model-Agent
- Supporting: Define-Agent, Evaluate-Agent, PCS-Agent
- PCS Emphasis: Predictability (method validity), Computability (feasibility)

5) Stage 5: Model Implementation Execution (模型实施执行)
- Primary Agent: Model-Agent
- Supporting: PCS-Agent
- PCS Emphasis: Computability (scalable training), Stability (reproducible runs)

6) Stage 6: Predictability Validation (可预测性验证)
- Primary Agent: Evaluate-Agent
- Supporting: PCS-Agent
- PCS Emphasis: Predictability (core), Stability (consistent metrics)

7) Stage 7: Stability Assessment (稳定性评估)
- Primary Agent: PCS-Agent
- Supporting: Evaluate-Agent, Model-Agent
- PCS Emphasis: Stability (core), Predictability (under perturbation)

8) Stage 8: Results Communication (结果传达)
- Primary Agent: Define-Agent, Evaluate-Agent
- Supporting: PCS-Agent
- PCS Emphasis: Stability (faithful reporting), Predictability (business value)

## DSLC API Hooks (per Step/Behavior)

- Planning First: POST `/planning` before entering a Step/Behavior to check goals.
- Generate Actions: POST `/generating` to fetch the next Actions for the current Behavior.
- Feedback Loop: POST `/planning` after Actions to evaluate completion and decide next.
- Details: see `docs/API_PROTOCOL.md`.

## Configuration (runtime)

- DSLC URL: `Config.set_dslc_url("http://localhost:28600")`
- Default Endpoints:
  - Planning: `http://localhost:28600/planning`
  - Generating: `http://localhost:28600/generating`

## Usage Notes

- In each Behavior file, “RECOMMENDED AGENT” should reflect the Primary Agent above; add “PCS-Agent 监督” where applicable.
- In each Step `goal.txt`, include PCS considerations and optionally list “DSLC ALIGNMENT” with Primary/Supporting Agents and API hooks.
- For large edits, prefer consistent, minimal wording to keep prompt tokens efficient.

