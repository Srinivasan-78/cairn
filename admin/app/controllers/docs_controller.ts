/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​‌‌​‌‌‌‌​​​​‌‌‌​​​‌​‌‌​​​‌‌​​‌‌‌​​​​‌‌‌​​‌‌​​‌‌​​‌‌​‌‌​​‌​​​‌​​‌​‌​​‌‌​‌​‌​​‌‌‌​‌‌​​​‌‌​​​‌​‌‌​​‌​​​‌​​‌​​‌​​‌​‌‌​‌​​‌‌​​‌‌​​‌‌​​‌‌​‌​‌​​​‌​‌​​‌​‌‌​‌​​​​​‌​‌​‌‌​‌​​‌‌​​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.cxqc8s3dJjv1dI-33QKAZc
 */
import { DocsService } from '#services/docs_service'
import { inject } from '@adonisjs/core'
import type { HttpContext } from '@adonisjs/core/http'

@inject()
export default class DocsController {
    constructor(
        private docsService: DocsService
    ) { }

    async list({ }: HttpContext) {
        return await this.docsService.getDocs();
    }

    async show({ params, inertia }: HttpContext) {
        const content = await this.docsService.parseFile(params.slug);
        return inertia.render('docs/show', {
            content,
        });
    }
}