import type { NotebookType } from '@/config/notebook';
import type { Filter } from '@/types/filter';
import type { OrderBy } from '@/types/notebook';

export interface QueryParam {
  view: string;
  filter: Filter;
  order_by: OrderBy;
  limit: number;
  offset: number;
}

export const DEFAULT_PAGE_LIMIT = 20;

export const defaultQueryParam = (stored?: Partial<QueryParam> | null): QueryParam => ({
  view: stored?.view ?? '',
  filter: stored?.filter ?? [[]],
  order_by: stored?.order_by ?? [['id', 'DESC']],
  limit: stored?.limit ?? DEFAULT_PAGE_LIMIT,
  offset: stored?.offset ?? 0,
});

export const orderByToUrl = (order_by: OrderBy): string =>
  order_by.map(([col, dir]) => `${col} ${dir}`).join(', ');

export const urlToOrderBy = (raw: string): OrderBy | null => {
  if (raw.trim() === '') return [];
  const result: OrderBy = [];
  for (const piece of raw.split(',')) {
    const [col, dir, ...rest] = piece.trim().split(/\s+/);
    const upper = dir?.toUpperCase();
    if (!col || !upper || rest.length > 0 || (upper !== 'ASC' && upper !== 'DESC')) {
      return null;
    }
    result.push([col, upper]);
  }
  return result;
};

export const encodeQueryParam = (qp: QueryParam): Record<string, string> => ({
  view: qp.view,
  order_by: orderByToUrl(qp.order_by),
  filter: JSON.stringify(qp.filter),
  limit: String(qp.limit),
  offset: String(qp.offset),
});

const queryParamKey = (userName: string, notetype: NotebookType) => `xfun-queryparam-${userName}-${notetype}`;

export const readStoredQueryParams = (userName: string, notetype: NotebookType): QueryParam | null => {
  const raw = localStorage.getItem(queryParamKey(userName, notetype));
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const writeStoredQueryParams = (userName: string, notetype: NotebookType, qp: QueryParam) => {
  localStorage.setItem(queryParamKey(userName, notetype), JSON.stringify(qp));
};
