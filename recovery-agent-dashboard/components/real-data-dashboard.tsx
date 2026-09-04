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
import PaymentList from './payment-list'

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

  // Seed database with test data
  const handleSeedDatabase = async () => {
    try {
      notify('Seeding database...')
      const { seedDatabase } = await import('@/lib/api')
      const result = await seedDatabase()
      notify(result.message)
      // Reload data after seeding
      window.location.reload()
    } catch (err: any) {
      notify(`Error: ${err.message}`)
    }
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
      <div className="loading-screen">
        <Sparkles className="loading-icon" />
        <p>Loading recovery data from backend...</p>
      </div>
    )
  }

  if (error && !metrics) {
    return (
      <div className="error-screen">
        <AlertCircle className="error-icon" />
        <h2>Failed to Connect to Backend</h2>
        <p>{error}</p>
        <p className="error-hint">Make sure backend is running on http://localhost:8000</p>
        <button className="primary-button" onClick={() => window.location.reload()}>
          <RefreshCw /> Retry
        </button>
      </div>
    )
  }

  const recoveryRate = metrics?.recovery_rate || 0
  const roi = metrics?.roi || 0

  return (
    <div className="page-wrap p-6">
      <div className="page-header">
        <div>
          <div className="demo-label"><span /> Real Data from Backend</div>
          <h1 className="text-3xl font-bold">Revenue Recovery Overview</h1>
          <p className="text-gray-600">Real-time data from FastAPI backend showing actual recovery performance.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {(metrics?.total_attempted === 0 || metrics?.total_attempted === undefined) && (
            <button 
              onClick={handleSeedDatabase}
              style={{
                background: '#10b981',
                color: 'white',
                padding: '10px 16px',
                borderRadius: '6px',
                border: 'none',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Seed Test Data
            </button>
          )}
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

          {/* Payment List - Click to view details */}
          <PaymentList />

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
              </div>
              <div className="saved-callout">
                <Check />
                <small>Recovery Rate</small>
                <strong>{recoveryRate.toFixed(1)}%</strong>
                <span>ROI: {roi.toFixed(1)}x</span>
              </div>
            </div>
          </section>

          {notice && (
            <div className="toast">
              <Check /> {notice}
            </div>
          )}
        </div>
      )
    }
