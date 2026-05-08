# AI Resume Document

> **For:** Fresh Claude session / Codex / any LLM with zero prior context  
> **Generated:** {{DATE}} at {{PCT}}% context ({{TOKENS}}/{{WINDOW}} tokens)  
> **Original session:** {{SESSION_ID}} on {{MODEL}}

---

## What This Project Is

**Name:** {{PROJECT_NAME}}  
**Path:** `{{PROJECT_PATH}}`  
**One-line purpose:** {{PROJECT_ONE_LINER}}

**Tech stack:**
```
{{TECH_STACK}}
```

**Start the dev environment:**
```bash
{{DEV_START_COMMANDS}}
```

---

## Exact Stopping Point

**Task in progress:** {{CURRENT_TASK}}  
**Last file touched:** `{{LAST_FILE}}` (around line {{LAST_LINE}})  
**Work state:** {{WORK_STATE}}  <!-- e.g. "half-implemented", "tests written but failing", "PR open" -->

**Last git commit:**
```
{{LAST_COMMIT}}
```

**Uncommitted changes:**
```
{{GIT_STATUS}}
```

---

## Architecture — Must Know Before Touching Code

<!-- Things that are NOT obvious from reading the code. Implicit decisions, constraints, invariants. -->

{{ARCHITECTURE_NOTES}}

---

## Read These Files First

_In order of importance:_

1. `{{FILE_1}}` — {{WHY_1}}
2. `{{FILE_2}}` — {{WHY_2}}
3. `{{FILE_3}}` — {{WHY_3}}

---

## Active / In-Progress Work

<!-- What's half-done. What needs to be completed before this is shippable. -->

{{IN_PROGRESS_WORK}}

---

## Do NOT Do This

<!-- Dead ends, wrong approaches, explicit decisions. Save the next AI from repeating failures. -->

| Approach | Why Not |
|----------|---------|
{{DO_NOT_DO_TABLE}}

---

## Full Task Queue

_Pick up from top:_

- [ ] **NOW:** {{TASK_IMMEDIATE}}
- [ ] {{TASK_2}}
- [ ] {{TASK_3}}
- [ ] {{TASK_4}}

---

## Key Patterns in This Codebase

<!-- Conventions that must be followed. Not style — things that will break if done differently. -->

{{KEY_PATTERNS}}

---

## External Dependencies / APIs

{{EXTERNAL_DEPS}}

---

## Verification — How to Know It Works

```bash
{{VERIFY_COMMANDS}}
```
