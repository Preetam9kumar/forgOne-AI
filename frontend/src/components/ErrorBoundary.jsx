import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Unhandled application error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center px-6">
          <div className="border-2 border-stamp-fail bg-paper px-8 py-6 max-w-lg text-center">
            <p className="font-mono text-[10px] tracking-widest uppercase text-stamp-fail mb-2">
              System Exception Caught
            </p>
            <h1 className="font-semibold text-lg mb-3">Application Error Encountered</h1>
            <p className="text-sm text-ink-soft mb-4 font-mono text-left bg-paper-line/30 p-3 overflow-x-auto text-xs">
              {this.state.error?.toString() || 'An unexpected rendering error occurred.'}
            </p>
            <button
              onClick={this.handleReset}
              className="font-mono text-xs uppercase tracking-wide border-2 border-ink px-4 py-2 hover:bg-ink hover:text-paper transition-colors"
            >
              Reload Application
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
