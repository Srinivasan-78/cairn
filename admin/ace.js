/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌​​‌‌​​‌​​​‌​​‌‌‌​​‌‌​‌​​​​‌​​​​‌‌​‌‌​‌‌‌‌​​‌‌​‌​‌​‌‌‌​​‌‌​​‌‌‌​​‌​‌​‌‌​‌​​‌‌​‌​​‌​‌​​​‌​‌​‌‌​‌‌‌‌​‌‌‌​‌‌​​‌​​​​​‌​‌​‌​‌‌​​‌‌​​​​‌​‌​​​​​‌​‌​​‌​‌​​‌‌​​​‌‌​‌‌​‌​​​​‌​‌‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.2dNhCo5s9ZiEovAVaAJch_
 */
/*
|--------------------------------------------------------------------------
| JavaScript entrypoint for running ace commands
|--------------------------------------------------------------------------
|
| DO NOT MODIFY THIS FILE AS IT WILL BE OVERRIDDEN DURING THE BUILD
| PROCESS.
|
| See docs.adonisjs.com/guides/typescript-build-process#creating-production-build
|
| Since, we cannot run TypeScript source code using "node" binary, we need
| a JavaScript entrypoint to run ace commands.
|
| This file registers the "ts-node/esm" hook with the Node.js module system
| and then imports the "bin/console.ts" file.
|
*/

/**
 * Register hook to process TypeScript files using ts-node-maintained
 */
import 'ts-node-maintained/register/esm'

/**
 * Import ace console entrypoint
 */
await import('./bin/console.js')
