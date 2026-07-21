import * as React from 'react';
import { twMerge } from 'tailwind-merge';

export interface TimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  category?: 'ALERT' | 'PERMIT' | 'SYSTEM' | 'MAINTENANCE';
  operatorName?: string;
}

interface TimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export const Timeline = ({ events, className }: TimelineProps) => {
  return (
    <div className={twMerge('relative border-l border-border/60 pl-4 py-2 space-y-6 font-mono text-xs', className)}>
      {events.map((event) => {
        const getMarkerColors = () => {
          switch (event.category) {
            case 'ALERT':
              return 'bg-danger border-danger/40';
            case 'PERMIT':
              return 'bg-success border-success/40';
            case 'MAINTENANCE':
              return 'bg-accent border-accent/40';
            default:
              return 'bg-muted border-border/40';
          }
        };

        return (
          <div key={event.id} className="relative group">
            {/* Timeline Circle Marker */}
            <span className={twMerge(
              'absolute -left-[21px] top-1 rounded-full w-2.5 h-2.5 border ring-4 ring-background transition-transform duration-150 group-hover:scale-125',
              getMarkerColors()
            )} />

            {/* Event Content */}
            <div className="space-y-1">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[10px] text-muted mb-0.5">
                <span>{new Date(event.timestamp).toLocaleString()}</span>
                {event.operatorName && <span className="uppercase font-semibold text-text-secondary">BY: {event.operatorName}</span>}
              </div>
              <h4 className="font-semibold text-text-primary text-xs uppercase tracking-wide">{event.title}</h4>
              <p className="text-text-secondary leading-relaxed font-sans">{event.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
