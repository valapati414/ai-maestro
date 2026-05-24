/**
 * Unit tests for orchestration-config.ts
 */
import { describe, it, expect } from 'vitest'
import {
  validateOrchestrationConfig,
  applyConfigDefaults,
  CONFIG_DEFAULTS,
} from '../lib/orchestration-config'

describe('validateOrchestrationConfig', () => {
  const validConfig = {
    enabled: true,
    workerSelection: 'round_robin',
    pollIntervalSeconds: 10,
    staleThresholdMinutes: 30,
    workers: [{ agentId: 'agent-1' }],
  }

  it('accepts a valid config', () => {
    const result = validateOrchestrationConfig(validConfig)
    expect(result.valid).toBe(true)
    expect(result.errors).toHaveLength(0)
  })

  it('rejects non-object input', () => {
    expect(validateOrchestrationConfig(null).valid).toBe(false)
    expect(validateOrchestrationConfig(undefined).valid).toBe(false)
    expect(validateOrchestrationConfig('string').valid).toBe(false)
    expect(validateOrchestrationConfig(42).valid).toBe(false)
  })

  it('rejects enabled !== true', () => {
    const result = validateOrchestrationConfig({ ...validConfig, enabled: false })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('enabled must be true when configuring orchestration')
  })

  it('rejects invalid workerSelection', () => {
    const result = validateOrchestrationConfig({ ...validConfig, workerSelection: 'invalid' })
    expect(result.valid).toBe(false)
  })

  it('accepts both round_robin and by_specialty', () => {
    expect(validateOrchestrationConfig({ ...validConfig, workerSelection: 'round_robin' }).valid).toBe(true)
    expect(validateOrchestrationConfig({ ...validConfig, workerSelection: 'by_specialty' }).valid).toBe(true)
  })

  it('rejects pollIntervalSeconds < 5', () => {
    const result = validateOrchestrationConfig({ ...validConfig, pollIntervalSeconds: 3 })
    expect(result.valid).toBe(false)
    expect(result.errors[0]).toContain('>= 5')
  })

  it('warns on very low pollIntervalSeconds', () => {
    const result = validateOrchestrationConfig({ ...validConfig, pollIntervalSeconds: 7 })
    expect(result.valid).toBe(true)
    expect(result.warnings.length).toBeGreaterThan(0)
  })

  it('warns on very high pollIntervalSeconds', () => {
    const result = validateOrchestrationConfig({ ...validConfig, pollIntervalSeconds: 120 })
    expect(result.valid).toBe(true)
    expect(result.warnings.some(w => w.includes('60s'))).toBe(true)
  })

  it('rejects staleThresholdMinutes < 1', () => {
    const result = validateOrchestrationConfig({ ...validConfig, staleThresholdMinutes: 0 })
    expect(result.valid).toBe(false)
  })

  it('rejects empty workers array', () => {
    const result = validateOrchestrationConfig({ ...validConfig, workers: [] })
    expect(result.valid).toBe(false)
    expect(result.errors[0]).toContain('non-empty')
  })

  it('rejects missing workers', () => {
    const { workers, ...noWorkers } = validConfig
    const result = validateOrchestrationConfig(noWorkers)
    expect(result.valid).toBe(false)
  })

  it('rejects duplicate agentIds', () => {
    const result = validateOrchestrationConfig({
      ...validConfig,
      workers: [{ agentId: 'a-1' }, { agentId: 'a-1' }],
    })
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.includes('duplicated'))).toBe(true)
  })

  it('rejects worker without agentId', () => {
    const result = validateOrchestrationConfig({
      ...validConfig,
      workers: [{ specialties: ['backend'] }],
    })
    expect(result.valid).toBe(false)
    expect(result.errors.some(e => e.includes('agentId'))).toBe(true)
  })

  it('rejects non-array specialties', () => {
    const result = validateOrchestrationConfig({
      ...validConfig,
      workers: [{ agentId: 'a-1', specialties: 'backend' }],
    })
    expect(result.valid).toBe(false)
  })

  it('accepts workers with specialties', () => {
    const result = validateOrchestrationConfig({
      ...validConfig,
      workers: [{ agentId: 'a-1', specialties: ['backend', 'typescript'] }],
    })
    expect(result.valid).toBe(true)
  })

  it('collects multiple errors at once', () => {
    const result = validateOrchestrationConfig({
      enabled: false,
      workerSelection: 'bad',
      pollIntervalSeconds: 1,
      staleThresholdMinutes: -1,
      workers: [],
    })
    expect(result.valid).toBe(false)
    expect(result.errors.length).toBeGreaterThanOrEqual(5)
  })
})

describe('applyConfigDefaults', () => {
  it('fills in missing fields with defaults', () => {
    const result = applyConfigDefaults({ workers: [{ agentId: 'a-1' }] })
    expect(result.enabled).toBe(true)
    expect(result.workerSelection).toBe('round_robin')
    expect(result.pollIntervalSeconds).toBe(CONFIG_DEFAULTS.pollIntervalSeconds)
    expect(result.staleThresholdMinutes).toBe(CONFIG_DEFAULTS.staleThresholdMinutes)
    expect(result.workers).toEqual([{ agentId: 'a-1' }])
  })

  it('preserves explicitly set values', () => {
    const result = applyConfigDefaults({
      enabled: true,
      workerSelection: 'by_specialty',
      pollIntervalSeconds: 15,
      staleThresholdMinutes: 60,
      workers: [{ agentId: 'a-1', specialties: ['frontend'] }],
    })
    expect(result.workerSelection).toBe('by_specialty')
    expect(result.pollIntervalSeconds).toBe(15)
    expect(result.staleThresholdMinutes).toBe(60)
  })

  it('does not mutate input', () => {
    const input = { workers: [{ agentId: 'a-1' }] }
    const result = applyConfigDefaults(input)
    expect(result).not.toBe(input)
    expect((input as any).enabled).toBeUndefined()
  })
})
