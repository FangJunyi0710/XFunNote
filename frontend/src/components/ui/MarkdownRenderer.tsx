import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

export interface MarkdownRendererProps {
  children: string | null | undefined;
  className?: string;
  /** 是否禁用 GFM 扩展（表格、删除线等） */
  disableGfm?: boolean;
}

/** code 组件的 props 类型（补充 inline 属性） */
interface CodeProps extends React.ClassAttributes<HTMLElement>, React.HTMLAttributes<HTMLElement> {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

/**
 * 统一的 Markdown 渲染组件
 * - 基于 react-markdown + remark-gfm
 * - 支持常见的 Markdown 语法：标题、列表、链接、代码块、表格等
 * - 配合 line-clamp-* 可自动截断
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  children,
  className,
  disableGfm = false,
}) => {
  if (!children) {
    return null;
  }

  const content = String(children);

  return (
    <div
      className={cn(
        'prose prose-sm max-w-none',
        // 自定义样式：在卡片内保持紧凑
        'prose-p:my-1 prose-headings:my-1 prose-ul:my-1 prose-ol:my-1',
        'prose-li:my-0 prose-blockquote:my-1 prose-pre:my-1',
        'prose-a:text-primary prose-a:no-underline hover:prose-a:underline',
        'prose-code:text-sm prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded',
        'prose-pre:bg-muted prose-pre:p-2 prose-pre:rounded-md',
        // 配合 line-clamp 使用时，确保内部元素不溢出
        'overflow-hidden',
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={disableGfm ? [] : [remarkGfm]}
        components={{
          // 链接在新窗口打开
          a: ({ href, children, ...props }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
              {children}
            </a>
          ),
          // 代码块/行内代码渲染
          code: ({ inline, className, children, ...props }: CodeProps) => {
            if (inline) {
              return (
                <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <pre className="bg-muted p-2 rounded-md overflow-x-auto text-sm">
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
