import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

// 基础图标容器
const Icon: React.FC<IconProps & {
  children: React.ReactNode;
}> = ({ size = 16, className, children }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    {children}
  </svg>
);

/** 单箭头图标 */
interface ArrowIconProps extends IconProps {
  direction: 'left' | 'right' | 'up' | 'down';
}

export const ArrowIcon: React.FC<ArrowIconProps> = ({ direction, ...props }) => {
  const pointsMap = {
    left: '15 18 9 12 15 6',
    right: '9 6 15 12 9 18',
    up: '18 15 12 9 6 15',
    down: '6 9 12 15 18 9',
  };

  return (
    <Icon {...props}>
      <polyline points={pointsMap[direction]} />
    </Icon>
  );
};


/** 双箭头图标 */
export const DoubleArrowIcon: React.FC<ArrowIconProps> = ({ direction, ...props }) => {
  const pointsMap: Record<ArrowIconProps['direction'], string[]> = {
    left: [
      '17 18 11 12 17 6',   // 右箭头（左侧）
      '11 18 5 12 11 6'     // 左箭头（右侧）
    ],
    right: [
      '7 6 13 12 7 18',     // 左箭头（左侧）
      '13 6 19 12 13 18'    // 右箭头（右侧）
    ],
    up: [
      '6 17 12 11 18 17',   // 下箭头（下方）
      '6 11 12 5 18 11'     // 上箭头（上方）
    ],
    down: [
      '18 7 12 13 6 7',     // 上箭头（上方）
      '18 11 12 19 6 11'    // 下箭头（下方）
    ]
  };

  const points = pointsMap[direction];

  return (
    <Icon {...props}>
      {points.map((p, idx) => (
        <polyline key={idx} points={p} />
      ))}
    </Icon>
  );
};

/** 返回/撤销（掉头箭头）图标 */
export const ReplyIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <polyline points="9 17 4 12 9 7" />
    <path d="M20 18v-2a4 4 0 0 0-4-4H4" />
  </Icon>
);

/** 关闭（X）图标 */
export const CloseIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </Icon>
);

/** 加号图标 */
export const PlusIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </Icon>
);

/** 漏斗/筛选图标 */
export const FilterIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <polygon points="22 3 2 3 10 12.46 10 19 14 19 14 12.46 22 3" />
  </Icon>
);

/** 提交（勾选）图标 */
export const SubmitIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <polyline points="20 6 9 17 4 12" />
  </Icon>
);

/** 发送图标 */
export const SendIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </Icon>
);

/** 编辑（铅笔）图标 */
export const EditIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </Icon>
);

/** 批量更新（铅笔在堆叠的文件上）图标 */
export const BatchEditIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    {/* 堆叠的文件 */}
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    {/* 第二个文件（堆叠效果） */}
    <path d="M4 6h-1a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-1" />
    {/* 铅笔 */}
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </Icon>
);

/** 删除（垃圾桶）图标 */
export const DeleteIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </Icon>
);

/** 复制图标 */
export const CopyIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </Icon>
);

/** 全选（堆叠的文件上有对勾）图标 */
export const SelectAllIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    {/* 主文件 */}
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    {/* 堆叠文件 */}
    <path d="M4 6h-1a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-1" />
    {/* 对勾 */}
    <polyline points="9 15 11 17 16 12" />
  </Icon>
);

/** 全不选（堆叠的文件上有叉号）图标 */
export const DeselectAllIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    {/* 主文件 */}
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    {/* 堆叠文件 */}
    <path d="M4 6h-1a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-1" />
    {/* 叉号 */}
    <line x1="10" y1="13" x2="15" y2="18" />
    <line x1="15" y1="13" x2="10" y2="18" />
  </Icon>
);

/** 太阳（亮色模式）图标 */
export const SunIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </Icon>
);

/** 月亮（暗色模式）图标 */
export const MoonIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </Icon>
);

/** 眼睛（显示）图标 */
export const EyeIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
);

/** 眼睛（隐藏）图标 */
export const EyeOffIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
    <line x1="1" y1="1" x2="23" y2="23" />
    <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
  </Icon>
);

/** 包装（中括号）图标 - 单 path 实现 */
export const WrapperIcon: React.FC<IconProps> = ({ ...props }) => (
  <Icon {...props}>
    <path
      d="
        M 4 4 L 8 4
        M 4 4 L 4 20
        M 4 20 L 8 20
        M 20 4 L 16 4
        M 20 4 L 20 20
        M 20 20 L 16 20
      "
    />
  </Icon>
);
