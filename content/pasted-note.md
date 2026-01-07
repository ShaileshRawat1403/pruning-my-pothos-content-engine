# AI Agent Factory (Clean Summary)

## Goal
A modular framework that assembles AI agents automatically, using specialized subagents to plan, integrate tools, manage dependencies, and validate outputs.

## Workflow (phases)
1) **Clarify**: capture requirements and constraints.
2) **Plan**: outline tasks and select tools/components.
3) **Parallel build**: specialized subagents handle prompts, tool wiring, and dependency setup.
4) **Implement**: assemble code, configs, and docs.
5) **Validate**: run tests/lints and sanity checks; revise if needed.

## Why this helps
- Faster delivery: parallel subagents cut cycle time.
- Separation of concerns: prompt, tool, and dependency work stay isolated.
- Repeatability: consistent scaffolds and tests per agent.

## Guardrails
- Keep subagent prompts focused; avoid context bleed.
- Enforce tests and linting before packaging.
- Record artifacts and dependencies for traceability.

## Suggested outputs
- Ready-to-run agent folder with README, tests, and example prompts.
- Logs of tool calls and decisions for auditability.
