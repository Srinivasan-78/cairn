/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌​‌‌​‌​​‌​‌‌​‌​​‌‌​​​‌​‌​‌​‌‌‌​‌​​‌​‌​​‌‌​‌​​‌​‌‌‌​​​​​‌‌​‌‌‌‌​‌​‌‌​‌​​‌‌​​‌​‌​‌‌‌​‌​​​‌‌​​‌‌​​‌‌​‌‌​​​‌​‌​‌​‌​​‌‌​​​‌​‌​​‌‌​‌​‌​​‌‌‌‌​‌​​​​‌‌​‌‌‌‌​‌​​‌‌‌‌​​‌​‌‌​​​‌​​‌​‌‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.--1WJipoZetflU1MOCzyb_
 */

export default function classNames(...classes: (string | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}