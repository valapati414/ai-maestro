/**
 * GET /api/orchestration/health — Health snapshot for orchestration service
 *
 * Returns the current state of the orchestration service.
 * Only accessible from localhost.
 */
import { NextRequest, NextResponse } from 'next/server'
import { orchestrationService } from '@/services/orchestration-service'

export async function GET(request: NextRequest) {
  // Restrict to localhost
  const host = request.headers.get('host') || ''
  const xForwardedFor = request.headers.get('x-forwarded-for') || ''
  const isLocalhost = host.startsWith('localhost') || host.startsWith('127.0.0.1') || xForwardedFor === '127.0.0.1'

  if (!isLocalhost) {
    return NextResponse.json({ error: 'Forbidden — localhost only' }, { status: 403 })
  }

  const health = orchestrationService.getHealth()
  return NextResponse.json(health)
}
