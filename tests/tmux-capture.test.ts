/**
 * Unit tests for tmux-capture.ts
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { captureTmuxPane, isTmuxSessionAlive, listTmuxSessions, getAgentSessionName } from '../lib/tmux-capture'

// Mock child_process.execSync
vi.mock('child_process', () => ({
  execSync: vi.fn(),
}))

import { execSync } from 'child_process'
const mockExecSync = execSync as unknown as ReturnType<typeof vi.fn>

describe('captureTmuxPane', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('captures and strips ANSI from tmux output', () => {
    mockExecSync.mockReturnValue('line1\n\x1b[32m###HMP/1 DONE test-id Done\x1b[0m\nline3')

    const result = captureTmuxPane('test-session')
    expect(result.success).toBe(true)
    expect(result.lines).toHaveLength(3)
    expect(result.lines[1]).toBe('###HMP/1 DONE test-id Done')
    expect(result.sessionName).toBe('test-session')
    expect(result.capturedAt).toBeTruthy()
  })

  it('returns failure on execSync error', () => {
    mockExecSync.mockImplementation(() => { throw new Error('session not found') })

    const result = captureTmuxPane('nonexistent')
    expect(result.success).toBe(false)
    expect(result.error).toContain('session not found')
    expect(result.lines).toHaveLength(0)
  })

  it('uses custom scrollback lines', () => {
    mockExecSync.mockReturnValue('output')

    captureTmuxPane('test', 500)
    expect(mockExecSync).toHaveBeenCalledWith(
      expect.stringContaining('-500'),
      expect.any(Object),
    )
  })

  it('escapes session name to prevent injection', () => {
    mockExecSync.mockReturnValue('output')

    captureTmuxPane('test; rm -rf /')
    // The shell escape should strip the dangerous characters
    expect(mockExecSync).toHaveBeenCalledWith(
      expect.not.stringContaining('rm -rf'),
      expect.any(Object),
    )
  })
})

describe('isTmuxSessionAlive', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns true for existing session', () => {
    mockExecSync.mockReturnValue('')
    expect(isTmuxSessionAlive('existing')).toBe(true)
  })

  it('returns false for non-existing session', () => {
    mockExecSync.mockImplementation(() => { throw new Error('no session') })
    expect(isTmuxSessionAlive('nonexistent')).toBe(false)
  })
})

describe('listTmuxSessions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists sessions correctly', () => {
    mockExecSync.mockReturnValue('session1\nsession2\nsession3\n')
    expect(listTmuxSessions()).toEqual(['session1', 'session2', 'session3'])
  })

  it('returns empty array when no sessions', () => {
    mockExecSync.mockImplementation(() => { throw new Error('no sessions') })
    expect(listTmuxSessions()).toEqual([])
  })

  it('filters empty lines', () => {
    mockExecSync.mockReturnValue('session1\n\nsession2\n')
    expect(listTmuxSessions()).toEqual(['session1', 'session2'])
  })
})

describe('getAgentSessionName', () => {
  it('returns agent name for index 0', () => {
    expect(getAgentSessionName('finance-bot', 0)).toBe('finance-bot')
  })

  it('returns indexed name for non-zero index', () => {
    expect(getAgentSessionName('finance-bot', 1)).toBe('finance-bot_1')
    expect(getAgentSessionName('finance-bot', 3)).toBe('finance-bot_3')
  })
})
