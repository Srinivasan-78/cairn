/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌​‌​‌‌‌​​‌​​‌‌‌​​​​​‌​‌​‌‌‌​‌​‌​‌‌​​​‌‌​​‌​​‌​​​​‌​​​‌‌‌​​‌​​‌‌​‌‌‌​‌‌​​‌​‌​​‌​‌‌​‌​‌‌​​​​‌​‌‌​‌​‌​​​‌‌‌​​‌​‌​​‌‌​‌​‌​​‌​​​​‌​​​‌‌​​‌‌​​‌‌‌​‌‌​​‌‌​​​‌‌​‌‌‌​​‌‌‌​​​​​‌‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.MrpWV2B97e-aj9MHFgf780
 */
import type { HttpContext } from '@adonisjs/core/http'
import { DownloadService } from '#services/download_service'
import { downloadJobsByFiletypeSchema } from '#validators/download'
import { inject } from '@adonisjs/core'

@inject()
export default class DownloadsController {
  constructor(private downloadService: DownloadService) {}

  async index() {
    return this.downloadService.listDownloadJobs()
  }

  async filetype({ request }: HttpContext) {
    const payload = await request.validateUsing(downloadJobsByFiletypeSchema)
    return this.downloadService.listDownloadJobs(payload.params.filetype)
  }

  async removeJob({ params }: HttpContext) {
    await this.downloadService.removeFailedJob(params.jobId)
    return { success: true }
  }

  async cancelJob({ params }: HttpContext) {
    return this.downloadService.cancelJob(params.jobId)
  }

  async retryJob({ params }: HttpContext) {
    return this.downloadService.retryFailedJob(params.jobId)
  }
}
