/**
 * Orchestration Service — Autonomous task dispatch for Hermes Maestro
 *
 * Singleton service that runs inside the Next.js server process.
 * Two main loops:
 * 1. Event-driven dispatch: hooked into task-registry write paths
 * 2. Polling completion detection: scans tmux panes for HMP/1 markers
 *
 * Usage:
 *   import { orchestrationService } from '@/services/orchestration-service'
 *   orchestrationService.init()   // called at server boot
 *   orchestrationService.stop()   // called at server shutdown
 */

import { loadTeams } from '@/lib/team-registry'
import { loadTasks, updateTask, getTask } from '@/lib/task-registry'
import { loadAgents, getAgent } from '@/lib/agent-registry'
import { scanForMarkers, MarkerDeduplicator } from '@/lib/completion-markers'
import { captureTmuxPane, getAgentSessionName, isTmuxSessionAlive } from '@/lib/tmux-capture'
import { sendFromUI } from '@/lib/message-send'
import { validateOrchestrationConfig } from '@/lib/orchestration-config'
import type { Team, TeamOrchestrationConfig } from '@/types/team'
import type { Task } from '@/types/task'
import type {
  DispatchRecord,
  WorkerTracker,
  WorkerState,
  OrchestrationHealth,
  OrchestrationEvent,
  CompletionMarker,
} from '@/types/orchestration'

// ============================================================================
// Dispatch Template
// ============================================================================

function buildDispatchMessage(task: Task, team: Team): string {
  const parts: string[] = [
    '[HMP/1 DISPATCH]',
    `Task-Id: ${task.id}`,
    `Team: ${team.name}`,
    `Priority: ${task.priority ?? 2}`,
    `Subject: ${task.subject}`,
    '',
    task.description || '(no additional description)',
    '',
  ]

  if (team.instructions) {
    parts.push('[TEAM RULES]')
    parts.push(team.instructions)
    parts.push('')
  }

  parts.push(
    '[COMPLETION]',
    'When you have completed this task, output exactly one line at the start',
    'of a line in this format:',
    '',
    '    ###HMP/1 DONE ' + task.id + ' <one-paragraph summary>',
    '',
    'If you cannot complete the task and become blocked, output:',
    '',
    '    ###HMP/1 BLOCKED ' + task.id + ' <one-sentence blocker>',
    '',
    'Begin work on the task now.',
  )

  return parts.join('\n')
}

// ============================================================================
// Orchestration Service
// ============================================================================

class OrchestrationService {
  private running = false
  private startedAt: string | null = null
  private pollTimer: ReturnType<typeof setInterval> | null = null
  private workers = new Map<string, WorkerTracker>()
  private dispatchHistory: DispatchRecord[] = []
  private dedup = new MarkerDeduplicator()
  private totalDispatches = 0
  private totalCompletions = 0
  private eventListeners: ((event: OrchestrationEvent) => void)[] = []

  // ── Lifecycle ──────────────────────────────────────────

  /**
   * Initialize the service. Scans all teams for enabled orchestration
   * and starts the polling loop.
   */
  init(): void {
    if (this.running) return

    console.log('[Orchestration] Initializing service...')
    this.running = true
    this.startedAt = new Date().toISOString()

    // Load all orchestrated teams and their workers
    this.loadWorkers()

    // Start polling loop
    const pollInterval = this.getMinPollInterval()
    this.pollTimer = setInterval(() => this.poll(), pollInterval * 1000)

    // Initial reconcile — dispatch any pending tasks immediately
    this.reconcileAll()

    console.log(`[Orchestration] Service initialized — ${this.workers.size} workers tracked, polling every ${pollInterval}s`)
  }

  /**
   * Stop the service cleanly.
   */
  stop(): void {
    if (!this.running) return

    console.log('[Orchestration] Stopping service...')
    if (this.pollTimer) {
      clearInterval(this.pollTimer)
      this.pollTimer = null
    }
    this.running = false
    console.log('[Orchestration] Service stopped.')
  }

  /**
   * Reset all internal state. Used by tests to isolate between runs.
   */
  reset(): void {
    this.stop()
    this.workers.clear()
    this.dispatchHistory = []
    this.totalDispatches = 0
    this.totalCompletions = 0
    this.eventListeners = []
    this.dedup.clear()
  }

  // ── Task Lifecycle Hook ────────────────────────────────

  /**
   * Called by task-registry after any task write.
   * Defensive: never throws.
   */
  onTaskChanged(teamId: string, taskId: string, _action: 'create' | 'update' | 'delete'): void {
    if (!this.running) return

    try {
      this.reconcile(teamId)
    } catch (err) {
      console.error(`[Orchestration] Error in onTaskChanged for team ${teamId}:`, err)
    }
  }

  // ── Reconcile ──────────────────────────────────────────

  /**
   * Reconcile all enabled teams. Called on init and available for testing.
   */
  reconcileAll(): void {
    const teams = loadTeams()
    for (const team of teams) {
      if (team.orchestration?.enabled) {
        try {
          this.reconcile(team.id)
        } catch (err) {
          console.error(`[Orchestration] Error reconciling team ${team.id}:`, err)
        }
      }
    }
  }

  /**
   * Run a single poll cycle. Useful for testing without waiting for timers.
   */
  pollOnce(): void {
    this.poll()
  }

  /**
   * Evaluate a team's tasks and dispatch if needed.
   * Called after task changes and on poll cycles.
   */
  private reconcile(teamId: string): void {
    const team = this.findTeam(teamId)
    if (!team?.orchestration?.enabled) return

    const tasks = loadTasks(teamId)
    const config = team.orchestration

    // Find dispatchable tasks: pending or backlog, no assignee, not blocked
    const dispatchable = tasks
      .filter(t =>
        (t.status === 'pending' || t.status === 'backlog') &&
        !t.assigneeAgentId
      )
      .filter(t => {
        // Check if all blockers are completed
        return t.blockedBy.every(depId => {
          const dep = tasks.find(d => d.id === depId)
          return dep && dep.status === 'completed'
        })
      })
      .sort((a, b) => (a.priority ?? 2) - (b.priority ?? 2)) // Lower number = higher priority

    for (const task of dispatchable) {
      const worker = this.selectWorker(teamId, config)
      if (!worker) break // No available workers

      this.dispatch(task, team, worker)
    }
  }

  // ── Dispatch ───────────────────────────────────────────

  private async dispatch(task: Task, team: Team, worker: WorkerTracker): Promise<void> {
    console.log(`[Orchestration] Dispatching task ${task.id} to worker ${worker.agentId}`)

    // Update task to in_progress
    updateTask(team.id, task.id, {
      status: 'in_progress',
      assigneeAgentId: worker.agentId,
    })

    // Update worker state
    worker.state = 'working'
    worker.currentTaskId = task.id
    worker.lastDispatchedAt = new Date().toISOString()
    worker.dispatchCount++

    // Build and send dispatch message
    const dispatchMsg = buildDispatchMessage(task, team)
    const agent = getAgent(worker.agentId)

    try {
      const result = await sendFromUI({
        from: 'orchestration',
        to: agent?.name || worker.agentId,
        subject: `Task: ${task.subject}`,
        content: {
          type: 'notification',
          message: dispatchMsg,
        },
        priority: 'high',
      })

      // Record dispatch
      const record: DispatchRecord = {
        taskId: task.id,
        teamId: team.id,
        workerAgentId: worker.agentId,
        dispatchedAt: new Date().toISOString(),
        messageId: result.message.id,
      }
      this.dispatchHistory.push(record)
      this.totalDispatches++

      this.emitEvent({
        type: 'task_dispatched',
        taskId: task.id,
        workerAgentId: worker.agentId,
        teamId: team.id,
      })

      console.log(`[Orchestration] Task ${task.id} dispatched to ${worker.agentId} (msg: ${result.message.id})`)
    } catch (err) {
      console.error(`[Orchestration] Failed to dispatch to ${worker.agentId}:`, err)
      // Revert task state
      updateTask(team.id, task.id, {
        status: 'pending',
        assigneeAgentId: null,
      })
      worker.state = 'idle'
      worker.currentTaskId = null
    }
  }

  // ── Completion Detection (Polling) ─────────────────────

  private poll(): void {
    if (!this.running) return

    // 1. Check workers tracked by the service (dispatched by us)
    for (const [agentId, worker] of this.workers) {
      if (worker.state !== 'working' || !worker.currentTaskId) continue

      const teamId = this.findTeamForWorker(agentId)
      if (!teamId) continue

      const sessionName = worker.sessionName || getAgentSessionName(agentId)
      if (!isTmuxSessionAlive(sessionName)) {
        this.emitEvent({ type: 'worker_offline', agentId })
        continue
      }

      const capture = captureTmuxPane(sessionName)
      if (!capture.success) continue

      const markers = scanForMarkers(capture.lines, sessionName)
      for (const marker of markers) {
        if (marker.taskId !== worker.currentTaskId) continue
        if (!this.dedup.isNew(marker)) continue

        this.handleCompletionMarker(marker, teamId, worker)
      }

      this.checkStale(worker, teamId)
    }

    // 2. Scan for in_progress tasks assigned to workers that we didn't dispatch
    //    (e.g., tasks set to in_progress externally or from a prior service restart)
    this.scanOrphanedInProgressTasks()
  }

  /**
   * Scan all in_progress tasks in orchestrated teams and check their
   * assigned workers for completion markers. Handles the case where
   * the service restarts and doesn't know about in-flight tasks.
   */
  private scanOrphanedInProgressTasks(): void {
    const teams = loadTeams()
    for (const team of teams) {
      if (!team.orchestration?.enabled) continue

      const tasks = loadTasks(team.id)
      const inProgress = tasks.filter(t =>
        t.status === 'in_progress' && t.assigneeAgentId,
      )

      for (const task of inProgress) {
        // Skip if this worker is already tracked (handled above)
        const trackedWorker = this.workers.get(task.assigneeAgentId!)
        if (trackedWorker?.state === 'working' && trackedWorker.currentTaskId === task.id) continue

        // This is an orphaned task — check the worker's session
        const agent = getAgent(task.assigneeAgentId!)
        if (!agent) continue

        const sessionName = agent.name
        if (!isTmuxSessionAlive(sessionName)) continue

        const capture = captureTmuxPane(sessionName)
        if (!capture.success) continue

        const markers = scanForMarkers(capture.lines, sessionName)
        for (const marker of markers) {
          if (marker.taskId !== task.id) continue
          if (!this.dedup.isNew(marker)) continue

          // Create a temporary tracker for this orphaned task
          const tempWorker: WorkerTracker = trackedWorker || {
            agentId: task.assigneeAgentId!,
            state: 'idle',
            currentTaskId: null,
            lastDispatchedAt: null,
            lastCompletedAt: null,
            dispatchCount: 0,
            sessionName,
          }

          this.handleCompletionMarker(marker, team.id, tempWorker)
        }
      }
    }
  }

  private handleCompletionMarker(marker: CompletionMarker, teamId: string, worker: WorkerTracker): void {
    console.log(`[Orchestration] Detected ${marker.type} marker for task ${marker.taskId} from ${worker.agentId}`)

    this.totalCompletions++

    if (marker.type === 'DONE') {
      updateTask(teamId, marker.taskId, { status: 'review' })
      this.emitEvent({
        type: 'task_completed',
        taskId: marker.taskId,
        workerAgentId: worker.agentId,
        marker,
      })
    } else if (marker.type === 'BLOCKED') {
      // Return task to backlog with blocker note
      const task = getTask(teamId, marker.taskId)
      updateTask(teamId, marker.taskId, {
        status: 'backlog',
        assigneeAgentId: null,
        description: `${task?.description || ''}\n\n**Blocked:** ${marker.text}`,
      })
      this.emitEvent({
        type: 'task_blocked',
        taskId: marker.taskId,
        workerAgentId: worker.agentId,
        marker,
      })
    }

    // Free the worker
    worker.state = 'idle'
    worker.currentTaskId = null
    worker.lastCompletedAt = new Date().toISOString()

    // Trigger reconcile only for DONE (to dispatch next task).
    // Skip reconcile for BLOCKED — the task is back in backlog and
    // should NOT be immediately re-dispatched to another worker.
    if (marker.type === 'DONE') {
      this.reconcile(teamId)
    }
  }

  private checkStale(worker: WorkerTracker, teamId: string): void {
    if (!worker.lastDispatchedAt || !worker.currentTaskId) return

    const team = this.findTeam(teamId)
    if (!team?.orchestration) return

    const threshold = team.orchestration.staleThresholdMinutes * 60 * 1000
    const elapsed = Date.now() - new Date(worker.lastDispatchedAt).getTime()

    if (elapsed > threshold) {
      const minutesElapsed = Math.round(elapsed / 60000)
      console.warn(`[Orchestration] WARN: task ${worker.currentTaskId} has been in_progress for ${minutesElapsed} minutes (threshold: ${team.orchestration.staleThresholdMinutes})`)
      this.emitEvent({
        type: 'stale_task_warning',
        taskId: worker.currentTaskId,
        workerAgentId: worker.agentId,
        minutesElapsed,
      })
    }
  }

  // ── Worker Management ──────────────────────────────────

  private loadWorkers(): void {
    this.workers.clear()
    const teams = loadTeams()

    for (const team of teams) {
      if (!team.orchestration?.enabled) continue

      for (const w of team.orchestration.workers) {
        if (!this.workers.has(w.agentId)) {
          const agent = getAgent(w.agentId)
          const sessionName = agent ? getAgentSessionName(agent.name) : null

          this.workers.set(w.agentId, {
            agentId: w.agentId,
            state: 'idle',
            currentTaskId: null,
            lastDispatchedAt: null,
            lastCompletedAt: null,
            dispatchCount: 0,
            sessionName,
          })
        }
      }
    }
  }

  private selectWorker(teamId: string, config: TeamOrchestrationConfig): WorkerTracker | null {
    const teamWorkers = config.workers

    for (const w of teamWorkers) {
      const tracker = this.workers.get(w.agentId)
      if (!tracker) continue

      // Check eligibility
      if (tracker.state !== 'idle') continue

      const agent = getAgent(w.agentId)
      if (!agent) continue

      // v1: only Hermes agents
      if (agent.program !== 'hermes') continue

      // Check session is online
      const sessionStatus = agent.sessions?.[0]?.status
      if (sessionStatus !== 'online') continue

      return tracker
    }

    return null
  }

  // ── Health ─────────────────────────────────────────────

  getHealth(): OrchestrationHealth {
    const idleWorkers = Array.from(this.workers.values()).filter(w => w.state === 'idle').length
    const inFlightTasks = Array.from(this.workers.values()).filter(w => w.state === 'working').length

    return {
      running: this.running,
      startedAt: this.startedAt,
      enabledTeams: this.countEnabledTeams(),
      totalWorkers: this.workers.size,
      idleWorkers,
      inFlightTasks,
      totalDispatches: this.totalDispatches,
      totalCompletions: this.totalCompletions,
      pollIntervalSeconds: this.getMinPollInterval(),
      lastPollAt: this.startedAt, // Simplified — real implementation would track
    }
  }

  // ── Events ─────────────────────────────────────────────

  onEvent(listener: (event: OrchestrationEvent) => void): void {
    this.eventListeners.push(listener)
  }

  private emitEvent(event: OrchestrationEvent): void {
    for (const listener of this.eventListeners) {
      try {
        listener(event)
      } catch (err) {
        console.error('[Orchestration] Event listener error:', err)
      }
    }
  }

  // ── Helpers ────────────────────────────────────────────

  private findTeam(teamId: string): Team | null {
    const teams = loadTeams()
    return teams.find(t => t.id === teamId) || null
  }

  private findTeamForWorker(agentId: string): string | null {
    const teams = loadTeams()
    for (const team of teams) {
      if (!team.orchestration?.enabled) continue
      if (team.orchestration.workers.some(w => w.agentId === agentId)) {
        return team.id
      }
    }
    return null
  }

  private countEnabledTeams(): number {
    const teams = loadTeams()
    return teams.filter(t => t.orchestration?.enabled).length
  }

  private getMinPollInterval(): number {
    const teams = loadTeams()
    const intervals = teams
      .filter(t => t.orchestration?.enabled)
      .map(t => t.orchestration!.pollIntervalSeconds)
    return intervals.length > 0 ? Math.min(...intervals) : 10
  }

  /** Reload workers (called when orchestration config changes) */
  reload(): void {
    this.loadWorkers()
    console.log('[Orchestration] Workers reloaded')
  }
}

// Singleton instance
export const orchestrationService = new OrchestrationService()
