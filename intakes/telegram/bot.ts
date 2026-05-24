/**
 * Telegram Bot Intake for Hermes Maestro
 *
 * Two commands:
 *   /task <subject>   → creates a task with priority 2 in the default team
 *   /urgent <subject> → creates a task with priority 0 in the default team
 *
 * Authorization: only user IDs in TELEGRAM_AUTHORIZED_USERS are allowed.
 * Unauthorized users get silent ignores.
 *
 * Configuration via env vars:
 *   TELEGRAM_BOT_TOKEN       — Bot token from @BotFather
 *   TELEGRAM_AUTHORIZED_USERS — Comma-separated user IDs (e.g., "12345,67890")
 *   TELEGRAM_DEFAULT_TEAM_ID  — Team ID to create tasks in
 *   TELEGRAM_ENABLED=1        — Set to "1" to enable the bot
 *
 * Started as a child process by Maestro on boot if TELEGRAM_ENABLED=1.
 */
import { createTask } from '@/lib/task-registry'

// ── Configuration ──────────────────────────────────────

function getConfig() {
  const token = process.env.TELEGRAM_BOT_TOKEN
  const authorizedUsers = (process.env.TELEGRAM_AUTHORIZED_USERS || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
  const defaultTeamId = process.env.TELEGRAM_DEFAULT_TEAM_ID || ''
  const enabled = process.env.TELEGRAM_ENABLED === '1'

  return { token, authorizedUsers, defaultTeamId, enabled }
}

// ── Bot Logic ──────────────────────────────────────────

interface TelegramMessage {
  message_id: number
  from?: {
    id: number
    first_name?: string
    username?: string
  }
  chat: {
    id: number
    type: string
  }
  text?: string
}

interface TelegramUpdate {
  update_id: number
  message?: TelegramMessage
}

const API_BASE = 'https://api.telegram.org/bot'

async function sendMessage(token: string, chatId: number, text: string): Promise<void> {
  const url = `${API_BASE}${token}/sendMessage`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'Markdown' }),
  })
  if (!res.ok) {
    const body = await res.text()
    console.error(`[Telegram] Failed to send message: ${res.status} ${body}`)
  }
}

function isAuthorized(userId: number, authorizedUsers: string[]): boolean {
  return authorizedUsers.includes(String(userId))
}

function parseCommand(text: string): { command: string; subject: string } | null {
  if (!text) return null

  // Match /task or /urgent followed by subject text
  const match = text.match(/^\/(task|urgent)(?:@\w+)?\s+(.+)$/s)
  if (!match) return null

  return {
    command: match[1],
    subject: match[2].trim(),
  }
}

async function handleUpdate(
  update: TelegramUpdate,
  config: ReturnType<typeof getConfig>,
): Promise<void> {
  const msg = update.message
  if (!msg?.text || !msg.from) return

  const parsed = parseCommand(msg.text)
  if (!parsed) return

  // Authorization check
  if (!isAuthorized(msg.from.id, config.authorizedUsers)) {
    console.log(`[Telegram] Unauthorized user ${msg.from.id} (${msg.from.username || 'unknown'}) attempted /${parsed.command}`)
    // Silent ignore — don't respond
    return
  }

  if (!config.defaultTeamId) {
    await sendMessage(config.token!, msg.chat.id, '⚠️ No default team configured. Set TELEGRAM_DEFAULT_TEAM_ID.')
    return
  }

  const priority = parsed.command === 'urgent' ? 0 : 2

  try {
    const task = createTask({
      teamId: config.defaultTeamId,
      subject: parsed.subject,
      description: `Created via Telegram by @${msg.from.username || msg.from.first_name || 'unknown'}`,
      priority,
      blockedBy: [],
      assigneeAgentId: null,
    })

    const priorityLabel = priority === 0 ? '🔴 URGENT' : priority <= 1 ? '🟡 HIGH' : '🔵 NORMAL'
    await sendMessage(
      config.token!,
      msg.chat.id,
      `✅ Task created: *${parsed.subject}*\n` +
      `Priority: ${priorityLabel}\n` +
      `Team: \`${config.defaultTeamId}\`\n` +
      `Task ID: \`${task.id}\``,
    )

    console.log(`[Telegram] Task created: "${parsed.subject}" (priority ${priority}, ID ${task.id})`)
  } catch (err) {
    console.error('[Telegram] Failed to create task:', err)
    await sendMessage(config.token!, msg.chat.id, `❌ Failed to create task: ${err instanceof Error ? err.message : 'Unknown error'}`)
  }
}

// ── Long Polling Loop ──────────────────────────────────

export async function startTelegramBot(): Promise<void> {
  const config = getConfig()

  if (!config.enabled) {
    console.log('[Telegram] Bot not enabled (TELEGRAM_ENABLED != "1")')
    return
  }

  if (!config.token) {
    console.error('[Telegram] TELEGRAM_BOT_TOKEN not set')
    return
  }

  if (config.authorizedUsers.length === 0) {
    console.warn('[Telegram] WARNING: TELEGRAM_AUTHORIZED_USERS is empty — no one can create tasks')
  }

  if (!config.defaultTeamId) {
    console.warn('[Telegram] WARNING: TELEGRAM_DEFAULT_TEAM_ID not set — tasks cannot be created')
  }

  console.log(`[Telegram] Bot starting with ${config.authorizedUsers.length} authorized user(s)...`)

  let lastUpdateId = 0
  const POLL_TIMEOUT = 30 // seconds

  while (true) {
    try {
      const url = `${API_BASE}${config.token}/getUpdates?offset=${lastUpdateId + 1}&timeout=${POLL_TIMEOUT}`
      const res = await fetch(url)

      if (!res.ok) {
        console.error(`[Telegram] Poll failed: ${res.status}`)
        await new Promise(r => setTimeout(r, 5000))
        continue
      }

      const data = await res.json() as { ok: boolean; result: TelegramUpdate[] }

      if (!data.ok || !Array.isArray(data.result)) {
        console.error('[Telegram] Invalid response:', data)
        await new Promise(r => setTimeout(r, 5000))
        continue
      }

      for (const update of data.result) {
        lastUpdateId = Math.max(lastUpdateId, update.update_id)
        await handleUpdate(update, config)
      }
    } catch (err) {
      console.error('[Telegram] Poll error:', err)
      await new Promise(r => setTimeout(r, 5000))
    }
  }
}

// ── CLI Entry Point ────────────────────────────────────

// Auto-start when run directly
if (typeof require !== 'undefined' && require.main === module) {
  startTelegramBot().catch(err => {
    console.error('[Telegram] Fatal:', err)
    process.exit(1)
  })
}

export { getConfig, parseCommand, isAuthorized, handleUpdate }
