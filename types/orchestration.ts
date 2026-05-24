/**
 * Orchestration types for Hermes-Maestro Protocol (HMP/1)
 *
 * This module defines the types used for autonomous task orchestration
 * within Hermes Maestro. The orchestration layer dispatches tasks to
 * Hermes workers, detects completion via marker strings in tmux panes,
 * and transitions task states automatically.
 *
 * Protocol: HMP/1 (Hermes-Maestro Protocol v1)
 * See: docs/HERMES_PROTOCOL.md for the full protocol specification.
 */

// ============================================================================
// Protocol Constants
// ============================================================================

/** Protocol version identifier used in marker strings */
export const HMP_VERSION = '1'

/** Protocol prefix for all marker strings */
export const HMP_PREFIX = '###HMP/1'

// ============================================================================
// Marker Types
// ============================================================================

/** Types of completion markers a worker can emit */
export type CompletionMarkerType = 'DONE' | 'BLOCKED'

/**
 * A parsed completion marker detected from worker output.
 *
 * Markers follow the format:
 *   ###HMP/1 <DONE|BLOCKED> <task-uuid> <summary text>
 *
 * Example:
 *   ###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Task completed successfully.
 */
export interface CompletionMarker {
  /** Whether the task was completed or blocked */
  type: CompletionMarkerType

  /** UUID of the task this marker refers to */
  taskId: string

  /** Summary text provided by the worker */
  text: string

  /** ISO timestamp when the marker was captured from tmux output */
  capturedAt: string

  /** tmux session name where the marker was detected */
  sessionName: string
}

// ============================================================================
// Dispatch Types
// ============================================================================

/**
 * Record of a task dispatch to a specific worker agent.
 *
 * Created when the orchestration service dispatches a task
 * to a Hermes worker via the message-send pipeline.
 */
export interface DispatchRecord {
  /** UUID of the dispatched task */
  taskId: string

  /** ID of the team the task belongs to */
  teamId: string

  /** ID of the worker agent the task was dispatched to */
  workerAgentId: string

  /** ISO timestamp when the task was dispatched */
  dispatchedAt: string

  /** ID of the AMP message sent to the worker */
  messageId: string
}

// ============================================================================
// Worker State
// ============================================================================

/** Current state of a worker from the orchestrator's perspective */
export type WorkerState = 'idle' | 'dispatching' | 'working' | 'unknown'

/**
 * Tracked state of an orchestration worker.
 * The orchestrator maintains this in memory for each configured worker.
 */
export interface WorkerTracker {
  /** Agent ID */
  agentId: string

  /** Current worker state */
  state: WorkerState

  /** Task ID currently being worked on (if any) */
  currentTaskId: string | null

  /** ISO timestamp of last dispatch to this worker */
  lastDispatchedAt: string | null

  /** ISO timestamp of last detected completion marker */
  lastCompletedAt: string | null

  /** Number of tasks dispatched to this worker since service start */
  dispatchCount: number

  /** tmux session name associated with this worker */
  sessionName: string | null
}

// ============================================================================
// Orchestration Events
// ============================================================================

/** Events emitted by the orchestration service */
export type OrchestrationEvent =
  | { type: 'task_dispatched'; taskId: string; workerAgentId: string; teamId: string }
  | { type: 'task_completed'; taskId: string; workerAgentId: string; marker: CompletionMarker }
  | { type: 'task_blocked'; taskId: string; workerAgentId: string; marker: CompletionMarker }
  | { type: 'worker_online'; agentId: string }
  | { type: 'worker_offline'; agentId: string }
  | { type: 'stale_task_warning'; taskId: string; workerAgentId: string; minutesElapsed: number }
  | { type: 'error'; message: string; context?: Record<string, unknown> }

// ============================================================================
// Health Check
// ============================================================================

/**
 * Health snapshot returned by the /api/orchestration/health endpoint.
 */
export interface OrchestrationHealth {
  /** Whether the service is running */
  running: boolean

  /** ISO timestamp when the service was started */
  startedAt: string | null

  /** Number of teams with orchestration enabled */
  enabledTeams: number

  /** Number of workers being tracked */
  totalWorkers: number

  /** Number of workers currently idle */
  idleWorkers: number

  /** Number of tasks currently in-flight */
  inFlightTasks: number

  /** Number of tasks dispatched since service start */
  totalDispatches: number

  /** Number of completion markers detected since service start */
  totalCompletions: number

  /** Current polling interval in seconds */
  pollIntervalSeconds: number

  /** ISO timestamp of last poll cycle */
  lastPollAt: string | null
}
