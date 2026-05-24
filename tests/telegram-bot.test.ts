/**
 * Unit tests for Telegram intake bot
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { parseCommand, isAuthorized, handleUpdate, getConfig } from '../intakes/telegram/bot'

// Mock task-registry
vi.mock('@/lib/task-registry', () => ({
  createTask: vi.fn((data) => ({
    id: 'test-task-uuid-001',
    ...data,
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  })),
}))

// Mock fetch for sendMessage
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Telegram Bot', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({ ok: true, text: async () => '{"ok":true}' })
  })

  // ─── parseCommand ──────────────────────────────────────

  describe('parseCommand', () => {
    it('parses /task command with subject', () => {
      const result = parseCommand('/task Fix the auth bug')
      expect(result).toEqual({ command: 'task', subject: 'Fix the auth bug' })
    })

    it('parses /urgent command with subject', () => {
      const result = parseCommand('/urgent Server is down!')
      expect(result).toEqual({ command: 'urgent', subject: 'Server is down!' })
    })

    it('handles bot-qualified commands (/task@mybot)', () => {
      const result = parseCommand('/task@hermes_maestro_bot Deploy to prod')
      expect(result).toEqual({ command: 'task', subject: 'Deploy to prod' })
    })

    it('returns null for empty subject', () => {
      expect(parseCommand('/task')).toBeNull()
      expect(parseCommand('/task ')).toBeNull()
    })

    it('returns null for non-command text', () => {
      expect(parseCommand('hello world')).toBeNull()
      expect(parseCommand('/other command')).toBeNull()
    })

    it('returns null for empty input', () => {
      expect(parseCommand('')).toBeNull()
    })

    it('handles multiline subject', () => {
      const result = parseCommand('/task Fix bug\nDetails here')
      expect(result?.subject).toContain('Fix bug')
    })
  })

  // ─── isAuthorized ──────────────────────────────────────

  describe('isAuthorized', () => {
    it('authorizes user in the list', () => {
      expect(isAuthorized(12345, ['12345', '67890'])).toBe(true)
    })

    it('rejects user not in the list', () => {
      expect(isAuthorized(99999, ['12345', '67890'])).toBe(false)
    })

    it('rejects when list is empty', () => {
      expect(isAuthorized(12345, [])).toBe(false)
    })

    it('handles string number comparison', () => {
      expect(isAuthorized(12345, ['12345'])).toBe(true)
    })
  })

  // ─── handleUpdate ──────────────────────────────────────

  describe('handleUpdate', () => {
    const config = {
      token: 'test-token-123',
      authorizedUsers: ['12345'],
      defaultTeamId: 'team-abc',
      enabled: true,
    }

    it('creates a task for /task command from authorized user', async () => {
      const update = {
        update_id: 1,
        message: {
          message_id: 100,
          from: { id: 12345, username: 'testuser', first_name: 'Test' },
          chat: { id: 12345, type: 'private' },
          text: '/task Fix the login page',
        },
      }

      await handleUpdate(update, config)

      // Should have sent a Telegram response
      expect(mockFetch).toHaveBeenCalled()
      const callUrl = mockFetch.mock.calls[0][0] as string
      expect(callUrl).toContain('sendMessage')

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body)
      expect(callBody.text).toContain('Fix the login page')
      expect(callBody.text).toContain('NORMAL')
    })

    it('creates an urgent task for /urgent command', async () => {
      const update = {
        update_id: 2,
        message: {
          message_id: 101,
          from: { id: 12345, username: 'testuser', first_name: 'Test' },
          chat: { id: 12345, type: 'private' },
          text: '/urgent Production is down',
        },
      }

      await handleUpdate(update, config)

      expect(mockFetch).toHaveBeenCalled()
      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body)
      expect(callBody.text).toContain('URGENT')
      expect(callBody.text).toContain('Production is down')
    })

    it('silently ignores unauthorized users', async () => {
      const update = {
        update_id: 3,
        message: {
          message_id: 102,
          from: { id: 99999, username: 'hacker' },
          chat: { id: 99999, type: 'private' },
          text: '/task Steal all data',
        },
      }

      await handleUpdate(update, config)

      // Should NOT send any message (silent ignore)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('ignores messages without text', async () => {
      const update = {
        update_id: 4,
        message: {
          message_id: 103,
          from: { id: 12345 },
          chat: { id: 12345, type: 'private' },
        },
      }

      await handleUpdate(update, config)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('ignores non-command text', async () => {
      const update = {
        update_id: 5,
        message: {
          message_id: 104,
          from: { id: 12345 },
          chat: { id: 12345, type: 'private' },
          text: 'Just a regular message',
        },
      }

      await handleUpdate(update, config)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('warns when default team is not configured', async () => {
      const noTeamConfig = { ...config, defaultTeamId: '' }

      const update = {
        update_id: 6,
        message: {
          message_id: 105,
          from: { id: 12345, username: 'testuser' },
          chat: { id: 12345, type: 'private' },
          text: '/task Some task',
        },
      }

      await handleUpdate(update, noTeamConfig)

      expect(mockFetch).toHaveBeenCalled()
      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body)
      expect(callBody.text).toContain('No default team')
    })
  })

  // ─── getConfig ──────────────────────────────────────────

  describe('getConfig', () => {
    it('reads config from env vars', () => {
      process.env.TELEGRAM_BOT_TOKEN = 'test-token'
      process.env.TELEGRAM_AUTHORIZED_USERS = '123,456'
      process.env.TELEGRAM_DEFAULT_TEAM_ID = 'team-1'
      process.env.TELEGRAM_ENABLED = '1'

      const cfg = getConfig()
      expect(cfg.token).toBe('test-token')
      expect(cfg.authorizedUsers).toEqual(['123', '456'])
      expect(cfg.defaultTeamId).toBe('team-1')
      expect(cfg.enabled).toBe(true)

      delete process.env.TELEGRAM_BOT_TOKEN
      delete process.env.TELEGRAM_AUTHORIZED_USERS
      delete process.env.TELEGRAM_DEFAULT_TEAM_ID
      delete process.env.TELEGRAM_ENABLED
    })

    it('handles missing env vars gracefully', () => {
      const cfg = getConfig()
      expect(cfg.enabled).toBe(false)
      expect(cfg.authorizedUsers).toEqual([])
    })
  })
})
