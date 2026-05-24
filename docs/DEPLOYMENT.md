# Personal-Use Deployment Guide

> How to deploy Hermes Maestro for single-operator use.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   Maestro Server                  │
│  ┌─────────────┐  ┌────────────┐  ┌───────────┐ │
│  │   Next.js    │  │Orchestration│  │ Telegram  │ │
│  │     UI       │  │  Service    │  │   Bot     │ │
│  └──────┬───────┘  └─────┬──────┘  └───────────┘ │
│         │                │                         │
│  ┌──────┴────────────────┴──────────────────────┐ │
│  │              Task Registry (JSON)             │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
          │ tmux send-keys          │ capture-pane
          ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│   Hermes Worker 1 │    │  Hermes Worker 2  │
│   (tmux session)  │    │  (tmux session)   │
└──────────────────┘    └──────────────────┘
```

## Prerequisites

1. **Node.js 22+** — `node -v` should show v22+
2. **tmux 3.5+** — `tmux -V`
3. **Hermes 0.14+** — `hermes --version`
4. **Git** — for version control

## Installation

```bash
# Clone your fork
git clone https://github.com/valapati414/ai-maestro.git
cd ai-maestro

# Install dependencies
yarn install

# Copy and configure environment
cp .env.example .env
```

## Configuration

### Environment Variables

```env
# Core Maestro settings (see .env.example for full list)
PORT=3000

# Optional: Telegram intake
TELEGRAM_ENABLED=1
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_AUTHORIZED_USERS=your-telegram-user-id
TELEGRAM_DEFAULT_TEAM_ID=your-team-uuid
```

### Hermes Workers

Each Hermes worker must:
1. Be running in a tmux session on the same host (or accessible host)
2. Have `program: "hermes"` in its agent config
3. Be registered in Maestro's agent registry

Create workers via the Maestro UI or API:
```bash
# Via tmux (automatic registration)
# In Maestro UI: Sessions → Create Session → Select "hermes" as program
```

### Orchestration Config

Enable orchestration for a team via API:
```bash
curl -X POST http://localhost:3000/api/teams/<team-id>/orchestration \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workerSelection": "round_robin",
    "pollIntervalSeconds": 10,
    "staleThresholdMinutes": 30,
    "workers": [
      { "agentId": "<hermes-agent-id>" }
    ]
  }'
```

## Running

```bash
# Development
yarn dev

# Production
yarn build
yarn start
```

The orchestration service starts automatically with the Next.js server.

## Migrating from Upstream

If you've been using the upstream `23blocks-OS/ai-maestro`:

1. **No data migration needed** — task storage format is identical (JSON files in `~/.aimaestro/`)
2. **Agent configs unchanged** — your existing agents work as-is
3. **New: orchestration field** — teams get an optional `orchestration` field. Existing teams without it are unaffected.
4. **New: Telegram intake** — optional, only activated with env vars

### Sync with Upstream

```bash
git fetch upstream
git merge upstream/main
# Resolve any conflicts
```

## Troubleshooting

### Workers not dispatching
- Check `GET /api/orchestration/health` for service status
- Verify agent has `program: "hermes"` in config
- Verify tmux session is alive: `tmux has-session -t <session-name>`

### Markers not detected
- Workers must print `###HMP/1 DONE <uuid> <summary>` (with leading whitespace OK)
- Check poll interval — default is 10 seconds
- See [HERMES_PROTOCOL.md](./docs/HERMES_PROTOCOL.md) for marker format

### Telegram not working
- Verify `TELEGRAM_ENABLED=1` in `.env`
- Check bot token is valid
- Verify your Telegram user ID is in `TELEGRAM_AUTHORIZED_USERS`
