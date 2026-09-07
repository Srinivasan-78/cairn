#!/bin/bash
# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌‌​​‌‌‌​​‌‌​‌‌​‌​‌​​‌​​​‌‌​​‌​‌‌​​‌​‌​​‌​​‌​‌​‌​​‌‌​‌‌​‌‌‌‌​‌‌​‌​​‌​‌‌​‌‌‌‌​‌‌​​​​‌​‌‌‌​​‌‌​​‌​‌‌​‌​‌​‌​​‌​​​‌‌​‌‌‌​‌​‌‌‌‌‌​​‌‌​‌​‌​‌‌​‌​​​​‌‌​‌‌‌​​‌​‌​​​​​‌‌​​​‌​​‌​‌​​​‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.nsjFYISoioas-R7_5hnPbQ

echo "Finding Cairn containers..."

# -a to include all containers (running and stopped)
containers=$(docker ps -a --filter "name=^cairn_" --format "{{.Names}}")

if [ -z "$containers" ]; then
    echo "No containers found for Cairn Is it installed?"
    exit 0
fi

echo "Found the following containers:"
echo "$containers"
echo ""

for container in $containers; do
    echo "Starting container: $container"
    if docker start "$container"; then
        echo "✓ Successfully started $container"
    else
        echo "✗ Failed to start $container"
    fi
    echo ""
done

echo "Finished initiating start of all Cairn containers."
