import * as React from 'react';
import { twMerge } from 'tailwind-merge';

export interface Column<T> {
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  className?: string;
}

interface DataTableProps<T> extends React.HTMLAttributes<HTMLTableElement> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  isLoading?: boolean;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No telemetry records located.',
  isLoading = false,
  className,
  ...props
}: DataTableProps<T>) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border bg-card/10">
      <table className={twMerge('w-full border-collapse text-left text-xs font-sans', className)} {...props}>
        <thead>
          <tr className="border-b border-border bg-card/85 text-[10px] font-mono text-muted uppercase tracking-wider select-none">
            {columns.map((col, index) => (
              <th key={index} className={twMerge('px-4 py-3 font-semibold', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30 font-mono text-text-secondary">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-muted uppercase font-mono animate-pulse">
                Refreshing critical pipeline telemetry...
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-muted uppercase font-mono">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor(row)}
                onClick={() => onRowClick?.(row)}
                className={twMerge(
                  'hover:bg-border/20 transition-colors',
                  onRowClick ? 'cursor-pointer select-none' : ''
                )}
              >
                {columns.map((col, index) => {
                  const content =
                    typeof col.accessor === 'function'
                      ? col.accessor(row)
                      : (row[col.accessor] as React.ReactNode);

                  return (
                    <td key={index} className={twMerge('px-4 py-3 align-middle', col.className)}>
                      {content}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
