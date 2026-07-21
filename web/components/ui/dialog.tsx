import * as React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Dialog = ({ isOpen, onClose, title, description, children, size = 'md' }: DialogProps) => {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleEscape);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className={twMerge(
              clsx(
                'relative w-full max-h-[85vh] bg-card border border-border shadow-xl rounded-xl flex flex-col overflow-hidden',
                {
                  'max-w-sm': size === 'sm',
                  'max-w-md': size === 'md',
                  'max-w-lg': size === 'lg',
                  'max-w-2xl': size === 'xl',
                }
              )
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border/30">
              <div>
                <h3 className="text-sm font-semibold tracking-wider uppercase text-text-primary">{title}</h3>
                {description && <p className="text-xs text-muted mt-0.5">{description}</p>}
              </div>
              <button
                onClick={onClose}
                className="text-text-secondary hover:text-text-primary p-1 rounded-sm hover:bg-border/20 transition-all focus-visible:outline-none"
              >
                <X size={16} />
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 p-4 overflow-y-auto min-h-0 text-sm leading-relaxed text-text-secondary">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  position?: 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
}

export const Drawer = ({ isOpen, onClose, title, description, children, position = 'right', size = 'md' }: DrawerProps) => {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleEscape);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  const widthClass = twMerge(
    clsx(
      'relative h-full bg-card border-border shadow-xl flex flex-col',
      position === 'left' ? 'border-r' : 'border-l',
      {
        'w-80': size === 'sm',
        'w-[450px] max-w-full': size === 'md',
        'w-[600px] max-w-full': size === 'lg',
      }
    )
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Drawer Wrapper */}
          <div className={twMerge('relative z-10 flex h-full ml-auto', position === 'left' && 'mr-auto ml-0')}>
            <motion.div
              initial={{ x: position === 'right' ? '100%' : '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: position === 'right' ? '100%' : '-100%' }}
              transition={{ type: 'tween', ease: 'easeInOut', duration: 0.25 }}
              className={widthClass}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border/30">
                <div>
                  <h3 className="text-sm font-semibold tracking-wider uppercase text-text-primary">{title}</h3>
                  {description && <p className="text-xs text-muted mt-0.5">{description}</p>}
                </div>
                <button
                  onClick={onClose}
                  className="text-text-secondary hover:text-text-primary p-1 rounded-sm hover:bg-border/20 transition-all focus-visible:outline-none"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 p-4 overflow-y-auto min-h-0 text-sm leading-relaxed text-text-secondary">
                {children}
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};
