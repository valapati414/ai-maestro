/**
 * Orchestration configuration validator
 *
 * Validates TeamOrchestrationConfig before enabling orchestration.
 * Ensures all worker agents exist, are Hermes agents, and config
 * values are within acceptable ranges.
 */

import type { TeamOrchestrationConfig } from '../types/team'

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/** Minimum and default values for config fields */
export const CONFIG_DEFAULTS = {
  pollIntervalSeconds: 10,
  staleThresholdMinutes: 30,
  minPollInterval: 5,
  minStaleThreshold: 1,
} as const

/**
 * Validate a TeamOrchestrationConfig object.
 *
 * Checks:
 * - Required fields are present
 * - pollIntervalSeconds >= 5
 * - staleThresholdMinutes >= 1
 * - workers array is non-empty
 * - worker agentIds are unique
 * - workerSelection is a valid value
 *
 * Does NOT check agent existence or program type — that requires
 * the agent registry and is done in the API route handler.
 */
export function validateOrchestrationConfig(config: unknown): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!config || typeof config !== 'object') {
    return { valid: false, errors: ['Config must be an object'], warnings }
  }

  const cfg = config as Record<string, unknown>

  // enabled
  if (cfg.enabled !== true) {
    errors.push('enabled must be true when configuring orchestration')
  }

  // workerSelection
  if (!cfg.workerSelection || !['round_robin', 'by_specialty'].includes(cfg.workerSelection as string)) {
    errors.push('workerSelection must be "round_robin" or "by_specialty"')
  }

  // pollIntervalSeconds
  const pollInterval = Number(cfg.pollIntervalSeconds)
  if (isNaN(pollInterval) || pollInterval < CONFIG_DEFAULTS.minPollInterval) {
    errors.push(`pollIntervalSeconds must be >= ${CONFIG_DEFAULTS.minPollInterval}`)
  } else if (pollInterval < CONFIG_DEFAULTS.pollIntervalSeconds) {
    warnings.push(`pollIntervalSeconds is below default (${CONFIG_DEFAULTS.pollIntervalSeconds}s); may cause high CPU usage`)
  } else if (pollInterval > 60) {
    warnings.push('pollIntervalSeconds > 60s; completion detection will be slow')
  }

  // staleThresholdMinutes
  const staleThreshold = Number(cfg.staleThresholdMinutes)
  if (isNaN(staleThreshold) || staleThreshold < CONFIG_DEFAULTS.minStaleThreshold) {
    errors.push(`staleThresholdMinutes must be >= ${CONFIG_DEFAULTS.minStaleThreshold}`)
  } else if (staleThreshold < 5) {
    warnings.push('staleThresholdMinutes < 5; may generate excessive stale warnings')
  }

  // workers
  if (!Array.isArray(cfg.workers) || cfg.workers.length === 0) {
    errors.push('workers must be a non-empty array')
  } else {
    const agentIds = new Set<string>()
    for (let i = 0; i < cfg.workers.length; i++) {
      const worker = cfg.workers[i] as Record<string, unknown>
      if (!worker || typeof worker !== 'object') {
        errors.push(`workers[${i}] must be an object`)
        continue
      }

      if (!worker.agentId || typeof worker.agentId !== 'string') {
        errors.push(`workers[${i}].agentId is required and must be a string`)
      } else {
        if (agentIds.has(worker.agentId)) {
          errors.push(`workers[${i}].agentId "${worker.agentId}" is duplicated`)
        }
        agentIds.add(worker.agentId)
      }

      if (worker.specialties !== undefined && !Array.isArray(worker.specialties)) {
        errors.push(`workers[${i}].specialties must be an array if provided`)
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Apply defaults to a config, filling in missing optional fields.
 * Returns a new object (does not mutate the input).
 */
export function applyConfigDefaults(config: Partial<TeamOrchestrationConfig>): TeamOrchestrationConfig {
  return {
    enabled: config.enabled ?? true,
    workerSelection: config.workerSelection ?? 'round_robin',
    pollIntervalSeconds: config.pollIntervalSeconds ?? CONFIG_DEFAULTS.pollIntervalSeconds,
    staleThresholdMinutes: config.staleThresholdMinutes ?? CONFIG_DEFAULTS.staleThresholdMinutes,
    workers: config.workers ?? [],
  }
}
