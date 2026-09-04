'use client'

import { useState, useEffect } from 'react'
import { ShieldAlert, AlertCircle, Clock, TrendingDown, ChevronRight, Check, Loader, X } from 'lucide-react'
import { getQueue, formatINR, formatDate } from '@/lib/api'

export default function AtRiskRevenue() {
  const [queue, setQueue] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [reviewModal, setReviewModal] = useState<any>(null)
  const [actionStatus, setActionStatus] = useState<Record<number, 'idle' | 'approving' | 'approved' | 'rejected'>>({})
  const [toast, setToast] = useState('')

  const showToast = (message: string) => {
    setToast(message)
    setTimeout(() => setToast(''), 3000)
  }

  const handleReviewClick = (caseData: any) => {
    setReviewModal(caseData)
  }

  const handleApprove = async (caseId: number) => {
    setActionStatus(prev => ({ ...prev, [caseId]: 'approving' }))
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1200))
    
    setActionStatus(prev => ({ ...prev, [caseId]: 'approved' }))
    setReviewModal(null)
    showToast('✓ Recovery approved and initiated!')
  }

  const handleReject = async (caseId: number) => {
    setActionStatus(prev => ({ ...prev, [caseId]: 'rejected' }))
    setReviewModal(null)
    showToast('✗ Recovery blocked as per policy')
  }

  useEffect(() => {
    async function loadData() {
      try {
        const queueData = await getQueue()
        setQueue(queueData)
      } catch (err) {
        console.error('Error loading queue:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) return <div className="loading">Loading...</div>

  // Demo data for high-value cases
  const demoHighValueCases = [
    { id: 1, payment_id: 'pay_enterprise_001', customer: 'Enterprise Corp', amount: 100000000, reason: 'High-value B2B invoice', priority: 'critical', age_hours: 2 },
    { id: 2, payment_id: 'pay_saas_large', customer: 'CloudSolutions Ltd', amount: 50000000, reason: 'Annual subscription renewal', priority: 'high', age_hours: 6 },
    { id: 3, payment_id: 'pay_checkout_vip', customer: 'Premium Customer', amount: 25000000, reason: 'Cart abandonment - VIP', priority: 'high', age_hours: 1 },
  ]

  const demoCheckoutAbandon = [
    { payment_id: 'pay_cart_001', amount: 7500000, customer: 'Arjun Sharma', abandoned_hours: 3, cart_items: 5, last_page: 'Payment' },
    { payment_id: 'pay_cart_002', amount: 12000000, customer: 'Priya Patel', abandoned_hours: 1, cart_items: 3, last_page: 'Review' },
    { payment_id: 'pay_cart_003', amount: 5000000, customer: 'Rahul Verma', abandoned_hours: 8, cart_items: 2, last_page: 'Payment' },
  ]

  const demoFailedSubs = [
    { subscription_id: 'sub_001', customer: 'TechStartup Pro', amount: 4990000, failure_reason: 'insufficient_funds', plan: 'Enterprise', retry_date: 'Tomorrow 10 AM' },
    { subscription_id: 'sub_002', customer: 'Sneha Reddy', amount: 99900, failure_reason: 'card_expired', plan: 'Premium', retry_date: 'Today 6 PM' },
    { subscription_id: 'sub_003', customer: 'Local Business', amount: 2990000, failure_reason: 'bank_declined', plan: 'Business', retry_date: 'Tomorrow 2 PM' },
  ]

  const totalAtRisk = demoHighValueCases.reduce((sum, c) => sum + c.amount, 0) + 
                      demoCheckoutAbandon.reduce((sum, c) => sum + c.amount, 0) +
                      demoFailedSubs.reduce((sum, c) => sum + c.amount, 0)

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1><ShieldAlert className="inline mr-2" />At-Risk Revenue</h1>
          <p>Cases requiring attention or approval before automated recovery</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="metrics-grid" style={{gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'}}>
        <div className="metric-card">
          <small>Total At Risk</small>
          <strong style={{fontSize: '1.8rem', color: 'var(--error)'}}>{formatINR(totalAtRisk)}</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Across all workflows</span>
        </div>
        <div className="metric-card">
          <small>High-Value Cases</small>
          <strong style={{fontSize: '1.8rem'}}>{demoHighValueCases.length}</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--warning)'}}>Needs approval</span>
        </div>
        <div className="metric-card">
          <small>Checkout Abandonment</small>
          <strong style={{fontSize: '1.8rem'}}>{demoCheckoutAbandon.length}</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--info)'}}>Active recovery</span>
        </div>
        <div className="metric-card">
          <small>Failed Subscriptions</small>
          <strong style={{fontSize: '1.8rem'}}>{demoFailedSubs.length}</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--warning)'}}>Retry scheduled</span>
        </div>
      </div>

      {/* High-Value Cases */}
      <section className="panel">
        <h3 style={{marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
          <AlertCircle size={20} color="var(--error)" />
          High-Value Cases (Needs Approval)
        </h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Reason</th>
                <th>Priority</th>
                <th>Age</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {demoHighValueCases.map(c => (
                <tr key={c.id}>
                  <td><code>{c.payment_id}</code></td>
                  <td><strong>{c.customer}</strong></td>
                  <td><strong style={{color: 'var(--error)'}}>{formatINR(c.amount)}</strong></td>
                  <td>{c.reason}</td>
                  <td><span className={`risk-badge ${c.priority === 'critical' ? 'high' : c.priority}`}>{c.priority}</span></td>
                  <td><Clock size={14} className="inline" /> {c.age_hours}h ago</td>
                  <td>
                    <button 
                      className="primary-button" 
                      style={{
                        padding: '0.3rem 0.8rem', 
                        fontSize: '0.85rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem'
                      }}
                      onClick={() => handleReviewClick(c)}
                      disabled={actionStatus[c.id] === 'approved' || actionStatus[c.id] === 'rejected'}
                    >
                      {actionStatus[c.id] === 'approved' && <Check size={14} />}
                      {actionStatus[c.id] === 'rejected' && <X size={14} />}
                      {actionStatus[c.id] === 'approved' ? 'Approved' : 
                       actionStatus[c.id] === 'rejected' ? 'Blocked' : 'Review'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Checkout Abandonment */}
      <section className="panel">
        <h3 style={{marginBottom: '1rem'}}>Checkout Abandonment Recovery</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Customer</th>
                <th>Cart Value</th>
                <th>Items</th>
                <th>Last Page</th>
                <th>Abandoned</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {demoCheckoutAbandon.map(c => (
                <tr key={c.payment_id}>
                  <td><code>{c.payment_id}</code></td>
                  <td>{c.customer}</td>
                  <td><strong>{formatINR(c.amount)}</strong></td>
                  <td>{c.cart_items} items</td>
                  <td>{c.last_page}</td>
                  <td>{c.abandoned_hours}h ago</td>
                  <td><span className="status-badge checkout_recovery">Recovery sent</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Failed Subscriptions */}
      <section className="panel">
        <h3 style={{marginBottom: '1rem'}}>Failed Subscription Renewals</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Subscription ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Plan</th>
                <th>Failure Reason</th>
                <th>Next Retry</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {demoFailedSubs.map(s => (
                <tr key={s.subscription_id}>
                  <td><code>{s.subscription_id}</code></td>
                  <td>{s.customer}</td>
                  <td><strong>{formatINR(s.amount)}</strong></td>
                  <td><span className="status-badge">{s.plan}</span></td>
                  <td>{s.failure_reason.replace(/_/g, ' ')}</td>
                  <td>{s.retry_date}</td>
                  <td><span className="status-badge subscription_renewal">Retry scheduled</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Review Modal */}
      {reviewModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'var(--background)',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '600px',
            width: '90%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1.5rem'}}>
              <div>
                <h2 style={{margin: 0, marginBottom: '0.5rem'}}>Review High-Value Case</h2>
                <p style={{color: 'var(--text-secondary)', margin: 0}}>Approve or block recovery attempt</p>
              </div>
              <button 
                onClick={() => setReviewModal(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '0.5rem'
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{
              background: 'var(--surface)',
              padding: '1.5rem',
              borderRadius: '8px',
              marginBottom: '1.5rem'
            }}>
              <div style={{display: 'grid', gap: '1rem'}}>
                <div>
                  <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Payment ID</div>
                  <code>{reviewModal.payment_id}</code>
                </div>
                <div>
                  <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Customer</div>
                  <strong>{reviewModal.customer}</strong>
                </div>
                <div>
                  <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Amount</div>
                  <strong style={{fontSize: '1.5rem', color: 'var(--error)'}}>{formatINR(reviewModal.amount)}</strong>
                </div>
                <div>
                  <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Reason</div>
                  <div>{reviewModal.reason}</div>
                </div>
                <div>
                  <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>Priority</div>
                  <span className={`risk-badge ${reviewModal.priority === 'critical' ? 'high' : reviewModal.priority}`}>
                    {reviewModal.priority}
                  </span>
                </div>
              </div>
            </div>

            <div style={{
              background: 'var(--info-bg)',
              border: '1px solid var(--info)',
              padding: '1rem',
              borderRadius: '6px',
              marginBottom: '1.5rem',
              fontSize: '0.9rem'
            }}>
              <strong>AI Recommendation:</strong> Approve recovery with priority escalation
            </div>

            <div style={{display: 'flex', gap: '1rem'}}>
              <button
                onClick={() => handleReject(reviewModal.id)}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  background: 'transparent',
                  border: '2px solid var(--error)',
                  color: 'var(--error)',
                  borderRadius: '6px',
                  fontSize: '0.95rem',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Block Recovery
              </button>
              <button
                onClick={() => handleApprove(reviewModal.id)}
                disabled={actionStatus[reviewModal.id] === 'approving'}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  background: 'var(--success)',
                  border: 'none',
                  color: 'white',
                  borderRadius: '6px',
                  fontSize: '0.95rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                {actionStatus[reviewModal.id] === 'approving' && <Loader size={16} className="spin" />}
                {actionStatus[reviewModal.id] === 'approving' ? 'Approving...' : 'Approve Recovery'}
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          background: toast.startsWith('✓') ? 'var(--success)' : 'var(--error)',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000
        }}>
          {toast}
        </div>
      )}

      <style jsx>{`
        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          color: var(--text-secondary);
        }
        .page-content {
          padding: 2rem;
          max-width: 1400px;
          margin: 0 auto;
        }
        .page-header {
          margin-bottom: 2rem;
        }
        .page-header h1 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
          display: flex;
          align-items: center;
        }
        .inline {
          display: inline;
          vertical-align: middle;
          margin-right: 0.25rem;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        :global(.spin) {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  )
}
