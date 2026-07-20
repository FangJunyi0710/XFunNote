import React from 'react';
import { getTimezoneOffsetStr } from '@/lib/utils';

type TimeUnit = 'year' | 'month' | 'day' | 'hour' | 'minute';

export interface TimestampProps {
  /** 日期字符串或 Date 对象 */
  date: string | Date | null | undefined;
  /** 显示起始单位，默认 'year' */
  from?: TimeUnit;
  /** 显示结束单位，默认 'minute' */
  to?: TimeUnit;
  /** 是否显示时区角标，默认 true */
  showTimezone?: boolean;
  /** 时间文本的额外类名 */
  className?: string;
  /** 角标文本的额外类名 */
  timezoneClassName?: string;
}

const UNIT_ORDER: TimeUnit[] = ['year', 'month', 'day', 'hour', 'minute'];

const UNIT_OPTIONS: Record<TimeUnit, Intl.DateTimeFormatOptions> = {
  year: { year: 'numeric' },
  month: { month: '2-digit' },
  day: { day: '2-digit' },
  hour: { hour: '2-digit' },
  minute: { minute: '2-digit' },
};

export const Timestamp: React.FC<TimestampProps> = ({
  date,
  from = 'year',
  to = 'minute',
  showTimezone = true,
  className = '',
  timezoneClassName = '',
}) => {
  if (!date) return <span className={className}>-</span>;

  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return <span className={className}>无效日期</span>;

  const fromIdx = UNIT_ORDER.indexOf(from);
  const toIdx = UNIT_ORDER.indexOf(to);
  const options: Intl.DateTimeFormatOptions = {};
  for (let i = fromIdx; i <= toIdx; i++) {
    Object.assign(options, UNIT_OPTIONS[UNIT_ORDER[i]]);
  }

  const timeStr = d.toLocaleString('zh-CN', options);
  const tz = getTimezoneOffsetStr();

  return (
    <span className={`relative inline-block ${className}`}>
      {timeStr}
      {showTimezone && (
        <sup className={`absolute top-1.5 -right-0 text-[8px] text-muted-foreground translate-x-full ${timezoneClassName}`}>
          UTC{tz}
        </sup>
      )}
    </span>
  );
};
