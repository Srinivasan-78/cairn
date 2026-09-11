#!/bin/bash
# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​​‌​​‌‌​‌​​​‌‌​​‌​​​‌‌​‌‌​‌​‌​‌‌‌‌‌​‌‌​‌‌‌​​​‌‌‌​​​​‌​​​‌​‌​​‌‌​‌‌‌​‌‌​​​​‌​‌​‌‌​‌​​‌​‌‌​‌​​‌‌​‌‌​‌​​‌‌​‌‌​​​‌‌‌​​‌​‌​​‌‌​‌​‌‌​​‌​​​‌​​‌‌​‌​‌‌‌​​​​​‌​​‌‌‌‌​‌​​​‌‌​​‌‌‌​‌​​⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.y4dm_n8E7aZZm69MdMpOFt

echo "Finding running Docker containers for Cairn.."

containers=$(docker ps --filter "name=^cairn_" --format "{{.Names}}")

if [ -z "$containers" ]; then
    echo "No running containers found for Cairn"
    exit 0
fi

echo "Found the following running containers:"
echo "$containers"
echo ""

for container in $containers; do
    echo "Gracefully stopping container: $container"
    if docker stop "$container"; then
        echo "✓ Successfully stopped $container"
    else
        echo "✗ Failed to stop $container"
    fi
    echo ""
done

echo "Finished initiating graceful shutdown of all Cairn containers."
