'use client'

import { useState, useEffect } from 'react'
import { ShieldAlert, AlertCircle, Clock, TrendingDown, ChevronRight } from 'lucide-react'
import { getQueue, formatINR, formatDate } from '@/lib/api'

export default function AtRiskRevenue() {
  const [queue, setQueue] = useState<any>(null)
  const [loading, setLoading] = useState(true)

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
                  <td><button className="primary-button" style={{padding: '0.3rem 0.8rem', fontSize: '0.85rem'}}>Review</button></td>
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
      `}</style>
    </div>
  )
}
