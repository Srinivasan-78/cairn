import type { BenchmarkType } from '../../types/benchmark'

/**
 * How a benchmark result's headline score should be presented. A partial run
 * (System Only / AI Only) is NOT the Cairn Score -- the Cairn Score is the full
 * benchmark composite -- so partial results are relabelled and flagged to avoid
 * users mistaking a partial number for their Cairn Score. The stored score for
 * a partial run is already renormalized to that category's own 0-100 range
 * (see BenchmarkService._calculateCairnScore).
 */
export function getScoreDisplay(type: BenchmarkType): {
  label: string
  isPartial: boolean
  /** Which full benchmark to run to get the real Cairn Score, for the CTA copy. */
  cta: string
} {
  switch (type) {
    case 'system':
      return {
        label: 'System Score',
        isPartial: true,
        cta: 'This is a partial result, not your Cairn Score. Run a Full Benchmark to get your Cairn Score.',
      }
    case 'ai':
      return {
        label: 'AI Score',
        isPartial: true,
        cta: 'This is a partial result, not your Cairn Score. Run a Full Benchmark to get your Cairn Score.',
      }
    default:
      return { label: 'Cairn Score', isPartial: false, cta: '' }
  }
}
