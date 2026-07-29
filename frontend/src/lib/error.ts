import { showToast } from '@/components/ui/Toast';

/**
 * 统一错误处理器：弹 toast
 *
 * 用法:
 *   try { ... } catch (e: unknown) {
 *     handleError(e, '删除失败');
 *   }
 */
export const handleError = (e: unknown, context: string): void => 
  showToast(`${context}: ${e instanceof Error ? e.message : String(e)}`, 'error');

export const handleSuccess = (context: string): void => showToast(context, 'success');
