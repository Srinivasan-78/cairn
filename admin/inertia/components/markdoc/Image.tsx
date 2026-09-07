/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​​‌​​‌‌​​‌‌​​‌‌​‌​‌​‌​‌‌​​‌​‌‌​‌​‌​​‌​​‌​‌​​‌​​​‌​‌​‌‌​​‌​​​​‌‌​‌​‌​‌​‌​‌‌‌​‌​‌​​‌‌​​‌‌‌​​‌​‌​‌‌​​‌​‌​​‌​​​​‌​​​​‌​​‌​​​​​‌​‌​​​‌‌​​‌​​​‌‌‌​‌​​​​‌​​‌‌​​​‌‌​​‌‌​​‌​​‌​‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.a35YjJEd5WS9YHBAFGBc2P
 */
export function Image({ src, alt, title }: { src: string; alt?: string; title?: string }) {
  return (
    <figure className="my-8">
      <div className="overflow-hidden rounded-lg border border-desert-tan-lighter shadow-md">
        <img
          src={src}
          alt={alt || ''}
          title={title}
          className="w-full h-auto"
          loading="lazy"
        />
      </div>
      {alt && (
        <figcaption className="mt-3 text-center text-sm text-desert-stone italic">
          {alt}
        </figcaption>
      )}
    </figure>
  )
}
