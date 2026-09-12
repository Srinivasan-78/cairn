# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌​‌​​‌‌‌​​​‌​‌​​​​​‌​‌​‌​​​​​‌‌‌‌​‌​​‌​‌‌‌‌‌​‌​‌​‌‌​​‌​‌​‌​​​‌‌​‌​​​​‌​​‌‌​‌​‌‌​​‌​​​‌​‌‌​​‌​‌​‌​‌​​​‌​​‌​‌‌​‌​‌​‌​‌​‌​​‌‌‌​​‌​‌‌​​​​‌‌‌​​‌​​‌​‌​‌‌​​‌​​​‌​‌​‌‌‌‌​​​​‌‌​​​‌‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.jqAPz_VThMdYTKUNXrVExc
FROM alpine:3.24

# Install Docker CLI for compose operations
RUN apk add --no-cache docker-cli docker-cli-compose bash jq

# Copy the update watcher script
COPY update-watcher.sh /usr/local/bin/update-watcher.sh
RUN chmod +x /usr/local/bin/update-watcher.sh

# Create shared communication directory
RUN mkdir -p /shared

WORKDIR /shared

CMD ["/usr/local/bin/update-watcher.sh"]
