# Hermes Empirical Validation Analysis (E1–E8)

> **Hermes version**: 0.14.0 (2026.5.16) · upstream 186bf25c
> **Model**: glm-5.1 (Nous Research)
> **Date**: 2026-05-24
> **Transcripts**: `validation/transcripts/`

## Summary

All 8 experiments completed successfully. Hermes reliably emits `###HMP/1` completion markers when instructed. Key findings confirm the design decisions in our marker parser (`MARKER_REGEX`).

---

## E1 — TUI Capture Strategy

**Question**: Does `tmux capture-pane -p -S -1000` reliably capture agent output including completion markers?

**Result**: YES. Extended scrollback (`-S -1000`) captures the full TUI including status bar, prompt, and all agent output. Standard capture (`-S -200`) misses older output but captures recent turns.

**Design implication**: Use `-S -1000` as default scrollback for the `captureTmuxPane()` function. This is safe because Hermes output per session rarely exceeds 1000 lines between polls.

---

## E2 — Marker Compliance (5/5 = 100%)

**Question**: Does Hermes reliably emit `###HMP/1 DONE <uuid> <summary>` when instructed?

**Iterations**: 5 sequential dispatch → completion cycles

| Iteration | Compliant | Notes |
|-----------|-----------|-------|
| 1         | YES       | Clean emission, 31s response time |
| 2         | YES       | Consistent format |
| 3         | YES       | Consistent format |
| 4         | YES       | Consistent format |
| 5         | YES       | Consistent format |

**Rate**: 5/5 = **100% compliance**

**Design implication**: Marker regex can be trusted. Hermes follows the protocol reliably when the instruction includes the exact format.

---

## E3 — Marker Placement

**Question**: Where does Hermes place the marker in the output?

**Result**: ALL 5 markers had **leading whitespace** (not at column 0, not mid-line).

| Placement     | Count |
|---------------|-------|
| Column 0      | 0     |
| Leading WS    | 5     |
| Mid-line      | 0     |

**Design implication**: `MARKER_REGEX` must tolerate leading whitespace. The regex `^\s{0,4}###HMP/1...` handles this correctly. The whitespace appears to come from Hermes' TUI formatting (the response panel has left padding).

---

## E4 — Multi-Task Session Behavior

**Question**: After completing one task, does the session return to a recognizable idle state for the next dispatch?

**Result**: YES. After each completion, the session returns to the prompt (`❯`), ready for the next command. Multiple sequential tasks in the same session work correctly.

**Design implication**: A single Hermes session can handle sequential tasks. No need to restart sessions between tasks.

---

## E5 — Idle Behavior

**Question**: What does a Hermes session look like when idle (no active task)?

**Observation**: 6 ticks over 60 seconds. The idle session shows:
- Status bar: ` ⚕ glm-5.1 │ 23.8K/200K │ [█░░░░░░░░░] 12% │ 3m │ ⏲ 3s`
- Empty prompt: `❯`
- No spontaneous output

**Design implication**: Idle sessions produce no noise. Polling an idle session will not generate false marker matches.

---

## E6 — Long-Task Interruption

**Question**: What happens if we capture output while a task is still in progress?

**Result**: Mid-task output does NOT contain completion markers. Partial output shows tool calls and streaming text, but no `###HMP/1` lines appear until the task is actually done.

**Design implication**: No risk of premature marker detection during long-running tasks.

---

## E7 — Memory and Skill Invocation

**Question**: Does invoking memory/skills during a task interfere with marker emission?

**Result**: NO. Tasks that use memory or skills still emit markers correctly upon completion.

**Design implication**: Marker detection is robust regardless of the tools the agent uses during task execution.

---

## E8 — Failure Case / Blocker Emission

**Question**: Can we instruct Hermes to emit `###HMP/1 BLOCKED` when it can't complete a task?

**Result**: YES. When given an impossible task and instructed to emit `BLOCKED`, Hermes correctly emits `###HMP/1 BLOCKED <uuid> <reason>`.

**Design implication**: Both `DONE` and `BLOCKED` marker types are supported in the protocol.

---

## Protocol Design Decisions (Confirmed by Validation)

1. **Marker format**: `###HMP/1 (DONE|BLOCKED) <uuid> <summary>` — reliable
2. **Leading whitespace**: Tolerate up to 4 chars in regex
3. **Scrollback**: 1000 lines is sufficient
4. **Polling interval**: 10s is safe (Hermes response time: ~30s per task)
5. **Session reuse**: One session can handle sequential tasks
6. **No false positives**: Idle or mid-task output never triggers markers

## Risks

1. **Model-dependent**: Compliance tested with glm-5.1 only. Other models may format differently.
2. **Instruction sensitivity**: If the dispatch template is altered, compliance may drop.
3. **Whitespace variance**: E3 showed consistent leading WS, but this could change with TUI updates.
