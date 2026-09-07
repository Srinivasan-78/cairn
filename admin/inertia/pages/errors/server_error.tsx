/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌​‌​‌​​​​‌​​‌‌​‌​​‌​‌​​‌‌​​​‌‌‌​‌‌​​​‌‌​​​‌​‌‌​‌‌​‌​​‌‌​‌‌‌​‌​‌​‌‌​​‌​​‌​​​​‌​​‌​‌​​‌​‌​‌​‌​‌‌‌‌​​​​‌​​‌​​‌​​‌‌​‌​​​‌‌‌‌​​‌​‌​‌​‌‌​​​‌‌‌​​​​‌​​​​‌‌​‌‌​‌‌‌‌​‌‌‌​‌‌‌​‌​‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.5BiLv1m7VHJUxI4yV8CowT
 */
export default function ServerError(props: { error: any }) {
  return (
    <>
      <div className="container">
        <div className="title">Server Error</div>

        <span>{props.error.message}</span>
      </div>
    </>
  )
}