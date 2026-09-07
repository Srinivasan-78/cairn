/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌​‌​​‌‌​​‌‌​‌‌​​‌​‌​‌​​‌​​‌​‌‌‌‌​‌​​‌‌​‌‌​‌​‌​​‌‌‌​​‌‌‌​‌​‌​‌‌‌​​‌​​‌​​​‌‌‌​‌​​​‌​​​‌​​‌‌‌​​​‌‌​​​‌​‌‌‌​‌​‌​‌‌​‌​‌‌​‌‌​​​​‌​‌​​‌​‌​​​‌‌​‌​​​​‌‌​‌‌‌​‌​​​​​‌​‌‌​‌​‌​​‌​​​‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.e3eIzmNurGDN1ukaJ47AjE
 */
import api from "~/lib/api"
import { CheckLatestVersionResult } from "../../types/system"
import { useQuery } from "@tanstack/react-query"


export const useUpdateAvailable = () => {
    const queryData = useQuery<CheckLatestVersionResult | undefined>({
        queryKey: ['system-update-available'],
        queryFn: () => api.checkLatestVersion(),
        refetchInterval: Infinity, // Disable automatic refetching
        refetchOnWindowFocus: false,
    })

    return queryData.data
}