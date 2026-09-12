/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​‌‌​‌‌​​​​‌​​‌‌​​‌​​‌‌‌​​‌​​‌​‌‌‌‌‌​‌‌​​‌​​​‌‌‌​‌‌‌​‌​‌​‌​​​‌​​​​‌‌​‌‌​‌​​​​‌​​​‌‌​​‌‌‌​‌​‌​‌‌‌​​​​​‌‌‌​​​‌​​‌‌​‌‌‌​‌‌​‌‌​​​‌​‌​​‌‌​‌‌​​‌​‌​‌​​‌​​‌​​‌‌​​​​​​‌‌​‌‌‌​‌‌​‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.ca2r_dwTChFupq7lSeI07h
 */

export const streamToString = async (stream: NodeJS.ReadableStream): Promise<string> => {
    const chunks: Buffer[] = [];
    for await (const chunk of stream) {
        chunks.push(Buffer.from(chunk));
    }
    return Buffer.concat(chunks).toString('utf-8');
};