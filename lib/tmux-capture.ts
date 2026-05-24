/**
 * Tmux capture wrapper for HMP/1 protocol
 *
 * Provides functions to capture tmux pane output for completion
 * marker detection. The capture strategy is determined by the
 * empirical validation experiment E1.
 *
 * Default strategy: `tmux capture-pane -t <session> -p -S -1000`
 * This captures the visible pane content plus up to 1000 lines
 * of scrollback history.
 */

import { execSync } from 'child_process'
import { stripAnsi } from './completion-markers'

export interface CaptureResult {
  /** Raw captured text (ANSI stripped) */
  text: string

  /** Lines of captured text */
  lines: string[]

  /** tmux session name that was captured */
  sessionName: string

  /** ISO timestamp of the capture */
  capturedAt: string

  /** Whether the capture succeeded */
  success: boolean

  /** Error message if capture failed */
  error?: string
}

/**
 * Capture the output of a tmux session pane.
 *
 * Uses `tmux capture-pane -p -S -1000` which captures visible
 * content plus scrollback. ANSI escape codes are stripped.
 *
 * @param sessionName - The tmux session name to capture
 * @param scrollbackLines - Number of scrollback lines (default: 1000)
 * @returns CaptureResult with the captured text
 */
export function captureTmuxPane(
  sessionName: string,
  scrollbackLines: number = 1000,
): CaptureResult {
  const capturedAt = new Date().toISOString()

  try {
    const cmd = `tmux capture-pane -t ${shellEscape(sessionName)} -p -S -${scrollbackLines}`
    const rawOutput = execSync(cmd, {
      encoding: 'utf-8',
      timeout: 5000,
      maxBuffer: 1024 * 1024, // 1MB
    })

    const text = stripAnsi(rawOutput)
    const lines = text.split('\n')

    return {
      text,
      lines,
      sessionName,
      capturedAt,
      success: true,
    }
  } catch (err: any) {
    return {
      text: '',
      lines: [],
      sessionName,
      capturedAt,
      success: false,
      error: err.message || String(err),
    }
  }
}

/**
 * Check if a tmux session exists and is active.
 */
export function isTmuxSessionAlive(sessionName: string): boolean {
  try {
    const result = execSync(`tmux has-session -t ${shellEscape(sessionName)} 2>&1`, {
      encoding: 'utf-8',
      timeout: 3000,
    })
    return true
  } catch {
    return false
  }
}

/**
 * List all active tmux session names.
 */
export function listTmuxSessions(): string[] {
  try {
    const result = execSync('tmux list-sessions -F "#{session_name}"', {
      encoding: 'utf-8',
      timeout: 3000,
    })
    return result.trim().split('\n').filter(Boolean)
  } catch {
    return []
  }
}

/**
 * Get the primary tmux session name for an agent.
 * Follows the Maestro convention: agent.name (primary) or agent.name_0.
 */
export function getAgentSessionName(agentName: string, index: number = 0): string {
  return index === 0 ? agentName : `${agentName}_${index}`
}

/**
 * Shell-escape a string for safe use in shell commands.
 * Prevents injection through tmux session names.
 */
function shellEscape(str: string): string {
  return str.replace(/[^a-zA-Z0-9_\-.:]/g, '')
}
