# Orchestration — Operator Guide

> Autonomous task dispatch for Hermes Maestro teams.

## What Is Orchestration?

Orchestration automatically assigns tasks from a team's kanban to Hermes worker
agents, detects when workers complete tasks, and transitions task states — all
without human intervention.

When enabled for a team:

1. Tasks created in the team's kanban are automatically dispatched to an
   available Hermes worker in priority order.
2. The worker receives a structured dispatch message with task details and
   a completion protocol.
3. When the worker finishes, it emits a marker string in its terminal.
4. The orchestrator detects the marker and transitions the task to `review`.

## Prerequisites

- **Hermes Agent** installed on worker machines (v0.14.0+).
- Workers must be registered as agents in Maestro with `program: "hermes"`.
- Workers must have an active tmux session (status: `online`).

## Enabling Orchestration for a Team

### Via API

```bash
# Enable orchestration for a team
curl -X POST http://localhost:3000/api/teams/<team-id>/orchestration \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "workerSelection": "round_robin",
    "pollIntervalSeconds": 10,
    "staleThresholdMinutes": 30,
    "workers": [
      { "agentId": "<agent-uuid-1>" },
      { "agentId": "<agent-uuid-2>", "specialties": ["backend", "typescript"] }
    ]
  }'
```

### Configuration Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | required | Must be `true` |
| `workerSelection` | string | `round_robin` | `round_robin` or `by_specialty` |
| `pollIntervalSeconds` | number | 10 | How often to check for completion markers (min: 5) |
| `staleThresholdMinutes` | number | 30 | Minutes before warning about stuck tasks |
| `workers` | array | required | List of worker configs |
| `workers[].agentId` | string | required | Agent UUID |
| `workers[].specialties` | string[] | optional | Tags for specialty-based assignment |

### Disabling

```bash
curl -X DELETE http://localhost:3000/api/teams/<team-id>/orchestration
```

## How It Works

### Dispatch

When a task is created or becomes unblocked, the orchestrator:

1. Checks if the team has orchestration enabled.
2. Finds the highest-priority task that is `pending` or `backlog` with no assignee.
3. Selects an eligible worker (round-robin or by specialty match).
4. Sends a structured dispatch message to the worker via AMP.
5. Sets the task status to `in_progress` with the worker as assignee.

### Completion Detection

Every `pollIntervalSeconds`, the orchestrator:

1. Scans the tmux pane of each worker that has an in-flight task.
2. Strips ANSI escape codes and searches for `###HMP/1` markers.
3. On `DONE`: transitions task to `review`.
4. On `BLOCKED`: returns task to `backlog` with blocker note.

### What You'll See in the Worker Terminal

When a task is dispatched, the Hermes worker's terminal will show:

```
[HMP/1 DISPATCH]
Task-Id: 550e8400-e29b-41d4-a716-446655440000
Team: Backend Squad
Priority: 2
Subject: Fix the login bug

<task description>

[COMPLETION]
...
```

When complete:
```
###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Fixed the null pointer in auth.ts
```

## Monitoring

### Health Endpoint

```bash
curl http://localhost:3000/api/orchestration/health
```

Returns a snapshot: enabled teams, worker states, in-flight tasks, poll interval.

### Service Logs

The orchestration service logs to stdout with `[Orchestration]` prefix:

```
[Orchestration] Service initialized — 1 teams enabled, 2 workers tracked
[Orchestration] Dispatched task abc-123 to worker finance-bot
[Orchestration] Detected DONE marker for task abc-123 from finance-bot
[Orchestration] WARN: task def-456 has been in_progress for 35 minutes (threshold: 30)
```

## Telegram Intake

Tasks can be created via Telegram for mobile access.

### Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your user ID from [@userinfobot](https://t.me/userinfobot)
3. Set environment variables:

```env
TELEGRAM_ENABLED=1
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_AUTHORIZED_USERS=12345,67890
TELEGRAM_DEFAULT_TEAM_ID=your-team-uuid
```

4. Restart Maestro

### Commands

- `/task <subject>` — Create a normal priority task (priority 2)
- `/urgent <subject>` — Create an urgent task (priority 0)

Unauthorized users are silently ignored.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Tasks not dispatched | No eligible workers | Check workers are online (`sessions[0].status === 'online'`) and `program === 'hermes'` |
| Tasks dispatched but never completed | Worker not emitting marker | Check worker terminal; see `docs/HERMES_PROTOCOL.md` for marker format |
| Tasks stuck in `in_progress` | Worker crashed or marker missed | Check stale warnings in logs; manually transition task |
| False marker detection | Noisy output matching regex | Review the capture logs; tighten marker format if needed |

## Emergency Disable

To immediately stop orchestration for a team:

```bash
curl -X DELETE http://localhost:3000/api/teams/<team-id>/orchestration
```

In-flight tasks will remain `in_progress` but no new tasks will be dispatched.
Let workers finish naturally, then manually review remaining tasks.

## Backwards Compatibility

Teams without orchestration configured behave exactly as before. No tasks are
auto-dispatched. Workers are not sent any orchestration messages.

To verify: create a task on a non-orchestrated team and confirm it stays in
`backlog` with no assignee.
