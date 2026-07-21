import * as React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'danger' | 'critical' | 'success' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'secondary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={twMerge(
          clsx(
            // Base enterprise style: sharp focus ring, letter-spacing, uppercase feel for secondary actions
            'inline-flex items-center justify-center font-semibold transition-all duration-150',
            'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent focus-visible:ring-offset-1 focus-visible:ring-offset-background',
            'disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
            {
              // Rounded constraints: rounded-xl
              'rounded-xl': true,
              
              // Variants matching palette
              'bg-primary text-text-primary hover:bg-blue-700 shadow-sm': variant === 'primary',
              'bg-card border border-border text-text-primary hover:bg-border/30 hover:border-text-secondary/30': variant === 'secondary',
              'bg-transparent border border-accent/30 text-accent hover:bg-accent/10 hover:border-accent': variant === 'accent',
              'bg-danger text-text-primary hover:bg-red-700': variant === 'danger',
              'bg-critical text-text-primary hover:bg-red-950 border border-critical glow-critical': variant === 'critical',
              'bg-success text-text-primary hover:bg-green-700': variant === 'success',
              'bg-transparent text-text-secondary hover:bg-border/20 hover:text-text-primary': variant === 'ghost',

              // Sizes
              'px-3 py-1.5 text-xs gap-1.5': size === 'sm',
              'px-4 py-2 text-sm gap-2': size === 'md',
              'px-6 py-3 text-base gap-2.5': size === 'lg',
            },
            className
          )
        )}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
