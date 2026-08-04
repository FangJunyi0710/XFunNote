import React from 'react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  expanded: boolean
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, expanded: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, expanded: false };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    // TODO: 后续可扩展错误上报到后端
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  override render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="error-boundary-fallback">
          <div className="error-boundary-card">
            <h1 className="error-boundary-title">Oops 页面出错了</h1>
            <div className="error-boundary-actions gap-3 flex-wrap justify-center">
              <button className="error-boundary-button" onClick={() => { this.handleReset(); window.history.back() }}>
                后退一页
              </button>
              <button className="error-boundary-button" onClick={() => { this.handleReset(); window.location.href = '/' }}>
                返回首页
              </button>
            </div>
            <div className="mt-5 text-center">
              <button
                onClick={() => this.setState(prev => ({ expanded: !prev.expanded }))}
                className='rounded border px-3 py-0.5 mb-3'
              >
                <pre>{this.state.error && this.state.error.message || '未知错误'}</pre>
              </button>
              {this.state.expanded && this.state.error?.stack && (
                <pre className='text-[10px]'>
                  {this.state.error.stack}
                </pre>
              )}
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
