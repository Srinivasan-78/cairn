/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​​​​​‌‌​‌‌‌​‌​‌​​‌​​‌‌‌​‌​‌​‌​‌​​​​​​‌‌‌​​​​‌​​‌‌​‌​​‌‌​‌‌‌​‌​​‌‌​‌​‌​‌​​‌​​‌‌‌​​​‌​‌‌​‌​​‌​‌‌​‌​‌​​‌‌‌​​​‌​‌‌‌​​‌‌​‌‌​​‌​​​‌‌​​​‌​​‌​‌​‌​​​‌‌‌​‌​‌​‌‌‌​‌‌‌​‌‌​​​​‌​‌‌​‌​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.x7RuP8M7MRqijqsdbTuwaj
 */
import { Exception } from '@adonisjs/core/exceptions'

export default class InternalServerErrorException extends Exception {
  static status = 500
  static code = 'E_INTERNAL_SERVER_ERROR'
}