'use client'

import { useState } from 'react'
import { RefreshCw, Send, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { formatINR } from '@/lib/api'

export default function RecoveryActions() {
  const [selectedWorkflow, setSelectedWorkflow] = useState('all')

  const workflows = [
    { id: 'checkout_recovery', name: 'Checkout Recovery', count: 12, icon: '🛒' },
    { id: 'subscription_renewal', name: 'Subscription Retry', count: 8, icon: '🔄' },
    { id: 'receivables_chase', name: 'Receivables Collection', count: 5, icon: '💼' },
    { id: 'mandate_retry', name: 'Mandate Retry', count: 3, icon: '📋' },
  ]

  const recentActions = [
    { id: 1, workflow: 'checkout_recovery', payment_id: 'pay_001', customer: 'Arjun Sharma', action: 'SMS reminder sent', amount: 7500000, status: 'sent', time: '5 mins ago' },
    { id: 2, workflow: 'subscription_renewal', payment_id: 'pay_sub_045', customer: 'TechCorp', action: 'Mandate retry scheduled', amount: 4990000, status: 'scheduled', time: '12 mins ago' },
    { id: 3, workflow: 'receivables_chase', payment_id: 'inv_2024_1050', customer: 'Enterprise Ltd', action: 'Escalation email sent', amount: 100000000, status: 'sent', time: '25 mins ago' },
    { id: 4, workflow: 'checkout_recovery', payment_id: 'pay_002', customer: 'Priya Patel', action: 'WhatsApp recovery link', amount: 12000000, status: 'delivered', time: '35 mins ago' },
    { id: 5, workflow: 'subscription_renewal', payment_id: 'pay_sub_046', customer: 'Sneha Reddy', action: 'Card update reminder', amount: 99900, status: 'sent', time: '1 hour ago' },
    { id: 6, workflow: 'mandate_retry', payment_id: 'pay_mandate_12', customer: 'Local Business', action: 'Retry on salary day', amount: 2990000, status: 'scheduled', time: '2 hours ago' },
    { id: 7, workflow: 'receivables_chase', payment_id: 'inv_2024_1048', customer: 'CloudSolutions', action: 'Gentle reminder', amount: 50000000, status: 'sent', time: '3 hours ago' },
    { id: 8, workflow: 'checkout_recovery', payment_id: 'pay_003', customer: 'Rahul Verma', action: 'Discount offer sent', amount: 5000000, status: 'opened', time: '4 hours ago' },
  ]

  const filtered = selectedWorkflow === 'all' ? recentActions : recentActions.filter(a => a.workflow === selectedWorkflow)

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'sent': case 'delivered': return <Send size={16} color="var(--info)" />
      case 'scheduled': return <Clock size={16} color="var(--warning)" />
      case 'opened': return <CheckCircle size={16} color="var(--success)" />
      case 'failed': return <XCircle size={16} color="var(--error)" />
      default: return <AlertTriangle size={16} />
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1><RefreshCw className="inline mr-2" />Recovery Actions</h1>
          <p>All automated and manual recovery actions across workflows</p>
        </div>
      </div>

      {/* Workflow Cards */}
      <div className="workflows-grid">
        <div 
          className={`workflow-card ${selectedWorkflow === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedWorkflow('all')}
        >
          <span className="workflow-icon">🎯</span>
          <strong>All Workflows</strong>
          <span className="workflow-count">{recentActions.length} actions</span>
        </div>
        {workflows.map(w => (
          <div 
            key={w.id}
            className={`workflow-card ${selectedWorkflow === w.id ? 'active' : ''}`}
            onClick={() => setSelectedWorkflow(w.id)}
          >
            <span className="workflow-icon">{w.icon}</span>
            <strong>{w.name}</strong>
            <span className="workflow-count">{w.count} active</span>
          </div>
        ))}
      </div>

      {/* Actions Table */}
      <section className="panel">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
          <h3>Recent Recovery Actions</h3>
          <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
            Showing {filtered.length} actions
          </span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Workflow</th>
                <th>Payment ID</th>
                <th>Customer</th>
                <th>Action Taken</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(action => (
                <tr key={action.id}>
                  <td>
                    <span className={`status-badge ${action.workflow}`}>
                      {action.workflow.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td><code>{action.payment_id}</code></td>
                  <td>{action.customer}</td>
                  <td><strong>{action.action}</strong></td>
                  <td>{formatINR(action.amount)}</td>
                  <td>
                    <span style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                      {getStatusIcon(action.status)}
                      {action.status}
                    </span>
                  </td>
                  <td style={{color: 'var(--text-secondary)'}}>{action.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Action Effectiveness */}
      <section className="panel">
        <h3 style={{marginBottom: '1.5rem'}}>Action Effectiveness by Workflow</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem'}}>
          <div style={{padding: '1rem', background: 'var(--surface)', borderRadius: '8px'}}>
            <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem'}}>Checkout Recovery</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>68%</div>
            <div style={{fontSize: '0.85rem', color: 'var(--success)'}}>↑ 12% this week</div>
          </div>
          <div style={{padding: '1rem', background: 'var(--surface)', borderRadius: '8px'}}>
            <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem'}}>Subscription Retry</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>72%</div>
            <div style={{fontSize: '0.85rem', color: 'var(--success)'}}>↑ 8% this week</div>
          </div>
          <div style={{padding: '1rem', background: 'var(--surface)', borderRadius: '8px'}}>
            <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem'}}>Receivables Chase</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>45%</div>
            <div style={{fontSize: '0.85rem', color: 'var(--info)'}}>→ Stable</div>
          </div>
          <div style={{padding: '1rem', background: 'var(--surface)', borderRadius: '8px'}}>
            <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem'}}>Mandate Retry</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>85%</div>
            <div style={{fontSize: '0.85rem', color: 'var(--success)'}}>↑ 5% this week</div>
          </div>
        </div>
      </section>

      <style jsx>{`
        .page-content {
          padding: 2rem;
          max-width: 1400px;
          margin: 0 auto;
        }
        .workflows-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .workflow-card {
          padding: 1.5rem;
          background: var(--surface);
          border: 2px solid transparent;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .workflow-card:hover {
          border-color: var(--primary);
          transform: translateY(-2px);
        }
        .workflow-card.active {
          border-color: var(--primary);
          background: var(--primary-bg);
        }
        .workflow-icon {
          font-size: 2rem;
        }
        .workflow-count {
          font-size: 0.85rem;
          color: var(--text-secondary);
        }
        .inline {
          display: inline;
          vertical-align: middle;
        }
      `}</style>
    </div>
  )
}
