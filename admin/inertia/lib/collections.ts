/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​‌‌​‌‌‌‌​‌​​‌‌‌‌​​‌​‌​​‌‌‌​​‌‌​‌​​​​‌​​‌‌​​​‌‌​​‌‌‌​‌​‌‌​‌​​‌​‌​‌​‌​‌​‌​‌‌​​​‌‌​‌​​​‌​‌​‌‌‌​‌‌​‌‌‌‌​‌‌‌​‌​​​‌‌​​‌‌​​​‌‌​‌​‌​​‌‌​​‌​​‌​​‌‌​​​‌​​​‌‌‌​‌‌‌​‌​​​‌​​​‌‌‌​‌‌‌​‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.czyNhLgZUV4Wotf52LGtGu
 */
import type { SpecResource, SpecTier } from '../../types/collections'

/**
 * Resolve all resources for a tier, including inherited resources from includesTier chain.
 * Shared between frontend components (TierSelectionModal, CategoryCard, EasySetup).
 */
export function resolveTierResources(tier: SpecTier, allTiers: SpecTier[]): SpecResource[] {
  const visited = new Set<string>()
  return resolveTierResourcesInner(tier, allTiers, visited)
}

function resolveTierResourcesInner(
  tier: SpecTier,
  allTiers: SpecTier[],
  visited: Set<string>
): SpecResource[] {
  if (visited.has(tier.slug)) return [] // cycle detection
  visited.add(tier.slug)

  const resources: SpecResource[] = []

  if (tier.includesTier) {
    const included = allTiers.find((t) => t.slug === tier.includesTier)
    if (included) {
      resources.push(...resolveTierResourcesInner(included, allTiers, visited))
    }
  }

  resources.push(...tier.resources)
  return resources
}
