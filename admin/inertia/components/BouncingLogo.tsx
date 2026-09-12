/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌​‌​‌​‌​‌​‌​‌​‌‌​​‌​‌‌​​‌‌‌​‌​​‌​‌​​‌‌‌​​‌​​‌​​‌​‌‌​‌‌​‌‌‌​​‌‌‌​‌‌‌​‌‌‌​‌‌‌​‌‌​‌‌​​​‌‌​‌‌‌​​‌‌​‌‌​‌​‌‌‌​‌​​​‌‌‌‌​​‌​‌​​‌​‌​​‌​‌​​‌‌​‌​‌‌​‌​​​‌‌​​​​​‌​‌​​‌​​‌​‌‌​​‌​‌‌‌​‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.mUYgJrKnwwlnmtyJSZ0RYu
 */
import { useState, useEffect } from 'react';

// Fading Image Component
const FadingImage = ({  alt = "Fading image", className = "" }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [shouldShow, setShouldShow] = useState(true);

  useEffect(() => {
    // Start fading out after 2 seconds
    const fadeTimer = setTimeout(() => {
      setIsVisible(false);
    }, 2000);

    // Remove from DOM after fade out completes
    const removeTimer = setTimeout(() => {
      setShouldShow(false);
    }, 3000);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(removeTimer);
    };
  }, []);

  if (!shouldShow) {
    return null;
  }

  return (
    <div className={`fixed inset-0 flex justify-center items-center bg-desert-sand z-50 pointer-events-none transition-opacity duration-1000 ${
      isVisible ? 'opacity-100' : 'opacity-0'
    }`}>
      <img
        src={`/cairn_logo.svg`}
        alt={alt}
        className={`w-64 h-64 ${className}`}
      />
    </div>
  );
};

export default FadingImage;