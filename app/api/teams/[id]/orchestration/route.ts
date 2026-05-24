/**
 * POST /api/teams/[id]/orchestration — Enable orchestration for a team
 * DELETE /api/teams/[id]/orchestration — Disable orchestration for a team
 *
 * Validates that all worker agents exist and are Hermes agents.
 */
import { NextRequest, NextResponse } from 'next/server'
import { loadTeams, saveTeams } from '@/lib/team-registry'
import { getAgent, loadAgents } from '@/lib/agent-registry'
import { validateOrchestrationConfig, applyConfigDefaults } from '@/lib/orchestration-config'
import { orchestrationService } from '@/services/orchestration-service'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id: teamId } = await params
    const body = await request.json()

    // Validate the config structure
    const validation = validateOrchestrationConfig(body)
    if (!validation.valid) {
      return NextResponse.json(
        { error: 'Invalid orchestration config', details: validation.errors },
        { status: 400 },
      )
    }

    // Apply defaults
    const config = applyConfigDefaults(body)

    // Validate all worker agents exist and are Hermes agents
    const agentErrors: string[] = []
    for (const worker of config.workers) {
      const agent = getAgent(worker.agentId)
      if (!agent) {
        agentErrors.push(`Agent "${worker.agentId}" not found`)
        continue
      }
      if (agent.program !== 'hermes') {
        agentErrors.push(`Agent "${agent.name}" (id: ${worker.agentId}) has program "${agent.program}", not "hermes". Only Hermes agents are supported in v1.`)
      }
    }

    if (agentErrors.length > 0) {
      return NextResponse.json(
        { error: 'Worker validation failed', details: agentErrors },
        { status: 400 },
      )
    }

    // Update the team with orchestration config
    const teams = loadTeams()
    const teamIndex = teams.findIndex(t => t.id === teamId)
    if (teamIndex === -1) {
      return NextResponse.json({ error: 'Team not found' }, { status: 404 })
    }

    teams[teamIndex] = {
      ...teams[teamIndex],
      orchestration: config,
      updatedAt: new Date().toISOString(),
    }

    saveTeams(teams)

    // Reload the orchestration service to pick up the new config
    orchestrationService.reload()

    // Log warnings
    if (validation.warnings.length > 0) {
      console.warn('[Orchestration] Config warnings:', validation.warnings)
    }

    console.log(`[Orchestration] Enabled for team "${teams[teamIndex].name}" (${teamId}) with ${config.workers.length} workers`)

    return NextResponse.json({
      message: 'Orchestration enabled',
      teamId,
      config,
      warnings: validation.warnings,
    })
  } catch (error: any) {
    console.error('[Orchestration] Error enabling orchestration:', error)
    return NextResponse.json(
      { error: 'Internal server error', message: error.message },
      { status: 500 },
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id: teamId } = await params

    const teams = loadTeams()
    const teamIndex = teams.findIndex(t => t.id === teamId)
    if (teamIndex === -1) {
      return NextResponse.json({ error: 'Team not found' }, { status: 404 })
    }

    if (!teams[teamIndex].orchestration) {
      return NextResponse.json(
        { error: 'Orchestration not configured for this team' },
        { status: 404 },
      )
    }

    // Remove orchestration config
    const { orchestration: _, ...teamWithoutOrchestration } = teams[teamIndex]
    teams[teamIndex] = {
      ...teamWithoutOrchestration,
      updatedAt: new Date().toISOString(),
    }

    saveTeams(teams)

    // Reload service
    orchestrationService.reload()

    console.log(`[Orchestration] Disabled for team "${teams[teamIndex].name}" (${teamId})`)

    return NextResponse.json({
      message: 'Orchestration disabled',
      teamId,
    })
  } catch (error: any) {
    console.error('[Orchestration] Error disabling orchestration:', error)
    return NextResponse.json(
      { error: 'Internal server error', message: error.message },
      { status: 500 },
    )
  }
}
