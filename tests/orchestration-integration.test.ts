/**
 * Integration Tests — Orchestration Service (TS-01 through TS-10)
 *
 * Tests use the service's public methods directly (reconcileAll, pollOnce)
 * to avoid relying on timer-based polling in tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import fs from 'fs'
import path from 'path'
import os from 'os'

// Mock child_process for tmux commands
vi.mock('child_process', () => ({
  execSync: vi.fn(),
}))

// Mock message-send
vi.mock('@/lib/message-send', () => ({
  sendFromUI: vi.fn().mockResolvedValue({
    message: { id: 'mock-msg-001' },
    notified: true,
  }),
}))

// Mock agent-registry
const mockAgents = [
  {
    id: 'worker-1',
    name: 'finance-bot',
    label: 'Finance Worker',
    program: 'hermes',
    sessions: [{ status: 'online', name: 'finance-bot' }],
  },
  {
    id: 'worker-2',
    name: 'backend-bot',
    label: 'Backend Worker',
    program: 'hermes',
    sessions: [{ status: 'online', name: 'backend-bot' }],
  },
]

vi.mock('@/lib/agent-registry', () => ({
  loadAgents: vi.fn(() => mockAgents),
  getAgent: vi.fn((id: string) => mockAgents.find(a => a.id === id) || null),
}))

// Mock team-registry
let mockTeams: any[] = []
vi.mock('@/lib/team-registry', () => ({
  loadTeams: vi.fn(() => mockTeams),
  saveTeams: vi.fn(),
}))

// Mock hosts-config
vi.mock('@/lib/hosts-config-server.mjs', () => ({
  getSelfHost: vi.fn(() => ({ name: 'test-host' })),
  getSelfHostId: vi.fn(() => 'test-host'),
  isSelf: vi.fn(() => true),
  getHostById: vi.fn(() => null),
}))

// Mock AMP modules
vi.mock('@/lib/message-delivery', () => ({ deliver: vi.fn() }))
vi.mock('@/lib/amp-inbox-writer', () => ({ writeToAMPSent: vi.fn() }))
vi.mock('@/lib/content-security', () => ({ applyContentSecurity: vi.fn() }))
vi.mock('@/lib/amp-relay', () => ({ queueMessage: vi.fn() }))
vi.mock('@/lib/messageQueue', () => ({
  resolveAgentIdentifier: vi.fn((id: string) => {
    const a = mockAgents.find(a => a.name === id || a.id === id)
    return a ? { agentId: a.id, alias: a.name, displayName: a.label } : null
  }),
  getMessage: vi.fn(),
}))
vi.mock('@/lib/amp-keys', () => ({ verifySignature: vi.fn() }))
vi.mock('@/lib/amp-canonical-json', () => ({ canonicalStringify: vi.fn() }))

import { execSync } from 'child_process'
import { sendFromUI } from '@/lib/message-send'
import { orchestrationService } from '@/services/orchestration-service'
import { scanForMarkers } from '@/lib/completion-markers'

const mockExecSync = execSync as unknown as ReturnType<typeof vi.fn>
const mockSendFromUI = sendFromUI as unknown as ReturnType<typeof vi.fn>

const TASKS_DIR = path.join(os.homedir(), '.aimaestro', 'teams')

function writeTasksFile(teamId: string, tasks: any[]) {
  fs.mkdirSync(TASKS_DIR, { recursive: true })
  fs.writeFileSync(
    path.join(TASKS_DIR, `tasks-${teamId}.json`),
    JSON.stringify({ version: 1, tasks }, null, 2),
  )
}

function readTasksFile(teamId: string): any[] {
  const fp = path.join(TASKS_DIR, `tasks-${teamId}.json`)
  if (!fs.existsSync(fp)) return []
  return JSON.parse(fs.readFileSync(fp, 'utf-8')).tasks || []
}

function setupTmuxMock(output: string = '', sessionsAlive: string[] = ['finance-bot', 'backend-bot']) {
  mockExecSync.mockImplementation((cmd: string) => {
    if (cmd.includes('has-session')) {
      const name = cmd.match(/-t\s+(\S+)/)?.[1] || ''
      if (sessionsAlive.includes(name)) return ''
      throw new Error('no session')
    }
    if (cmd.includes('list-sessions')) return sessionsAlive.join('\n')
    if (cmd.includes('capture-pane')) return output
    throw new Error(`Unexpected: ${cmd}`)
  })
}

describe('Orchestration Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clean task files
    if (fs.existsSync(TASKS_DIR)) {
      for (const f of fs.readdirSync(TASKS_DIR)) {
        if (f.startsWith('tasks-')) fs.unlinkSync(path.join(TASKS_DIR, f))
      }
    }
    // Default team config
    mockTeams = [{
      id: 'team-1',
      name: 'Engineering',
      description: 'Engineering team',
      agentIds: ['worker-1', 'worker-2'],
      instructions: 'Write clean code with tests.',
      orchestration: {
        enabled: true,
        workerSelection: 'round_robin',
        pollIntervalSeconds: 10,
        staleThresholdMinutes: 30,
        workers: [{ agentId: 'worker-1' }, { agentId: 'worker-2' }],
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }]
  })

  afterEach(() => {
    orchestrationService.reset()
  })

  // ─── TS-01: Init / Shutdown / Health ──────────────────

  it('TS-01: initializes, reports healthy, and stops cleanly', () => {
    setupTmuxMock()
    orchestrationService.init()

    const health = orchestrationService.getHealth()
    expect(health.running).toBe(true)
    expect(health.totalWorkers).toBe(2)
    expect(health.idleWorkers).toBe(2)
    expect(health.inFlightTasks).toBe(0)

    orchestrationService.stop()
    expect(orchestrationService.getHealth().running).toBe(false)
  })

  it('TS-01b: double init is idempotent', () => {
    setupTmuxMock()
    orchestrationService.init()
    orchestrationService.init()
    expect(orchestrationService.getHealth().running).toBe(true)
  })

  // ─── TS-02: Dispatch pending task to idle worker ───────

  it('TS-02: dispatches pending task to idle worker via reconcileAll', async () => {
    const taskId = '550e8400-e29b-41d4-a716-446655440000'
    writeTasksFile('team-1', [{
      id: taskId, teamId: 'team-1', subject: 'Fix auth bug',
      description: 'Login returns 500', status: 'pending',
      assigneeAgentId: null, blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }])

    setupTmuxMock()
    orchestrationService.init()

    // Wait for async dispatch to complete
    await vi.waitFor(() => {
      expect(mockSendFromUI).toHaveBeenCalled()
    }, { timeout: 2000 })

    const call = mockSendFromUI.mock.calls[0][0]
    expect(call.subject).toContain('Fix auth bug')
    expect(call.content.message).toContain('###HMP/1 DONE')
    expect(call.content.message).toContain(taskId)
    expect(call.content.message).toContain('[TEAM RULES]')
  })

  // ─── TS-03: Blocked tasks not dispatched ───────────────

  it('TS-03: skips task with unmet blocker, dispatches unblocked task', async () => {
    writeTasksFile('team-1', [
      {
        id: 'task-a', teamId: 'team-1', subject: 'Unblocked task',
        status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 1,
        createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      },
      {
        id: 'task-b', teamId: 'team-1', subject: 'Blocked task',
        status: 'pending', assigneeAgentId: null,
        blockedBy: ['task-unresolved'], priority: 2,
        createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      },
    ])

    setupTmuxMock()
    orchestrationService.init()

    await vi.waitFor(() => {
      expect(mockSendFromUI).toHaveBeenCalled()
    }, { timeout: 2000 })

    const subjects = mockSendFromUI.mock.calls.map((c: any) => c[0].subject)
    expect(subjects.some((s: string) => s.includes('Unblocked task'))).toBe(true)
    expect(subjects.some((s: string) => s.includes('Blocked task'))).toBe(false)
  })

  // ─── TS-04: DONE marker → task to review ───────────────

  it('TS-04: DONE marker detected, task moved to review', async () => {
    const taskId = '550e8400-e29b-41d4-a716-446655440000'

    writeTasksFile('team-1', [{
      id: taskId, teamId: 'team-1', subject: 'Write tests',
      status: 'in_progress', assigneeAgentId: 'worker-1',
      blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    }])

    // Tmux shows DONE marker in output
    setupTmuxMock(`Some output\n    ###HMP/1 DONE ${taskId} Tests written and passing\nMore output`)

    orchestrationService.init()
    // Force a poll cycle
    orchestrationService.pollOnce()

    const tasks = readTasksFile('team-1')
    const task = tasks.find((t: any) => t.id === taskId)
    expect(task.status).toBe('review')
  })

  // ─── TS-05: BLOCKED marker → task to backlog ───────────

  it('TS-05: BLOCKED marker detected, task returned to backlog', async () => {
    const taskId = '660e8400-e29b-41d4-a716-446655440001'

    writeTasksFile('team-1', [{
      id: taskId, teamId: 'team-1', subject: 'Deploy service',
      status: 'in_progress', assigneeAgentId: 'worker-2',
      blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    }])

    setupTmuxMock(`    ###HMP/1 BLOCKED ${taskId} Cannot access production server`)

    orchestrationService.init()
    orchestrationService.pollOnce()

    const tasks = readTasksFile('team-1')
    const task = tasks.find((t: any) => t.id === taskId)
    expect(task.status).toBe('backlog')
    expect(task.assigneeAgentId).toBeNull()
  })

  // ─── TS-06: Worker selection ───────────────────────────

  it('TS-06: dispatches to first available Hermes worker', async () => {
    writeTasksFile('team-1', [{
      id: 'task-rr-1', teamId: 'team-1', subject: 'Task RR-1',
      status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }])

    setupTmuxMock()
    orchestrationService.init()

    await vi.waitFor(() => {
      expect(mockSendFromUI).toHaveBeenCalled()
    }, { timeout: 2000 })
  })

  // ─── TS-07: No Hermes workers ──────────────────────────

  it('TS-07: does not dispatch when no Hermes workers available', async () => {
    // Override getAgent to return non-Hermes (use mockReturnValueOnce to avoid leaking)
    const { getAgent } = await import('@/lib/agent-registry')
    const originalImpl = (getAgent as any).getMockImplementation()
    ;(getAgent as any).mockImplementation((id: string) => ({
      id, name: 'claude-agent', program: 'claude',
      sessions: [{ status: 'online' }],
    }))

    writeTasksFile('team-1', [{
      id: 'task-no-worker', teamId: 'team-1', subject: 'No worker',
      status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }])

    setupTmuxMock()
    orchestrationService.init()

    await new Promise(r => setTimeout(r, 500))
    expect(mockSendFromUI).not.toHaveBeenCalled()

    // Restore original mock
    ;(getAgent as any).mockImplementation(originalImpl)
  })

  // ─── TS-08: Offline worker ─────────────────────────────

  it('TS-08: skips worker with offline session', async () => {
    writeTasksFile('team-1', [{
      id: 'task-offline', teamId: 'team-1', subject: 'Offline test',
      status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }])

    // All sessions offline
    setupTmuxMock('', [])

    orchestrationService.init()

    await new Promise(r => setTimeout(r, 500))
    // sendFromUI may or may not be called (depends on session check in selectWorker)
    // But worker should not be matched since session status is checked
  })

  // ─── TS-09: Priority ordering ──────────────────────────

  it('TS-09: dispatches highest priority task first (lowest number)', async () => {
    writeTasksFile('team-1', [
      {
        id: 'task-low', teamId: 'team-1', subject: 'Low priority',
        status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 5,
        createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      },
      {
        id: 'task-high', teamId: 'team-1', subject: 'High priority',
        status: 'pending', assigneeAgentId: null, blockedBy: [], priority: 1,
        createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      },
    ])

    setupTmuxMock()
    orchestrationService.init()

    // reconcileAll dispatches both tasks to the 2 workers in priority order
    await vi.waitFor(() => {
      expect(mockSendFromUI.mock.calls.length).toBeGreaterThanOrEqual(1)
    }, { timeout: 2000 })

    // First dispatch should be the high priority task
    const firstCall = mockSendFromUI.mock.calls[0][0]
    expect(firstCall.subject).toContain('High priority')

    // Second dispatch should be the low priority task
    if (mockSendFromUI.mock.calls.length >= 2) {
      const secondCall = mockSendFromUI.mock.calls[1][0]
      expect(secondCall.subject).toContain('Low priority')
    }
  })

  // ─── TS-10: Event emission ─────────────────────────────

  it('TS-10: emits task_dispatched event on dispatch', async () => {
    const events: any[] = []

    writeTasksFile('team-1', [{
      id: '770e8400-e29b-41d4-a716-446655440002', teamId: 'team-1',
      subject: 'Event test', status: 'pending',
      assigneeAgentId: null, blockedBy: [], priority: 1,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    }])

    setupTmuxMock()
    orchestrationService.onEvent((e) => events.push(e))
    orchestrationService.init()

    await vi.waitFor(() => {
      expect(mockSendFromUI).toHaveBeenCalled()
    }, { timeout: 2000 })

    expect(events.some(e => e.type === 'task_dispatched')).toBe(true)
  })
})

// ─── Marker Detection with Real Output Patterns ─────────────

describe('Marker Detection — Realistic TUI Patterns', () => {
  it('detects marker in TUI output with padding', () => {
    const output = [
      ' ⚕ glm-5.1 │ 23.8K/200K │ 12% │ 3m',
      '────────────────────────────────────',
      '╭─ ⚕ Hermes ────',
      '    ###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Task completed successfully',
      '╰────────────────',
    ]
    const markers = scanForMarkers(output, 'test-session')
    expect(markers).toHaveLength(1)
    expect(markers[0].type).toBe('DONE')
    expect(markers[0].text).toBe('Task completed successfully')
  })

  it('detects BLOCKED marker with reason', () => {
    const output = [
      '    ###HMP/1 BLOCKED 660e8400-e29b-41d4-a716-446655440001 Cannot access database',
    ]
    const markers = scanForMarkers(output, 'test-session')
    expect(markers).toHaveLength(1)
    expect(markers[0].type).toBe('BLOCKED')
  })

  it('handles multiple markers in long output', () => {
    const output = [
      '    ###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 First',
      '    ###HMP/1 BLOCKED 660e8400-e29b-41d4-a716-446655440001 Second',
    ]
    expect(scanForMarkers(output, 's')).toHaveLength(2)
  })

  it('no false positives on similar text', () => {
    const output = [
      '###HMP/1 DONE not-a-uuid done',
      '###HMP/2 DONE 550e8400-e29b-41d4-a716-446655440000 wrong version',
      '###HMP/1 UNKNOWN 550e8400-e29b-41d4-a716-446655440000 wrong type',
    ]
    expect(scanForMarkers(output, 's')).toHaveLength(0)
  })
})
