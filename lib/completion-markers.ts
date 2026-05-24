/**
 * Completion marker parser for HMP/1 protocol
 *
 * Parses marker strings from captured tmux output. Markers follow
 * the format: ###HMP/1 <DONE|BLOCKED> <task-uuid> <summary>
 *
 * The regex is designed based on empirical validation results:
 * - Tolerates up to 4 chars of leading whitespace
 * - Requires valid UUID format
 * - Captures all text after UUID as summary
 */

import { HMP_PREFIX, HMP_VERSION } from '../types/orchestration'
import type { CompletionMarker, CompletionMarkerType } from '../types/orchestration'

/**
 * Regex for matching HMP/1 completion markers.
 *
 * - Optional leading whitespace (up to 4 chars)
 * - Protocol prefix: ###HMP/1
 * - Type: DONE or BLOCKED
 * - UUID: standard 8-4-4-4-12 hex format
 * - Summary: remaining text on the line
 */
export const MARKER_REGEX = /^\s{0,4}###HMP\/1\s+(DONE|BLOCKED)\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+(.+)$/i

/** Simple hash function for deduplication */
function hashString(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash |= 0 // Convert to 32-bit integer
  }
  return hash.toString(36)
}

/**
 * Parse a single line of text for an HMP/1 marker.
 *
 * @returns A CompletionMarker if the line matches, null otherwise.
 */
export function parseMarkerLine(
  line: string,
  sessionName: string,
): { type: CompletionMarkerType; taskId: string; text: string } | null {
  const match = line.match(MARKER_REGEX)
  if (!match) return null

  const [, typeStr, taskId, text] = match
  return {
    type: typeStr.toUpperCase() as CompletionMarkerType,
    taskId: taskId.toLowerCase(),
    text: text.trim(),
  }
}

/**
 * Scan multiple lines of tmux output for markers.
 *
 * @returns Array of detected markers (one per matching line).
 */
export function scanForMarkers(
  lines: string[],
  sessionName: string,
): CompletionMarker[] {
  const markers: CompletionMarker[] = []

  for (const line of lines) {
    const parsed = parseMarkerLine(line, sessionName)
    if (parsed) {
      markers.push({
        ...parsed,
        capturedAt: new Date().toISOString(),
        sessionName,
      })
    }
  }

  return markers
}

/**
 * Marker deduplication tracker.
 * Tracks (taskId, lineHash) pairs to avoid processing the same marker twice.
 */
export class MarkerDeduplicator {
  private seen = new Set<string>()

  /**
   * Check if a marker is new (not previously seen).
   * If new, it's added to the seen set.
   *
   * @returns true if the marker is new, false if it was already seen.
   */
  isNew(marker: CompletionMarker): boolean {
    const key = `${marker.taskId}:${hashString(marker.text)}`
    if (this.seen.has(key)) {
      return false
    }
    this.seen.add(key)
    return true
  }

  /** Clear all seen markers */
  clear(): void {
    this.seen.clear()
  }

  /** Get the number of unique markers seen */
  get size(): number {
    return this.seen.size
  }
}

/**
 * Strip ANSI escape codes from a string.
 * Used to clean tmux capture-pane output before marker scanning.
 */
export function stripAnsi(text: string): string {
  // eslint-disable-next-line no-control-regex
  return text.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
    .replace(/\x1b\[[0-9;]*m/g, '')
    .replace(/\x1b\(B/g, '')
    .replace(/\x1b\[\?[0-9]+[hl]/g, '')
}

/**
 * Build a completion marker string (for testing or dispatch template).
 */
export function formatMarker(
  type: CompletionMarkerType,
  taskId: string,
  text: string,
): string {
  return `${HMP_PREFIX} ${type} ${taskId} ${text}`
}
