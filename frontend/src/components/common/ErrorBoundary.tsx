import { Component, type ReactNode } from 'react';
import { ErrorNotice } from './ErrorNotice';

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed
      ? <ErrorNotice message="Không thể mở màn hình này. Vui lòng tải lại trang." retry={() => window.location.reload()} />
      : this.props.children;
  }
}
