# Session Summary

**Date:** {{DATE}}  
**Session ID:** {{SESSION_ID}}  
**Model:** {{MODEL}}  
**Plan:** {{PLAN}}  
**Context at save:** {{PCT}}% — {{TOKENS}}/{{WINDOW}} tokens  
**Trigger:** {{TRIGGER}} (threshold was {{THRESHOLD}}%)

---

## What Was Accomplished

<!-- Be specific. Not "worked on auth" but "fixed JWT expiry check in middleware.ts:84 — was using < instead of <=" -->

{{SUMMARY_BULLETS}}

---

## Architectural / Design Decisions

<!-- Decisions that aren't obvious from reading the code. WHY, not WHAT. -->

{{DECISIONS}}

---

## Files Changed This Session

```
{{GIT_DIFF_STAT}}
```

**Commits made:**
```
{{GIT_LOG}}
```

---

## Bugs Fixed

| Bug | Root Cause | Fix Location |
|-----|-----------|--------------|
{{BUGS_TABLE}}

---

## What Failed / Dead Ends

<!-- Critical for the next session — saves re-trying bad approaches -->

{{DEAD_ENDS}}

---

## State of the Codebase at Save

<!-- Is it broken? Tests passing? Build passing? Anything half-done? -->

{{CODEBASE_STATE}}
