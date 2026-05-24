# Supporting Other AI Agents (Future)

> This document describes how Hermes Maestro could support non-Hermes agents
> in a future version. **None of this is implemented in v1.**

## Current State (v1)

The orchestration service only dispatches to agents where `program === "hermes"`.
This is intentional:

- The dispatch template and completion protocol are tuned to Hermes's behavior.
- Empirical validation was only run against Hermes.
- Marker compliance, idle behavior, and interruption handling are Hermes-specific.

## Extension Path (v2)

To support additional agents (Claude Code, Aider, Codex, OpenCode, etc.):

### 1. Agent-Type Abstraction

The eligibility check currently gates on `program === "hermes"`. This becomes:

```typescript
const SUPPORTED_AGENTS = ['hermes']  // v1

// v2:
const SUPPORTED_AGENTS = ['hermes', 'claude-code', 'codex', 'aider']
```

### 2. Agent-Specific Dispatch Templates

Each agent type may need a different dispatch message format. Create a
`DispatchTemplate` abstraction:

```typescript
interface DispatchTemplate {
  format(task: Task, team: Team): string
  markerFormat: {
    prefix: string
    done: string
    blocked: string
  }
}

// hermes-template.ts — the current HMP/1 format
// claude-template.ts — adapted for Claude Code's CLI behavior
// codex-template.ts — adapted for Codex's prompt format
```

### 3. Agent-Specific Validation

Before adding an agent type, run the same empirical validation suite (E1-E8)
against that agent. Document compliance rates and any behavioral quirks.

### 4. Completion Detection Per Agent

Some agents may not support marker-based completion. Alternatives:

- **Structured tool calls** — If the agent supports tool-call output.
- **File-based signaling** — Agent writes results to a known path.
- **Exit code detection** — For agents that run one-shot tasks.
- **WebSocket events** — If the agent emits structured events.

### Where the Code Would Go

```
lib/dispatch/
  templates/
    hermes.ts        (current HMP/1 dispatch template)
    claude-code.ts   (future)
    codex.ts         (future)
  completion/
    marker.ts        (current marker detection)
    tool-call.ts     (future)
    file-watch.ts    (future)
```

### Recommended Validation Order

1. Claude Code (most similar to Hermes in CLI behavior)
2. OpenAI Codex CLI
3. Aider
4. Cursor / other IDE-based agents (hardest — different interaction model)

## Why This Is Deferred

Each new agent type requires:
- Empirical validation (8 experiments per agent)
- Potentially different completion detection mechanism
- Separate integration test suite
- Documentation updates

The cost is significant. v1 proves the architecture works with one agent,
then v2 extends it to others on demand.
