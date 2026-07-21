import { create } from 'zustand';
import { SystemNotification } from '../types';
import { MOCK_NOTIFICATIONS } from '../constants/dummyData';

interface NotificationsState {
  notifications: SystemNotification[];
  unreadCount: number;
  setNotifications: (notifications: SystemNotification[]) => void;
  addNotification: (notif: Omit<SystemNotification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotification: (id: string) => void;
}

export const useNotificationsStore = create<NotificationsState>((set, get) => {
  const getUnreadCount = (list: SystemNotification[]) => list.filter((n) => !n.read).length;

  return {
    notifications: MOCK_NOTIFICATIONS,
    unreadCount: getUnreadCount(MOCK_NOTIFICATIONS),

    setNotifications: (notifications) =>
      set({ notifications, unreadCount: getUnreadCount(notifications) }),

    addNotification: (notif) => {
      const newNotif: SystemNotification = {
        ...notif,
        id: `not-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        read: false,
      };
      const updated = [newNotif, ...get().notifications];
      set({ notifications: updated, unreadCount: getUnreadCount(updated) });
    },

    markAsRead: (id) => {
      const updated = get().notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      set({ notifications: updated, unreadCount: getUnreadCount(updated) });
    },

    markAllAsRead: () => {
      const updated = get().notifications.map((n) => ({ ...n, read: true }));
      set({ notifications: updated, unreadCount: 0 });
    },

    clearNotification: (id) => {
      const updated = get().notifications.filter((n) => n.id !== id);
      set({ notifications: updated, unreadCount: getUnreadCount(updated) });
    },
  };
});
