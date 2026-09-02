'use client'

import { useState, useEffect } from 'react'
import {
  Activity, AlertCircle, ArrowDown, ArrowUpRight, Check, ChevronRight,
  CircleDollarSign, Clock3, CreditCard, LayoutDashboard, Menu,
  MoreHorizontal, RefreshCw, Settings, ShieldAlert, Sparkles,
  Target, TrendingUp, Users, X, Zap,
} from 'lucide-react'
import { 
  getRecoveryMetrics, 
  getBatchResults, 
  getComplianceStats,
  getQueue,
  formatCompactINR,
  formatINR,
  formatDate,
  type BatchResult
} from '@/lib/api'

function IconBox({ children, tone = 'navy' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`icon-box ${tone}`}>{children}</span>
}

function Metric({ icon, tone, label, value, copy, trend, up = true }: any) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <IconBox tone={tone}>{icon}</IconBox>
        <span className={up ? 'trend positive' : 'trend negative'}>
          {up ? <ArrowUpRight /> : <ArrowDown />}
          {trend}
        </span>
      </div>
      <p>{label}</p>
      <strong>{value}</strong>
      <small>{copy}</small>
    </article>
  )
}

function SectionTitle({ eyebrow, title, copy, action }: any) {
  return (
    <div className="section-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {copy && <p className="section-copy">{copy}</p>}
      </div>
      {action}
    </div>
  )
}

export default function RealDataDashboard() {
  const [range, setRange] = useState('Last 30 days')
  const [active, setActive] = useState('Overview')
  const [notice, setNotice] = useState('')
  
  // Real data states
  const [metrics, setMetrics] = useState<any>(null)
  const [batches, setBatches] = useState<BatchResult[]>([])
  const [compliance, setCompliance] = useState<any>(null)
  const [queue, setQueue] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const notify = (text: string) => {
    setNotice(text)
    window.setTimeout(() => setNotice(''), 2600)
  }

  // Map range to API period
  const getPeriod = () => {
    if (range === 'Today') return '24h'
    if (range === 'Last 7 days') return '7d'
    if (range === 'Last 30 days') return '30d'
    return 'all'
  }

  // Load data from backend
  useEffect(() => {
    async function loadData() {
      setLoading(true)
      setError('')
      try {
        const period = getPeriod()
        const [metricsData, batchesData, complianceData, queueData] = await Promise.all([
          getRecoveryMetrics(period),
          getBatchResults(period, 50),
          getComplianceStats(period),
          getQueue()
        ])
        
        setMetrics(metricsData)
        setBatches(batchesData.batches)
        setCompliance(complianceData)
        setQueue(queueData)
      } catch (err: any) {
        setError(err.message || 'Failed to load data')
        console.error('Error loading data:', err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [range])

  if (loading && !metrics) {
    return (
      <div className="app-shell">
        <div className="loading-screen">
          <Sparkles className="loading-icon" />
          <p>Loading recovery data from backend...</p>
        </div>
      </div>
    )
  }

  if (error && !metrics) {
    return (
      <div className="app-shell">
        <div className="error-screen">
          <AlertCircle className="error-icon" />
          <h2>Failed to Connect to Backend</h2>
          <p>{error}</p>
          <p className="error-hint">Make sure backend is running on http://localhost:8000</p>
          <button className="primary-button" onClick={() => window.location.reload()}>
            <RefreshCw /> Retry
          </button>
        </div>
      </div>
    )
  }

  const recoveryRate = metrics?.recovery_rate || 0
  const roi = metrics?.roi || 0

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><Zap /></span>
          <span>Recovery<span>Agent</span></span>
        </div>
        <nav aria-label="Main navigation">
          {[
            ['Overview', LayoutDashboard, '/'],
            ['At-Risk Revenue', ShieldAlert, '/at-risk'],
            ['Recovery Actions', RefreshCw, '/recovery-actions'],
            ['Insights', TrendingUp, '/insights']
          ].map(([label, I, path]) => {
            const isActive = (typeof window !== 'undefined' && window.location.pathname === path) || (path === '/' && active === 'Overview')
            return (
              <a
                key={label as string}
                href={path as string}
                className={isActive ? 'nav-item active' : 'nav-item'}
                onClick={(e) => {
                  e.preventDefault()
                  window.location.href = path as string
                }}
              >
                <I />
                <span>{label as string}</span>
                {label === 'At-Risk Revenue' && queue?.count > 0 && <b>{queue.count}</b>}
              </a>
            )
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="agent-mini">
            <span className="status-dot" />
            <div>
              <strong>AI Agent Active</strong>
              <small>Monitoring payments</small>
            </div>
            <MoreHorizontal />
          </div>
          <button className="nav-item"><Settings /><span>Settings</span></button>
          <div className="profile">
            <span className="avatar">AK</span>
            <div>
              <strong>Admin</strong>
              <small>Buildathon Demo</small>
            </div>
            <ChevronRight />
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Open menu"><Menu /></button>
          <div className="mobile-brand">RecoveryAgent</div>
          <div className="topbar-right">
            <span className="live-pill"><span className="status-dot" /> Backend Connected</span>
            <button className="icon-button" aria-label="Notifications"><Activity /></button>
            <span className="avatar small">AK</span>
          </div>
        </header>

        <div className="page-wrap">
          <div className="page-header">
            <div>
              <div className="demo-label"><span /> Real Data from Backend</div>
              <h1>Revenue Recovery Overview</h1>
              <p>Real-time data from FastAPI backend showing actual recovery performance.</p>
            </div>
            <div className="range-control" role="group" aria-label="Date range">
              {['Today', 'Last 7 days', 'Last 30 days'].map(item => (
                <button
                  key={item}
                  className={range === item ? 'selected' : ''}
                  onClick={() => setRange(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {/* Metrics Grid - Real Data */}
          <section className="metrics-grid">
            <Metric
              icon={<CircleDollarSign />}
              tone="blue"
              label="Total Attempted"
              value={formatCompactINR(metrics?.total_attempted || 0)}
              copy="Amount attempted for recovery"
              trend={`${metrics?.active_cases || 0} active`}
            />
            <Metric
              icon={<Check />}
              tone="green"
              label="Total Recovered"
              value={formatCompactINR(metrics?.total_recovered || 0)}
              copy="Actual money recovered"
              trend={`${recoveryRate.toFixed(1)}%`}
            />
            <Metric
              icon={<Target />}
              tone="purple"
              label="Recovery Rate"
              value={`${recoveryRate.toFixed(1)}%`}
              copy="Success rate across all workflows"
              trend={recoveryRate > 50 ? 'Above target' : 'Below target'}
              up={recoveryRate > 50}
            />
            <Metric
              icon={<TrendingUp />}
              tone="amber"
              label="ROI"
              value={`${roi.toFixed(1)}x`}
              copy="Return on investment"
              trend={roi > 5 ? 'Excellent' : 'Good'}
              up={roi > 5}
            />
          </section>

          {/* Batch Results Table - Real Data */}
          <section className="panel table-panel">
            <SectionTitle
              eyebrow="Batch processing"
              title="Recovery Batch Results"
              copy="Measured outcomes by workflow type showing actual money recovered."
            />
            <div className="table-wrap">
              {batches.length === 0 ? (
                <div className="empty-state">
                  <AlertCircle />
                  <p>No batch results yet</p>
                  <small>Run a batch recovery to see results here</small>
                </div>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Batch ID</th>
                      <th>Workflow</th>
                      <th>Cases</th>
                      <th>Attempted</th>
                      <th>Recovered</th>
                      <th>Rate</th>
                      <th>ROI</th>
                      <th>Completed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map(batch => (
                      <tr key={batch.batch_id}>
                        <td><code>{batch.batch_id.slice(0, 12)}...</code></td>
                        <td>
                          <span className={`status-badge ${batch.workflow_type}`}>
                            {batch.workflow_type.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td><b>{batch.total_cases}</b></td>
                        <td>{formatINR(batch.amount_attempted)}</td>
                        <td><b className="text-green">{formatINR(batch.amount_recovered)}</b></td>
                        <td>
                          <span className={`risk-badge ${
                            batch.recovery_rate > 60 ? 'low' :
                            batch.recovery_rate > 30 ? 'medium' : 'high'
                          }`}>
                            {batch.recovery_rate.toFixed(1)}%
                          </span>
                        </td>
                        <td>{batch.roi.toFixed(1)}x</td>
                        <td><small>{formatDate(batch.completed_at)}</small></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>

          {/* Compliance Stats - Real Data */}
          {compliance && (
            <section className="panel">
              <SectionTitle
                eyebrow="Compliance"
                title="Stopping Rules Effectiveness"
                copy="Cases blocked by compliance rules before execution."
              />
              <div className="compliance-grid">
                <div className="compliance-stat">
                  <small>Total Checked</small>
                  <strong>{compliance.total_checked}</strong>
                </div>
                <div className="compliance-stat">
                  <small>Blocked</small>
                  <strong className="text-red">{compliance.blocked_count}</strong>
                </div>
                <div className="compliance-stat">
                  <small>Block Rate</small>
                  <strong>
                    {compliance.total_checked > 0
                      ? ((compliance.blocked_count / compliance.total_checked) * 100).toFixed(1)
                      : 0}%
                  </strong>
                </div>
              </div>

              {Object.keys(compliance.block_reasons || {}).length > 0 && (
                <div className="block-reasons">
                  <h4>Block Reasons</h4>
                  {Object.entries(compliance.block_reasons).map(([reason, count]) => (
                    <div key={reason} className="bar-item">
                      <div>
                        <span>{reason.replace(/_/g, ' ')}</span>
                        <b>{count as number}</b>
                      </div>
                      <div className="bar-track">
                        <i style={{ width: `${((count as number) / compliance.blocked_count) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Summary */}
          <section className="panel impact-panel">
            <SectionTitle
              eyebrow="Buildathon priority feature"
              title="Measured Money Recovery"
              copy="Showing ACTUAL money recovered, not just attempts. This is the key metric."
            />
            <div className="impact-content">
              <div className="impact-bars">
                <div className="impact-row">
                  <span>Amount Attempted</span>
                  <div>
                    <i className="risk-fill" style={{ width: '100%' }} />
                    <b>{formatINR(metrics?.total_attempted || 0)}</b>
                  </div>
                </div>
                <div className="impact-row">
                  <span>Amount Recovered</span>
                  <div>
                    <i className="recovered-fill" style={{ width: `${recoveryRate}%` }} />
                    <b>{formatINR(metrics?.total_recovered || 0)}</b>
                  </div>
                </div>
              </div>
              <div className="saved-callout">
                <Check />
                <small>Recovery Rate</small>
                <strong>{recoveryRate.toFixed(1)}%</strong>
                <span>ROI: {roi.toFixed(1)}x</span>
              </div>
            </div>
          </section>
        </div>
      </main>

      {notice && (
        <div className="toast">
          <Check /> {notice}
        </div>
      )}

      <style jsx>{`
        .loading-screen, .error-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          padding: 2rem;
          text-align: center;
        }
        .loading-icon, .error-icon {
          width: 48px;
          height: 48px;
          margin-bottom: 1rem;
          color: var(--primary);
        }
        .loading-icon {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .error-hint {
          color: var(--text-secondary);
          margin-top: 0.5rem;
        }
        .empty-state {
          padding: 4rem 2rem;
          text-align: center;
          color: var(--text-secondary);
        }
        .empty-state svg {
          width: 48px;
          height: 48px;
          margin-bottom: 1rem;
          opacity: 0.5;
        }
        .text-green {
          color: var(--success);
        }
        .text-red {
          color: var(--error);
        }
        .compliance-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .compliance-stat {
          text-align: center;
          padding: 1.5rem;
          background: var(--surface);
          border-radius: 0.5rem;
        }
        .compliance-stat small {
          display: block;
          margin-bottom: 0.5rem;
          color: var(--text-secondary);
        }
        .compliance-stat strong {
          font-size: 2rem;
        }
        .block-reasons {
          margin-top: 2rem;
        }
        .block-reasons h4 {
          margin-bottom: 1rem;
        }
      `}</style>
    </div>
  )
}
