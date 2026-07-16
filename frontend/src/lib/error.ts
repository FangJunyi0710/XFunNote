import { showToast } from '@/components/ui/Toast';

/**
 * 统一错误处理器：弹 toast + 返回格式化后的错误消息字符串
 *
 * 用法:
 *   try { ... } catch (e: unknown) {
 *     handleError(e, '删除失败');
 *   }
 *
 * @returns 格式化后的错误消息
 */
export function handleError(e: unknown, context: string): string {
  const message = e instanceof Error ? e.message : String(e);
  showToast(`${context}: ${message}`, 'error');
  return message;
}

/**
 * 统一成功提示
 *
 * 用法:
 *   handleSuccess('删除成功');
 */
export function handleSuccess(context: string): void {
  showToast(context, 'success');
}
