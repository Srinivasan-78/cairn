# @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​​​‌​‌​​​​​‌​​‌‌‌​​​​​‌‌​‌‌​​‌‌​‌​​‌​‌​​​​‌​​​‌‌​‌​‌​‌‌​​‌​​​‌‌​‌‌‌​​‌​​​​‌‌​‌​​‌​​‌​‌​​‌‌‌‌​‌​​​‌​​​‌‌‌​​​‌​‌​​​‌‌‌​‌​​‌‌​‌​‌​​‌‌​​​‌‌​‌‌‌​​‌‌‌‌​​‌​‌​​​​‌​​‌​​​‌‌‌​‌​‌​‌‌‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.QA86iB5dnCIODqGMLnyBGW
FROM alpine:3.20
RUN apk add --no-cache util-linux bash
COPY collect-disk-info.sh /usr/local/bin/collect-disk-info.sh
RUN chmod +x /usr/local/bin/collect-disk-info.sh && mkdir -p /storage
WORKDIR /storage
CMD ["/usr/local/bin/collect-disk-info.sh"]
