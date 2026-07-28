# AGENTS.md

## Cursor Cloud specific instructions

This is **Hermes Maestro** (a fork of AI Maestro): a Next.js 14 web dashboard that
orchestrates AI coding agents running in **tmux** sessions, exposing each as a live
web terminal (xterm.js ↔ WebSocket ↔ node-pty ↔ `tmux attach`). It runs as a single
Node process (`server.mjs`) combining the Next.js app and several WebSocket servers on
**one port: 23000**. See `README.md` and `CLAUDE.md` for architecture; commands live in
`package.json` scripts (`dev`, `build`, `start`, `test`, `lint`).

### Running / testing / building
- Dependencies are installed by the startup update script (`yarn install`). Native
  modules (`node-pty`, `cozo-node`, `onnxruntime-node`) are prebuilt/rebuilt during
  install; all Node 22.x share ABI 127, so no rebuild is needed to run.
- Dev server: `yarn dev` (serves UI + API + WebSockets on `http://localhost:23000`).
- Other commands: `yarn test` (vitest, ~880 tests), `yarn lint` (`next lint`),
  `yarn build` (`next build`). All pass out of the box.
- Config: copy `cp .env.example .env.local` (gitignored). Defaults `HOSTNAME=0.0.0.0`,
  `PORT=23000`. No external DB/broker is required for the core product.

### CRITICAL gotcha: never start the server from inside a tmux session
The app spawns `tmux attach-session` to bridge each web terminal. If the server process
has `TMUX` set in its environment (i.e. you launched `yarn dev` from inside a tmux
pane), tmux refuses to nest and the PTY never attaches. Symptoms: terminals look blank,
typed input does nothing, and the server log spams
`Error processing message: TypeError: Cannot read properties of null (reading 'write')`.
Run the server with `TMUX` unset. When you must background it via tmux, launch it as
`env -u TMUX yarn dev` so the server's children don't inherit `TMUX`.

### Node version gotcha for `yarn install`
The VM's default node (`/exec-daemon/node`, v22.14.0) makes `yarn install` **exit 1**:
yarn 1.x auto-installs node-gyp (node-pty has `gypfile: true`), and current node-gyp's
deps (`proc-log`/`nopt`) require node `>=22.22.2`. Install therefore runs under nvm's
node 22.22.2 (handled by the startup update script). Running/testing/building work fine
under the default 22.14.0.

### Agents to interact with
Agents are auto-discovered from tmux. Create one with `tmux new-session -s <name> -d`
(optionally `tmux send-keys -t <name> 'claude' C-m` for a real Claude Code agent); it
appears in the sidebar within a few seconds. Session names must match
`^[a-zA-Z0-9_-]+$`.

### Health check
There is **no** `/api/health`. Use `GET /api/sessions` (lists discovered tmux agents and
confirms the server is up). `GET /api/v1/health` exists for the AMP provider API.

### Optional / not required for core
The `plugin/` git submodule and the many `install-*.sh` scripts install end-user CLI
tooling/skills (AMP messaging, memory/graph/doc tools) into `~/.local/bin` and
`~/.claude`; they are not needed to build, test, or run this repo.
