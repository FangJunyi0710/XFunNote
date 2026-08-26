import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FILTER_OPS_LABEL, type Condition, type Filter, type FilterOp, type Leaf, isLeaf, getCond, getLeafNegate, isSimpleDNF, useFilterState, flattenGroups, setCond, setLeafNegate, isEmpty } from '@/types/filter';
import { ArrowIcon, CloseIcon, DeleteIcon, NegateIcon, PlusIcon, WrapperIcon } from '@/components/ui/icons';
import type { ColumnDef } from '@/types/notebook';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { ValueEditor } from '@/components/notebook/ValueEditor';
import { getFieldLabel } from '@/config/notebook';
import { Select } from '@/components/ui/select';
import { DropdownMenu } from '@/components/ui/dropdown-menu';

interface FilterEditorProps {
  columns: ColumnDef[];
  value: Filter;
  onChange: (filter: Filter | null) => void;
  /** 移动端 ⋮ 菜单追加的操作（由外层下发，如切换/转为分类讨论） */
  extraActions?: { label: string; onSelect: () => void }[];
}

const FlatFilterEditor: React.FC<FilterEditorProps> = ({columns, value, onChange, extraActions}) => {
  const {
    state,
    setNegate,
    addGroup,
    addRow,
    updateRow,
    removeRow,
  } = useFilterState(value, onChange, () => ({col: columns[0]?.name ?? '', op: 'GLOB', val: null}));

  const isSameCond = (a: Condition, b: Condition): boolean => a.col === b.col && a.op === b.op;
  const isSameCondLeaves = (flt: Leaf[]): boolean =>
    !flt[0] || flt.every(leaf => isSameCond(getCond(flt[0]!), getCond(leaf)))

  const renderCond = (updateList: [string, string][], leaf: Leaf, incNegate?: boolean) => {
    const cond = getCond(leaf);
    const updateConds = (patch: Partial<Condition>): void => updateList.forEach(([gid, rid]) => updateRow(gid, rid, setCond(leaf, {...cond, ...patch})));
    const removeConds = (): void => updateList.forEach(([gid, rid]) => removeRow(gid, rid));
    return <span className="flex items-center gap-2">
      {incNegate && state.negate && <span className="sm:hidden">NOT</span>}
      {incNegate && <Switch checked={state.negate} onCheckedChange={() => setNegate(prev => !prev)} className="hidden sm:inline-flex" />}
      <Select value={cond.col} onChange={e => updateConds({ col: e.target.value, val: null })}>
        {columns.map(col => <option key={col.name} value={col.name}>{getFieldLabel(col.name)}</option>)}
      </Select>
      <Select value={cond.op} onChange={e => updateConds({ op: e.target.value as FilterOp })}>
        {Object.entries(FILTER_OPS_LABEL).map(([value, label]) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </Select>
      <Button variant="outline" size="sm" onClick={() => removeConds()} className="text-destructive hidden sm:inline-flex"><DeleteIcon/></Button>
      <DropdownMenu
        className="sm:hidden"
        title="更多操作"
        items={[
          ...(incNegate ? [{ label: '切换取反', icon: <NegateIcon />, onSelect: () => setNegate(prev => !prev) }] : []),
          { label: '删除条件',  danger: true, icon: <DeleteIcon />, onSelect: removeConds },
          ...extraActions ?? [],
        ]}
      />
    </span>
  };
  const renderValue = (gid: string, rid: string, leaf: Leaf, addCond: () => void, isLast?: boolean) => {
    const cond = getCond(leaf);
    const colDef = columns.find(c => c.name === cond.col)!;
    const opRenderers: Partial<Record<FilterOp, () => React.ReactNode>> = {
      'BETWEEN': () => {
        const arr = Array.isArray(cond.val) ? cond.val : [null, null];
        const min = arr[0] ?? null;
        const max = arr[1] ?? null;
        return (
          <span className="flex items-center gap-1 flex-1">
            <ValueEditor col={colDef} value={min} onChange={v => {
                const newArr = [v, max];
                updateRow(gid, rid, setCond(leaf, {...cond, val: newArr}));
              }} placeholder="最小值"
            />
            <span className="text-muted-foreground"> - </span>
            <ValueEditor col={colDef} value={max} onChange={v => {
                const newArr = [min, v];
                updateRow(gid, rid, setCond(leaf, {...cond, val: newArr}));
              }} placeholder="最大值"
            />
          </span>
        );
      }
    };
    // 根据运算符获取渲染函数
    const renderValueArea = opRenderers[cond.op] ?? ((): React.ReactNode => <ValueEditor col={colDef} value={cond.val} onChange={v => updateRow(gid, rid, setCond(leaf, {...cond, val: v}))} placeholder={`${getFieldLabel(cond.col)} ${FILTER_OPS_LABEL[cond.op]} 的值`} />);

    return <span key={rid} className="flex items-center gap-1">
      {getLeafNegate(leaf) && <span className="sm:hidden">NOT</span>}
      <Switch checked={getLeafNegate(leaf)} onCheckedChange={() => updateRow(gid, rid, setLeafNegate(leaf, !getLeafNegate(leaf)))} className="hidden sm:inline-flex" />
      {renderValueArea()}
      {!(isLast && cond.val) && <Button variant="ghost" size="sm" onClick={() => removeRow(gid, rid)} className="text-destructive hidden sm:inline-flex">
        <DeleteIcon/>
      </Button>}
      {isLast && <Button variant="ghost" size="sm" onClick={addCond}>
        <PlusIcon/>
      </Button>}
      <DropdownMenu
        className="sm:hidden"
        title="更多操作"
        items={[
          { label: '切换取反', icon: <NegateIcon />, onSelect: () => updateRow(gid, rid, setLeafNegate(leaf, !getLeafNegate(leaf))) },
          { label: '删除此行', danger: true, icon: <DeleteIcon />, onSelect: () => removeRow(gid, rid) },
        ]}
      />
    </span>;
  };

  const fallbackDisplay = <span className='flex'>
    <p>{JSON.stringify(value)}</p>
    <DropdownMenu className="sm:hidden ml-auto" title="更多操作" items={extraActions ?? []} />
  </span>;

  if (!isSimpleDNF(state.groups)) {
    return fallbackDisplay;
  }
  const flatLeaves = flattenGroups(state.groups);

  if (flatLeaves.length === 0) {
    return fallbackDisplay;
  }

  const type: 'AND' | 'OR' | undefined = 
    state.groups.every(g => g.rows.length === 1) ? 'OR' :
    state.groups.length === 1 ? 'AND' :
  undefined;

  if (type && isSameCondLeaves(flatLeaves.map(([_1, _2, leaf]) => leaf))) {
    const [first_gid, _, leaf] = flatLeaves[0]!;
    const updateList: [string, string][] = flatLeaves.map(([gid, rid, _]) => [gid, rid]);
    const addCond = (cond: Condition) => type === 'OR' ? addGroup(cond) : addRow(first_gid, cond);
    return <>
      {type === 'AND' && <div>(AND)</div>}
      {renderCond(updateList, leaf, true)}
      {flatLeaves.map(([gidx, ridx, leaf], idx) => renderValue(gidx, ridx, leaf, () => addCond({...getCond(leaf), val: null}), idx === flatLeaves.length - 1))}
    </>
  }

  return fallbackDisplay;
};

const DNFFilterEditor: React.FC<FilterEditorProps> = ({columns, value, onChange, extraActions}) => {
  const {
    state,
    setNegate,
    addGroup,
    clearGroups,
    addRow,
    removeGroup,
    updateRow,
    removeRow,
  } = useFilterState(value, onChange, () => ({col: columns[0]?.name ?? '', op: 'GLOB', val: null}));

  return (
    <Card className="ring-1">
      <CardContent className="px-1">
        {/** 编辑器首行 */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">分类讨论</span>
          <div className="flex gap-2 items-center">
            <Switch checked={state.negate} onCheckedChange={() => setNegate(prev => !prev)} />
            <Button variant={state.groups.length ? 'outline' : 'default'} size="sm" onClick={() => addGroup()} title='添加情况'><PlusIcon/></Button>
            <Button variant="ghost" size="sm" className='text-destructive' onClick={clearGroups} title="清除"><CloseIcon /></Button>
            <DropdownMenu className="sm:hidden" title="更多操作" items={extraActions ?? []} />
          </div>
        </div>
        {/** 渲染条件组 */}
        {state.groups.map((g, gidx) => <div className="space-y-2" key={g.id}>
          {/** 条件组首行 */}
          <div className="flex items-center justify-between">
            <span>情况 {gidx + 1}</span>
            <div className={cn("flex-1 border-t-4 ml-3 mr-2", state.negate ? "border-primary/95" : "border-primary/30")} />
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" title='添加条件' onClick={() => addRow(g.id)}><PlusIcon/></Button>
              <Button variant="ghost" size="sm" title='删除该情况' onClick={() => removeGroup(g.id)} className="text-destructive"><DeleteIcon/></Button>
            </div>
          </div>
          {/** 条件组各条件 */}
          {g.rows.map(r => <FilterEditor columns={columns} value={r.filter} key={r.id}
            onChange={filter => filter ? updateRow(g.id, r.id, filter) : removeRow(g.id, r.id)}
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
  const displayWrapping: boolean = !isDNFMode && !isLeaf(value) && !isEmpty(value);
  const actions = [
    { label: isDNFMode ? '收起讨论' : '展开讨论', icon: <ArrowIcon direction={isDNFMode?'left':'down'}/>, onSelect: () => setIsDNFMode(prev => !prev) },
    ...(displayWrapping ? [{ label: '作为情况', icon: <WrapperIcon />, onSelect: () => { onChange([[value]]); setIsDNFMode(true); } }] : []),
  ];
  return <div className='relative'>
    <Button variant='ghost' className='absolute top-0 -right-10 z-10 hidden sm:inline-flex' onClick={() => setIsDNFMode(prev => !prev)}>
      <ArrowIcon direction="left" className={cn('transition-transform duration-100 origin-center', isDNFMode && '-rotate-90')}/>
    </Button>
    {displayWrapping && <Button variant='ghost' className='absolute top-8 -right-10 z-10 hidden sm:inline-flex' onClick={() => {onChange([[value]]); setIsDNFMode(true)}}>
      <WrapperIcon />
    </Button>}
    <Editor columns={columns} value={value} onChange={onChange} extraActions={actions} />
  </div>;
};
// TODO 添加新组等时，取之前值作为初始值。
