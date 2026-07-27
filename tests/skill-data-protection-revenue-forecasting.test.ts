import { describe, it, expect } from 'vitest'
import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

const SKILL_DIR = path.resolve(__dirname, '../.agents/skills/data-protection-revenue-forecasting')
const ENGINE_DIR = path.join(SKILL_DIR, 'engine')

const REFERENCES = [
  'variable-taxonomy.md',
  'with-order-flow.md',
  'without-order-flow.md',
  'probability-and-calibration.md',
  'demand-drivers-and-alt-data.md',
  'profit-levers.md',
  'company-profiles.md',
]

function hasPython(): boolean {
  try {
    execFileSync('python3', ['-c', 'import numpy'], { stdio: 'ignore' })
    return true
  } catch {
    return false
  }
}

describe('data-protection-revenue-forecasting skill', () => {
  it('has a SKILL.md with valid frontmatter', () => {
    const skillPath = path.join(SKILL_DIR, 'SKILL.md')
    expect(existsSync(skillPath)).toBe(true)

    const content = readFileSync(skillPath, 'utf-8')
    const match = content.match(/^---\n([\s\S]*?)\n---\n/)
    expect(match).not.toBeNull()

    const frontmatter = match![1]
    expect(frontmatter).toContain('name: data-protection-revenue-forecasting')
    expect(frontmatter).toMatch(/^description: .+/m)

    // The description is the only thing an agent sees when deciding whether to load the
    // skill, so it has to stay specific and third-person.
    const description = frontmatter.match(/description: (.+)/)![1]
    expect(description.length).toBeGreaterThan(80)
    expect(description.length).toBeLessThan(1024)
    expect(description.toLowerCase()).toContain('forecast')
  })

  it('ships every reference file that SKILL.md links to', () => {
    const content = readFileSync(path.join(SKILL_DIR, 'SKILL.md'), 'utf-8')
    for (const ref of REFERENCES) {
      expect(existsSync(path.join(SKILL_DIR, 'references', ref))).toBe(true)
      expect(content).toContain(`references/${ref}`)
    }
  })

  it('ships the runnable engine, its tests, and the worked example', () => {
    for (const file of ['dpforecast.py', 'test_dpforecast.py', 'example_outside_in.py']) {
      expect(existsSync(path.join(ENGINE_DIR, file))).toBe(true)
    }
  })

  it('keeps the engine dependency-light: numpy only, no hard scipy import', () => {
    const source = readFileSync(path.join(ENGINE_DIR, 'dpforecast.py'), 'utf-8')
    const topLevelImports = source
      .split('\n')
      .filter((line) => /^(import|from) /.test(line))
      .join('\n')
    expect(topLevelImports).toContain('import numpy as np')
    // pandas / sklearn / statsmodels would break the "runs anywhere" promise.
    expect(topLevelImports).not.toMatch(/\b(pandas|sklearn|scikit|statsmodels|matplotlib)\b/)
    // scipy is optional and must stay inside a try/except.
    expect(source).toMatch(/try:[\s\S]{0,200}from scipy\.special import/)
  })
})

describe.runIf(hasPython())('data-protection-revenue-forecasting engine', () => {
  it('passes its own self-test suite', () => {
    const output = execFileSync('python3', ['test_dpforecast.py'], {
      cwd: ENGINE_DIR,
      encoding: 'utf-8',
    })
    expect(output).toContain('all self-tests passed')
    expect(output).not.toContain('FAIL')
  }, 120_000)

  it('runs the worked example end to end and emits the full output contract', () => {
    const output = execFileSync('python3', ['example_outside_in.py'], {
      cwd: ENGINE_DIR,
      encoding: 'utf-8',
    })
    for (const section of [
      '1. HEADLINE',
      '2. THE SPLIT',
      '3. DECOMPOSITION',
      '4. MOST SENSITIVE ASSUMPTIONS',
      '5. ASSUMPTION REGISTER',
      '6. SCORING PLAN',
    ]) {
      expect(output).toContain(section)
    }
    // Iron Rule #2: never a point estimate alone.
    expect(output).toMatch(/80% interval \$\d+M to \$\d+M/)
  }, 120_000)
})
