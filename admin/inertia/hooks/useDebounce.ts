import { useRef, useEffect, useCallback } from "react";

const useDebounce = () => {
  const timeout = useRef<number | undefined>(undefined);

  const debounce = useCallback(
    (func: Function, wait: number = 0) =>
      (...args: any[]) => {
        clearTimeout(timeout.current);
        timeout.current = window.setTimeout(() => func(...args), wait);
      },
    []
  );

  useEffect(() => {
    return () => {
      if (!timeout.current) return;
      clearTimeout(timeout.current);
    };
  }, []);

  return { debounce };
};

export default useDebounce;
