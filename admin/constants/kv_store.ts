/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌‌​​‌‌‌​‌‌​​​‌‌​‌​‌​‌‌​​‌​​​‌‌‌‌​​​​‌​‌​​‌​​‌‌‌​‌‌​​‌​‌​​‌‌​‌‌‌​​​​​​‌‌​‌​​​‌‌​‌‌​‌​‌‌‌​‌​‌​‌‌‌​‌‌​​​‌‌​‌​‌​‌‌‌​‌​‌​‌‌‌​‌​‌​‌‌‌​​​​​‌​​‌‌​‌​‌​​​‌​​​‌​​​​‌​​‌​‌​​​​​‌‌​‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Nv5dxRvSp4muv5uupMDBPh
 */
import { KVStoreKey } from "../types/kv_store.js";

export const SETTINGS_KEYS: KVStoreKey[] = [
    'chat.suggestionsEnabled',
    'chat.lastModel',
    'ui.hasVisitedEasySetup',
    'ui.theme',
    'system.earlyAccess',
    'system.internetStatusTestUrl',
    'ai.assistantCustomName',
    'ai.remoteOllamaUrl',
    'ai.ollamaFlashAttention',
    'ai.autoThinking',
    'rag.defaultIngestPolicy',
    'autoUpdate.enabled',
    'autoUpdate.windowStart',
    'autoUpdate.windowEnd',
    'autoUpdate.cooloffHours',
    'appAutoUpdate.enabled',
    'contentAutoUpdate.enabled',
    'contentAutoUpdate.windowStart',
    'contentAutoUpdate.windowEnd',
    'contentAutoUpdate.cooloffHours',
    'contentAutoUpdate.maxBytesPerWindow',
    'benchmark.rerunBannerDismissed',
    'apps.homebox.apiKeyPepper'
];