/**
 * Unit tests for completion-markers.ts
 */
import { describe, it, expect } from 'vitest'
import {
  parseMarkerLine,
  scanForMarkers,
  stripAnsi,
  formatMarker,
  MARKER_REGEX,
  MarkerDeduplicator,
} from '../lib/completion-markers'

describe('MARKER_REGEX', () => {
  it('matches a valid DONE marker at column 0', () => {
    const line = '###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Task completed successfully'
    expect(MARKER_REGEX.test(line)).toBe(true)
  })

  it('matches a valid BLOCKED marker', () => {
    const line = '###HMP/1 BLOCKED 550e8400-e29b-41d4-a716-446655440000 Cannot access database'
    expect(MARKER_REGEX.test(line)).toBe(true)
  })

  it('tolerates up to 4 chars of leading whitespace', () => {
    const line = '    ###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Done'
    expect(MARKER_REGEX.test(line)).toBe(true)
  })

  it('rejects more than 4 chars of leading whitespace', () => {
    const line = '      ###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Done'
    expect(MARKER_REGEX.test(line)).toBe(false)
  })

  it('rejects invalid UUID format', () => {
    const line = '###HMP/1 DONE not-a-uuid Done'
    expect(MARKER_REGEX.test(line)).toBe(false)
  })

  it('rejects unknown marker type', () => {
    const line = '###HMP/1 UNKNOWN 550e8400-e29b-41d4-a716-446655440000 Done'
    expect(MARKER_REGEX.test(line)).toBe(false)
  })

  it('captures summary text with spaces', () => {
    const line = '###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Fixed bug in auth.ts and added tests'
    const match = line.match(MARKER_REGEX)
    expect(match).not.toBeNull()
    expect(match![3]).toBe('Fixed bug in auth.ts and added tests')
  })
})

describe('parseMarkerLine', () => {
  const validUUID = '550e8400-e29b-41d4-a716-446655440000'

  it('parses a DONE marker', () => {
    const result = parseMarkerLine(`###HMP/1 DONE ${validUUID} Task done`, 'test-session')
    expect(result).toEqual({
      type: 'DONE',
      taskId: validUUID,
      text: 'Task done',
    })
  })

  it('parses a BLOCKED marker', () => {
    const result = parseMarkerLine(`###HMP/1 BLOCKED ${validUUID} No access`, 'test-session')
    expect(result).toEqual({
      type: 'BLOCKED',
      taskId: validUUID,
      text: 'No access',
    })
  })

  it('returns null for non-matching line', () => {
    expect(parseMarkerLine('Just some regular output', 'test-session')).toBeNull()
  })

  it('returns null for empty line', () => {
    expect(parseMarkerLine('', 'test-session')).toBeNull()
  })

  it('normalizes UUID to lowercase', () => {
    const result = parseMarkerLine(`###HMP/1 DONE ${validUUID.toUpperCase()} Done`, 'test-session')
    expect(result?.taskId).toBe(validUUID)
  })

  it('is case-insensitive for marker type', () => {
    const result = parseMarkerLine(`###HMP/1 done ${validUUID} Done`, 'test-session')
    expect(result?.type).toBe('DONE')
  })
})

describe('scanForMarkers', () => {
  it('finds multiple markers in multi-line output', () => {
    const uuid1 = '550e8400-e29b-41d4-a716-446655440000'
    const uuid2 = '660e8400-e29b-41d4-a716-446655440001'
    const lines = [
      'Some output here',
      `###HMP/1 DONE ${uuid1} First task done`,
      'More output',
      `###HMP/1 BLOCKED ${uuid2} Second task blocked`,
      'Final output',
    ]
    const markers = scanForMarkers(lines, 'session-1')
    expect(markers).toHaveLength(2)
    expect(markers[0].type).toBe('DONE')
    expect(markers[0].taskId).toBe(uuid1)
    expect(markers[1].type).toBe('BLOCKED')
    expect(markers[1].taskId).toBe(uuid2)
  })

  it('returns empty array when no markers found', () => {
    const lines = ['Just output', 'No markers here', 'Nothing to see']
    expect(scanForMarkers(lines, 'session-1')).toHaveLength(0)
  })

  it('populates capturedAt and sessionName', () => {
    const lines = [`###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Done`]
    const markers = scanForMarkers(lines, 'my-session')
    expect(markers[0].sessionName).toBe('my-session')
    expect(markers[0].capturedAt).toBeTruthy()
  })
})

describe('MarkerDeduplicator', () => {
  it('accepts new markers', () => {
    const dedup = new MarkerDeduplicator()
    const marker = {
      type: 'DONE' as const,
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      text: 'Done',
      capturedAt: new Date().toISOString(),
      sessionName: 'test',
    }
    expect(dedup.isNew(marker)).toBe(true)
  })

  it('rejects duplicate markers', () => {
    const dedup = new MarkerDeduplicator()
    const marker = {
      type: 'DONE' as const,
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      text: 'Done',
      capturedAt: new Date().toISOString(),
      sessionName: 'test',
    }
    dedup.isNew(marker)
    expect(dedup.isNew(marker)).toBe(false)
  })

  it('allows same taskId with different text', () => {
    const dedup = new MarkerDeduplicator()
    const marker1 = {
      type: 'DONE' as const,
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      text: 'First attempt',
      capturedAt: new Date().toISOString(),
      sessionName: 'test',
    }
    const marker2 = {
      ...marker1,
      text: 'Second attempt',
    }
    expect(dedup.isNew(marker1)).toBe(true)
    expect(dedup.isNew(marker2)).toBe(true)
  })

  it('clear resets the deduplicator', () => {
    const dedup = new MarkerDeduplicator()
    const marker = {
      type: 'DONE' as const,
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      text: 'Done',
      capturedAt: new Date().toISOString(),
      sessionName: 'test',
    }
    dedup.isNew(marker)
    dedup.clear()
    expect(dedup.isNew(marker)).toBe(true)
  })

  it('tracks size correctly', () => {
    const dedup = new MarkerDeduplicator()
    expect(dedup.size).toBe(0)
    dedup.isNew({
      type: 'DONE', taskId: '550e8400-e29b-41d4-a716-446655440000',
      text: 'A', capturedAt: '', sessionName: '',
    })
    expect(dedup.size).toBe(1)
  })
})

describe('stripAnsi', () => {
  it('removes basic ANSI color codes', () => {
    expect(stripAnsi('\x1b[32mgreen text\x1b[0m')).toBe('green text')
  })

  it('removes complex ANSI sequences', () => {
    expect(stripAnsi('\x1b[1;32;40mbold green on black\x1b[0m')).toBe('bold green on black')
  })

  it('leaves plain text untouched', () => {
    expect(stripAnsi('hello world')).toBe('hello world')
  })

  it('handles empty string', () => {
    expect(stripAnsi('')).toBe('')
  })
})

describe('formatMarker', () => {
  it('formats a DONE marker', () => {
    const result = formatMarker('DONE', '550e8400-e29b-41d4-a716-446655440000', 'Task done')
    expect(result).toBe('###HMP/1 DONE 550e8400-e29b-41d4-a716-446655440000 Task done')
  })

  it('formats a BLOCKED marker', () => {
    const result = formatMarker('BLOCKED', '550e8400-e29b-41d4-a716-446655440000', 'Blocked')
    expect(result).toBe('###HMP/1 BLOCKED 550e8400-e29b-41d4-a716-446655440000 Blocked')
  })

  it('round-trips through parseMarkerLine', () => {
    const uuid = '550e8400-e29b-41d4-a716-446655440000'
    const text = 'Round trip test'
    const formatted = formatMarker('DONE', uuid, text)
    const parsed = parseMarkerLine(formatted, 'test')
    expect(parsed).toEqual({ type: 'DONE', taskId: uuid, text })
  })
})
