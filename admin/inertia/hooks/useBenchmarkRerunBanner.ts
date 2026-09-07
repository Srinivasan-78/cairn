/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​​​​‌​‌‌​‌​​‌‌‌​‌‌​​‌‌​​‌​‌​‌‌​‌‌​​​‌‌​‌‌‌​​‌‌​‌​​‌​‌‌‌​​​‌​‌​‌​‌​‌​‌‌‌​‌‌‌​‌​​‌​​​​​‌​‌‌​‌​​‌‌​‌​‌​‌‌​‌‌​​​‌‌​‌‌​‌​​‌‌​‌‌​​‌‌‌​​​​​‌‌‌‌​​‌​‌‌‌​​​‌​‌‌​‌​‌​​‌​‌​‌‌‌​‌‌‌​​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.pZvelniqUwH-5lm6pyqjWr
 */
import api from "~/lib/api"
import { useQuery } from "@tanstack/react-query"

export const BENCHMARK_RERUN_BANNER_QUERY_KEY = ['benchmark-rerun-banner']

export const useBenchmarkRerunBanner = () => {
    const queryData = useQuery<{ show: boolean } | undefined>({
        queryKey: BENCHMARK_RERUN_BANNER_QUERY_KEY,
        queryFn: () => api.checkBenchmarkRerunBanner(),
        refetchInterval: Infinity, // Disable automatic refetching
        refetchOnWindowFocus: false,
    })

    return queryData.data
}
