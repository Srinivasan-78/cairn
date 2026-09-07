/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​​‌​​‌​‌‌​‌​‌‌‌​‌​‌​‌‌‌​​​​​‌​​​‌‌‌​‌‌‌​​‌‌​​‌‌​​‌​​‌‌‌​​‌‌​‌​‌​​​‌​‌‌​​‌‌​​‌‌​​​‌‌​‌‌‌​‌​‌​​‌‌​​​‌​‌​‌‌​‌​​‌‌‌​​‌​​‌​​‌‌​‌​​‌‌​​‌​​‌​​‌‌‌‌​‌‌​​‌​​​‌‌​‌​​​​‌​​‌‌​‌​‌‌​‌​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.a-upGs2sQfcu1ZrM2OdhMj
 */
import * as assert from 'node:assert/strict'
import { test } from 'node:test'
import { resolve, join, sep } from 'node:path'

import { CollectionUpdateService } from '../../app/services/collection_update_service.js'
import { applyContentUpdateValidator } from '../../app/validators/common.js'
import { ZIM_STORAGE_PATH } from '../../app/utils/fs.js'

test('buildFilename rejects path traversal and separators in resource_id', () => {
  const service = new CollectionUpdateService()
  const maliciousIds = [
    '../../etc/x',
    '../x',
    '..\\windows\\win.ini',
    '/etc/passwd',
    'foo/bar',
    'foo\\bar',
    '..',
  ]

  for (const id of maliciousIds) {
    assert.throws(
      () =>
        service.buildFilename({
          resource_id: id,
          resource_type: 'zim',
          installed_version: '2026-01',
          latest_version: '2026-06',
          download_url: 'https://example.com/test.zim',
        }),
      /Invalid resource_id/,
      `Expected ${id} to be rejected in buildFilename`
    )
  }
})

test('buildFilename rejects path traversal and separators in latest_version', () => {
  const service = new CollectionUpdateService()
  const maliciousVersions = ['../../v1', '..', '1.0/evil', '1.0\\evil', '/root']

  for (const ver of maliciousVersions) {
    assert.throws(
      () =>
        service.buildFilename({
          resource_id: 'wikipedia_en_top_mini',
          resource_type: 'zim',
          installed_version: '2026-01',
          latest_version: ver,
          download_url: 'https://example.com/test.zim',
        }),
      /Invalid latest_version/,
      `Expected ${ver} to be rejected in buildFilename`
    )
  }
})

test('buildFilename builds valid filenames for safe identifiers', () => {
  const service = new CollectionUpdateService()

  assert.equal(
    service.buildFilename({
      resource_id: 'wikipedia_en_top_mini',
      resource_type: 'zim',
      installed_version: '2026-01',
      latest_version: '2026-06',
      download_url: 'https://example.com/test.zim',
    }),
    'wikipedia_en_top_mini_2026-06.zim'
  )

  assert.equal(
    service.buildFilename({
      resource_id: 'nhs.uk_en_medicines',
      resource_type: 'zim',
      installed_version: '2025-01',
      latest_version: '2025-12',
      download_url: 'https://example.com/test.zim',
    }),
    'nhs.uk_en_medicines_2025-12.zim'
  )

  assert.equal(
    service.buildFilename({
      resource_id: 'planet_osm',
      resource_type: 'map',
      installed_version: '2026-01',
      latest_version: '2026-02',
      download_url: 'https://example.com/test.pmtiles',
    }),
    'planet_osm_2026-02.pmtiles'
  )
})

test('buildFilepath asserts target path stays under storage root', () => {
  const service = new CollectionUpdateService()
  const expectedZimBase = resolve(join(process.cwd(), ZIM_STORAGE_PATH))

  const safeZimPath = service.buildFilepath(
    {
      resource_id: 'wikipedia_en_top_mini',
      resource_type: 'zim',
      installed_version: '2026-01',
      latest_version: '2026-06',
      download_url: 'https://example.com/test.zim',
    },
    'wikipedia_en_top_mini_2026-06.zim'
  )
  assert.equal(safeZimPath, resolve(join(expectedZimBase, 'wikipedia_en_top_mini_2026-06.zim')))
  assert.ok(safeZimPath.startsWith(expectedZimBase + sep))

  // Malicious filename escaping base
  assert.throws(
    () =>
      service.buildFilepath(
        {
          resource_id: 'safe_id',
          resource_type: 'zim',
          installed_version: '2026-01',
          latest_version: '2026-06',
          download_url: 'https://example.com/test.zim',
        },
        '../../etc/passwd'
      ),
    /Invalid filename/
  )
})

test('applyContentUpdateValidator rejects traversal payload in resource_id (regression test #1)', async () => {
  await assert.rejects(
    async () => {
      await applyContentUpdateValidator.validate({
        resource_id: '../../etc/x',
        resource_type: 'zim',
        installed_version: '2026-01',
        latest_version: '2026-06',
        download_url: 'https://example.com/file.zim',
      })
    },
    (err: any) => {
      return err && err.messages && err.messages.some((m: any) => m.field === 'resource_id')
    },
    'Should reject resource_id with traversal sequences'
  )
})

test('applyContentUpdateValidator rejects traversal payload in latest_version', async () => {
  await assert.rejects(
    async () => {
      await applyContentUpdateValidator.validate({
        resource_id: 'valid_id',
        resource_type: 'zim',
        installed_version: '2026-01',
        latest_version: '../../1.0',
        download_url: 'https://example.com/file.zim',
      })
    },
    (err: any) => {
      return err && err.messages && err.messages.some((m: any) => m.field === 'latest_version')
    },
    'Should reject latest_version with traversal sequences'
  )
})

test('applyContentUpdateValidator accepts valid update payload', async () => {
  const valid = await applyContentUpdateValidator.validate({
    resource_id: 'wikipedia_en_top_mini',
    resource_type: 'zim',
    installed_version: '2026-01',
    latest_version: '2026-06',
    download_url: 'https://download.kiwix.org/zim/wikipedia_en_top_mini_2026-06.zim',
    size_bytes: 1234567,
  })

  assert.equal(valid.resource_id, 'wikipedia_en_top_mini')
  assert.equal(valid.latest_version, '2026-06')
  assert.equal(valid.resource_type, 'zim')
})
