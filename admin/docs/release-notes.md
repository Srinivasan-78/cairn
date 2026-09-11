<!--
  @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌‌​​‌‌​‌‌​​‌​​‌‌​‌​‌​​‌‌​​​‌​​‌​‌​​‌​​‌​​‌​‌‌‌‌​​​​‌​‌​‌​‌​‌​‌​​‌​​‌‌​‌​​‌​​‌‌​‌​​​​‌‌​‌​‌​‌‌​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​‌​‌‌‌‌​‌​​‌​​‌​‌‌​‌‌​‌‌‌‌​​‌‌​​​‌​‌‌‌​​​‌​‌‌‌‌​​​​‌​‌​‌‌​⁠
  Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
  Author: https://github.com/Srinivasan-78
  SPDX-License-Identifier: MIT
  Fingerprint: AMK1.36MLJIxURi45giuzKo1qxV
-->
# Release Notes

Cairn is a fork of [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad).
This file tracks changes made in Cairn. For the history before the fork, see the
[upstream release notes](https://github.com/Crosstalk-Solutions/project-nomad/blob/main/admin/docs/release-notes.md).

## Unreleased

### Changed
- Forked from Project NOMAD at upstream `v1.34.1` (commit `f8e40fb`).
- Rebranded the project to **Cairn**: renamed identifiers, install scripts, docs, and the
  in-app custom-instructions file (`NOMAD.md` -> `CAIRN.md`).
- Removed upstream marks and hosted services (logo, `projectnomad.us`, Discord, benchmark
  leaderboard, `api.projectnomad.us`, `ghcr.io/crosstalk-solutions/*` images). Hosted-service
  URLs now point at the reserved `cairn.example` domain and are non-functional placeholders.
- Added `NOTICE` with attribution and the list of modifications; kept `LICENSE` (Apache-2.0).

### Known gaps
- Container images referenced by the auto-updater and benchmark do not exist yet; those
  features are inert until Cairn publishes its own images and backends.
- Logo and favicons are placeholders.
