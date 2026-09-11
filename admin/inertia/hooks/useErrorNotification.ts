/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​‌​​​‌‌​​​‌​​‌‌​‌​‌​‌‌‌​​​‌​‌​‌‌‌‌‌​‌‌​​‌‌​​‌‌‌​​​​​​‌‌​‌‌​​‌‌​‌‌​​​‌​‌‌​‌​​‌​‌‌​​​​‌​‌​​‌​​‌​​‌​‌‌​‌​‌‌​​​​‌​‌​‌​‌​‌‌‌​‌​​​‌‌​‌​‌‌​‌​‌​‌​​​‌​​‌​‌‌​‌‌‌‌​​​​‌​​​​‌​​​‌‌​‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.b15q_fp6lZXRKXUtkTKxB6
 */
// Helper hook to show error notifications
import { useNotifications } from '../context/NotificationContext';

const useErrorNotification = () => {
  const { addNotification } = useNotifications();

  const showError = (message: string) => {
    addNotification({ message, type: 'error' });
  };

  return { showError };
};

export default useErrorNotification;
