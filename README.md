# Hermes Maestro

> A fork of [ai-maestro](https://github.com/23blocks-OS/ai-maestro) by [23blocks](https://github.com/23blocks-OS) with autonomous task orchestration for [Hermes](https://hermes-agent.nousresearch.com/) workers.

**License:** MIT (see [LICENSE](./LICENSE)). Upstream license at [LICENSE.upstream](./LICENSE.upstream).

## What This Fork Adds

- **Autonomous Orchestration** — Automatically dispatch kanban tasks to Hermes agent workers, detect completion via tmux markers, and manage the full task lifecycle.
- **HMP/1 Protocol** — A simple wire protocol (`###HMP/1 DONE <uuid> <summary>`) for agents to signal task completion back to Maestro.
- **Telegram Intake** — Create tasks via Telegram (`/task` and `/urgent` commands) from your phone.
- **Event System** — Hook into orchestration events (dispatch, completion, blocked, stale) for custom integrations.

## Quick Start

### Prerequisites

- Node.js 22+
- [Hermes](https://hermes-agent.nousresearch.com/) 0.14+ installed on worker hosts
- tmux 3.5+

### Install

```bash
git clone https://github.com/valapati414/ai-maestro.git
cd ai-maestro
yarn install
cp .env.example .env
# Edit .env with your configuration
yarn dev
```

### Enable Orchestration

1. Create a team with Hermes workers in the Maestro UI
2. Add an `orchestration` config to the team:

```json
{
  "orchestration": {
    "enabled": true,
    "workerSelection": "round_robin",
    "pollIntervalSeconds": 10,
    "staleThresholdMinutes": 30,
    "workers": [
      { "agentId": "your-hermes-agent-id" }
    ]
  }
}
```

3. Or use the API: `POST /api/teams/<id>/orchestration`

### Enable Telegram (Optional)

Set environment variables:
```
TELEGRAM_ENABLED=1
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_AUTHORIZED_USERS=12345,67890
TELEGRAM_DEFAULT_TEAM_ID=<team-uuid>
```

Then send `/task <subject>` or `/urgent <subject>` to your bot.

## Status

**v1** — Hermes-only, self-hosted, single-operator use case.

Only Hermes agents are supported as workers. Multi-agent support (Claude, Codex, etc.) is planned for a future version. See [docs/OTHER_AGENTS.md](./docs/OTHER_AGENTS.md).

## Documentation

- [ORCHESTRATION.md](./docs/ORCHESTRATION.md) — Operator guide for autonomous dispatch
- [HERMES_PROTOCOL.md](./docs/HERMES_PROTOCOL.md) — HMP/1 wire protocol specification
- [OTHER_AGENTS.md](./docs/OTHER_AGENTS.md) — Future multi-agent support notes
- [VALIDATION_ANALYSIS.md](./validation/VALIDATION_ANALYSIS.md) — Empirical Hermes validation results

## Development

```bash
yarn dev          # Start development server
yarn test         # Run all tests (865+ tests)
yarn lint         # Lint code
yarn build        # Production build
```

## Upstream

- Original: [23blocks-OS/ai-maestro](https://github.com/23blocks-OS/ai-maestro)
- Fork maintained by [Prasad Alapati](https://github.com/valapati414)
