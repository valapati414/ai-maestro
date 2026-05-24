# Hermes-Maestro Protocol (HMP/1)

> The wire protocol for autonomous task dispatch between Hermes Maestro
> and Hermes agent workers.

## Protocol Version

**HMP/1** — Hermes-Maestro Protocol, version 1.

## Overview

HMP/1 defines the contract between the Hermes Maestro orchestration layer and
Hermes worker agents. The protocol has two phases:

1. **Dispatch** — The orchestrator sends a structured task envelope to the worker
   via the existing Maestro message pipeline (AMP message -> tmux send-keys).
2. **Completion** — The worker emits a marker string in its terminal output.
   The orchestrator detects the marker by polling `tmux capture-pane`.

## Dispatch Envelope

When a task is dispatched, the worker receives a message in this format:

```
[HMP/1 DISPATCH]
Task-Id: <uuid>
Team: <team name>
Priority: <integer>
Subject: <single line>

<task description, possibly multi-line>

[TEAM RULES]
<team.instructions, verbatim>

[COMPLETION]
When you have completed this task, output exactly one line at the start
of a line in this format:

    ###HMP/1 DONE <task_id> <one-paragraph summary>

If you cannot complete the task and become blocked, output:

    ###HMP/1 BLOCKED <task_id> <one-sentence blocker>

Begin work on the task now.
```

### Dispatch Fields

| Field | Required | Description |
|---|---|---|
| Task-Id | Yes | UUID of the task |
| Team | Yes | Name of the team |
| Priority | Yes | Integer priority (0 = highest) |
| Subject | Yes | Single-line task title |
| (body) | No | Multi-line task description |
| TEAM RULES | No | Team-level instructions if set |

## Completion Markers

### DONE Marker

```
###HMP/1 DONE <task-uuid> <summary text>
```

- Emitted when the worker has successfully completed the task.
- `<task-uuid>` must match the dispatched Task-Id.
- `<summary text>` is a free-text one-paragraph summary of what was done.

### BLOCKED Marker

```
###HMP/1 BLOCKED <task-uuid> <blocker description>
```

- Emitted when the worker cannot complete the task.
- The task transitions back to `backlog` with the blocker description appended.

## Marker Detection

### Regex (Default)

```
^###HMP\/1\s+(DONE|BLOCKED)\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+(.+)$
```

### Detection Strategy

The orchestrator polls tmux pane output on a configurable interval (default: 10s).
Captured text is processed per-line after stripping ANSI escape codes.

Deduplication: each detected marker is tracked by `(taskId, lineHash)` to prevent
the same marker from being processed twice.

### Placement Rules

Based on empirical validation (see `validation/analysis/`):

- Markers MUST appear at the start of a new line (column 0 or with leading whitespace).
- The regex tolerates up to 4 characters of leading whitespace.
- Markers embedded mid-line or inside code blocks are NOT matched.

## Worker Eligibility

A worker is eligible for dispatch when ALL of the following are true:

1. The agent is listed in the team's `orchestration.workers` config.
2. The agent's `program` field equals `"hermes"` (v1 only supports Hermes).
3. The agent's primary session (`sessions[0]`) has `status === 'online'`.
4. The agent is NOT currently assigned to any `in_progress` task.

## Task State Transitions

```
                    ┌─────────────────────────────┐
                    │         backlog              │
                    └──────┬──────────────────────┘
                           │ reconcile() dispatches
                           ▼
                    ┌─────────────────────────────┐
                    │        in_progress           │
                    │  (assignee = worker agent)    │
                    └──────┬──────────┬────────────┘
                           │          │
                    DONE   │          │  BLOCKED
                    marker │          │  marker
                           ▼          ▼
                    ┌──────────┐  ┌─────────────────┐
                    │  review  │  │ backlog          │
                    └──────────┘  │ (+ blocker note) │
                                  └─────────────────┘
```

## Error Handling

| Scenario | Behavior |
|---|---|
| Worker goes offline mid-task | Task remains `in_progress`; stale warning after threshold |
| Marker not emitted after threshold | Warn in logs; no automatic action |
| Invalid marker format | Logged and ignored |
| Marker with unknown task UUID | Logged and ignored |
| Multiple markers for same task | Only the first is processed; rest deduplicated |

## Known Limitations (Hermes-Specific)

> This section will be populated after the empirical validation phase (T1).
> See `validation/protocol-decisions.md` for validation-driven decisions.

## Version History

- **HMP/1** — Initial version. Hermes-only, marker-based completion detection.
