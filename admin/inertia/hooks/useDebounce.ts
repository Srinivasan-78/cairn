/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​‌​​‌​​‌‌‌​​‌‌​‌​‌‌​‌‌​‌‌‌​​‌‌‌​​‌​​‌​​‌‌‌‌​​‌​‌‌​‌​‌​​‌‌‌​​‌‌‌‌​​‌​​‌‌​​​​​‌‌​​‌‌​​‌‌​​‌​​​‌‌‌‌​​​​​‌‌​​‌​​​‌‌​​​​​​‌‌​‌‌​​‌​​‌​​​​​‌‌‌​​‌​​‌‌​‌​​​‌​‌​‌​​​‌​‌‌‌‌‌​‌​‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.zNknrO-Ny0fdx206H94T_T
 */
import { useRef, useEffect } from "react";

const useDebounce = () => {
  const timeout = useRef<number | undefined>(400);

  const debounce =
    (func: Function, wait: number = 0) =>
    (...args: any[]) => {
      clearTimeout(timeout.current);
      timeout.current = window.setTimeout(() => func(...args), wait);
    };

  useEffect(() => {
    return () => {
      if (!timeout.current) return;
      clearTimeout(timeout.current);
    };
  }, []);

  return { debounce };
};

export default useDebounce;
