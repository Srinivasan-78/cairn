/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​​​​‌‌​‌​​​​‌‌‌​‌​​​‌‌​​‌​‌​‌​‌​​​‌​​‌‌​‌‌‌​‌​​​‌​‌​‌​‌​‌​‌​‌‌‌​‌‌​​‌‌‌​‌‌‌​‌‌​‌​‌​​‌​​‌‌​​​‌‌‌‌​‌​​‌​​‌‌‌​​‌‌‌​​‌‌​‌‌​​‌‌​​‌‌​​‌​‌​‌‌‌​‌‌‌​‌​​‌‌​‌​​‌‌‌​​​​‌​​​‌‌‌​‌​​​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.xhteQ7EUvwjLzNsfewM8GC
 */

export type DockerComposeServiceConfig = {
    image: string;
    container_name: string;
    restart: string;
    ports: string[];
    environment?: Record<string, string>;
    volumes?: string[];
    networks?: string[];
}