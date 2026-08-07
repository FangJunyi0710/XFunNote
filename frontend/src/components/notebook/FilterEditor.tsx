import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FILTER_OPS_LABEL, isCondition, isNegation, toFilter, toState, type Condition, type Filter, type FilterOp, type FilterState } from '@/types/filter';
import { ArrowIcon, CloseIcon, DeleteIcon, PlusIcon } from '@/components/ui/icons';
import type { ColumnDef } from '@/types/notebook';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { ValueEditor } from '@/components/notebook/ValueEditor';
import { getFieldLabel } from '@/config/notebook';
import { Select } from '@/components/ui/select';

interface FilterEditorProps {
  columns: ColumnDef[];
  value: Filter;
  onChange: (state: Filter | null) => void;
}

const FlatFilterEditor: React.FC<FilterEditorProps> = ({columns, value, onChange}) => {
  const state = toState(value);
  const [filter, setFilter] = useState<Filter[][]>(() => state.filter);
  const [negate, setNegate] = useState<boolean>(() => state.negate ?? false);

  useEffect(() => { onChange(filter.length ? toFilter({filter, negate}) : null) }, [filter, negate]);

  type Leaf = Condition | [Condition, boolean];
  const isLeaf = (flt: Filter): flt is Leaf => isCondition(flt) || isNegation(flt) && isCondition(flt[0]);
  const getCond = (leaf: Leaf): Condition => isNegation(leaf) ? leaf[0] : leaf;
  const isSimpleDNF = (flt: Filter[][]): flt is Leaf[][] => flt.every(g => g.every(r => isLeaf(r)));
  const isPureOr = (flt: Leaf[][]): flt is [Leaf][] => flt.every(g => g.length === 1);
  const isPureAnd = (flt: Leaf[][]): flt is [Leaf[]] => flt.length === 1;
  const isSameCond = (a: Condition, b: Condition): boolean => a.column === b.column && a.op === b.op;
  const isSameCondDNF = (flt: Leaf[][]): boolean =>
    !flt[0]?.[0] || flt.every(g => g.every(r => isLeaf(r) && isSameCond(getCond(flt[0]?.[0]!), getCond(r))))

  if (!isSimpleDNF(filter)) {
    return JSON.stringify(toFilter(state));
  }

  // const setCond = (orIndex: number, andIndex: number, patch: Partial<Condition>): void => setFilter()

  if (isPureOr(filter) || isPureAnd(filter)) {
    if (isSameCondDNF(filter)) {

    }
    return;
  }

  if (isCondition(filter)) {
    const colDef = columns.find(c => c.name === filter.column)!;
    // ── 查找表：运算符 → 值区域渲染函数 ──
    const opRenderers: Partial<Record<FilterOp, () => React.ReactNode>> = {
      'BETWEEN': () => {
        const arr = Array.isArray(filter.value) ? filter.value : [null, null];
        const min = arr[0] ?? null;
        const max = arr[1] ?? null;
        return (
          <div className="flex items-center gap-1 flex-1">
            <ValueEditor col={colDef} value={min} onChange={e => {
                const newArr = [e, max];
                setFilter(prev => ({...prev, value: newArr}));
              }} placeholder="最小值"
            />
            <span className="text-muted-foreground"> - </span>
            <ValueEditor col={colDef} value={max} onChange={e => {
                const newArr = [min, e];
                setFilter(prev => ({...prev, value: newArr}));
              }} placeholder="最大值"
            />
          </div>
        );
      },
      '=': () => {
        const items = Array.isArray(filter.value) ? filter.value : [null];
        return (
          <div className="flex-1 space-y-1">
            {items.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <ValueEditor col={colDef} value={item}
                  onChange={e => {
                    const newItems = [...items];
                    newItems[idx] = e;
                    setFilter(prev => ({...prev, value: newItems}));
                  }}
                  placeholder={`第 ${idx + 1} 项`}
                />
                {!(idx === items.length - 1 && item) && <Button variant="outline" size="sm" onClick={() => 'removeInItem(groupId, row.id, idx)'} className="text-destructive">
                  <DeleteIcon/>
                </Button>}
                {idx === items.length - 1 && <Button variant="outline" size="sm" onClick={() => 'addInItem(groupId, row.id)'}>
                  <PlusIcon/>
                </Button>}
              </div>
            ))}
          </div>
        );
      },
    };
    // 根据运算符获取渲染函数
    const renderValueArea = opRenderers[filter.op] ?? ((): React.ReactNode => <ValueEditor col={colDef} value={filter.value} onChange={value => 'setFilter(prev => ({...prev, value}))'} placeholder={`${getFieldLabel(filter.column)} ${FILTER_OPS_LABEL[filter.op]} 的值`} />);
    const renderTopRow = () => {
      return (
        <div className="flex items-center gap-2">
          <Switch checked={negate} onCheckedChange={() => setNegate(prev => !prev)} />
          <Select value={filter.column} onChange={e => setFilter(prev => ({ ...prev, column: e.target.value, value: null }))}>
            {columns.map(col => <option key={col.name} value={col.name}>{getFieldLabel(col.name)}</option>)}
          </Select>
          <Select value={filter.op} onChange={e => setFilter(prev => ({ ...prev, op: e.target.value as FilterOp }))}>
            {Object.entries(FILTER_OPS_LABEL).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
          <Button variant="outline" size="sm" onClick={() => onChange(null)} className="text-destructive"><DeleteIcon/></Button>
        </div>
      );
    };
    return <>
      {renderTopRow()}
      {renderValueArea()}
    </>
  }

  return JSON.stringify(toFilter(state));
};

const DNFFilterEditor: React.FC<FilterEditorProps> = ({columns, value, onChange}) => {
  const defaultCond: Condition = {column: columns[0]?.name ?? '', op: 'GLOB' as FilterOp, value: null};
  const state = toState(value);
  const [groups, setGroups] = useState<Filter[][]>(() => state.filter);
  const [negate, setNegate] = useState<boolean>(() => state.negate ?? false)

  useEffect(() => { onChange(toFilter({filter: groups, negate})); }, [groups, negate]);

  const addGroup = () => setGroups(prev => [...prev, [defaultCond]]);
  const removeGroup = (orIndex: number) => setGroups(prev => prev.filter((_, idx) => idx !== orIndex));
  const addRow = (orIndex: number) => setGroups(prev => prev.map((g, idx) => idx === orIndex ? [ ...g, defaultCond ] : g));
  const updateRow = (orIndex: number, andIndex: number, newLeaf: Filter) => setGroups(prev => prev.map((g, gidx) => gidx === orIndex ? g.map((r, ridx) => ridx === andIndex ? newLeaf : r) : g));
  const removeRow = (orIndex: number, andIndex: number) => setGroups(prev => prev.map((g, gidx) => gidx === orIndex ? g.filter((_, ridx) => ridx !== andIndex) : g).filter(g => g.length > 0));

  const handleClear = () => {setGroups([]); setNegate(false); };

  return (
    <Card className="ring-1">
      <CardContent className="">
        {/** 编辑器首行 */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">分类讨论</span>
          <div className="flex gap-2 items-center">
            {negate && <p>排除下列情况</p>}
            <Switch checked={negate} onCheckedChange={() => setNegate(prev => !prev)} />
            <Button variant={groups.length ? 'outline' : 'default'} size="sm" onClick={addGroup} title='添加情况'><PlusIcon/></Button>
            <Button variant="ghost" size="sm" onClick={handleClear} title="清除"><CloseIcon /></Button>
          </div>
        </div>
        {/** 渲染条件组 */}
        {groups.map((g, gidx) => <div className="space-y-2">
          {/** 条件组首行 */}
          <div className="flex items-center justify-between">
            <span>情况 {gidx + 1}</span>
            <div className="flex-1 border-t-4 ml-3 mr-2 border-primary/50" />
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" title='添加条件' onClick={() => addRow(gidx)}><PlusIcon/></Button>
              <Button variant="ghost" size="sm" title='删除该情况' onClick={() => removeGroup(gidx)} className="text-destructive"><DeleteIcon/></Button>
            </div>
          </div>
          {/** 条件组各条件 */}
          {g.map((r, ridx) => <FilterEditor columns={columns} value={r}
            onChange={filter => filter ? updateRow(gidx, ridx, filter) : removeRow(gidx, ridx)}
          />)}
        </div>)}
      </CardContent>
    </Card>
  );
};

export const FilterEditor: React.FC<FilterEditorProps> = ({ columns, value, onChange }) => {
  const [isDNFMode, setIsDNFMode] = useState(false);
  if (!columns[0]?.name) return null;

  const Editor = isDNFMode ? DNFFilterEditor : FlatFilterEditor;
  return <div className='relative'>
    <Button variant='ghost' className='absolute top-0 -right-10 z-10' onClick={() => setIsDNFMode(prev => !prev)}>
      <ArrowIcon direction="left" className={cn('transition-transform duration-100 origin-center', isDNFMode && '-rotate-90')}/>
    </Button>
    <Editor columns={columns} value={value} onChange={filter => onChange(filter)} />
  </div>;
};
// TODO 实现完整的 filter 编辑器 含双重取反、均列表、引用等
// TODO 添加新组等时，取之前值作为初始值。
