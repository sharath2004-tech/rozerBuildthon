'use client'

import { TrendingUp, DollarSign, Users, Zap, ArrowUpRight, ArrowDown } from 'lucide-react'
import { formatINR } from '@/lib/api'

export default function Insights() {
  const insights = [
    {
      title: 'Checkout abandonment peaks 8-10 PM',
      description: 'Sending recovery messages at 9 PM shows 45% higher open rates',
      impact: 'High',
      recommendation: 'Schedule bulk recovery campaigns for 9 PM daily',
      type: 'timing',
      potential_revenue: 250000000
    },
    {
      title: 'Card expiry notifications improve renewal',
      description: '3-day advance notice reduces subscription failures by 35%',
      impact: 'High',
      recommendation: 'Auto-send expiry reminders 3 days before billing',
      type: 'automation',
      potential_revenue: 180000000
    },
    {
      title: 'Salary day retries show 2.5x success',
      description: 'Mandate retries on 1st & 5th of month have highest success',
      impact: 'Medium',
      recommendation: 'Schedule all mandate retries for salary days',
      type: 'timing',
      potential_revenue: 120000000
    },
    {
      title: 'B2B escalation reduces recovery time',
      description: 'Direct escalation after 30 days cuts collection time by 40%',
      impact: 'Medium',
      recommendation: 'Escalate B2B invoices at 30 days, not 45',
      type: 'process',
      potential_revenue: 350000000
    },
    {
      title: 'Hinglish messages perform better',
      description: 'Bilingual messages show 28% higher response rate',
      impact: 'Medium',
      recommendation: 'Enable Hinglish for tier-2/3 city customers',
      type: 'communication',
      potential_revenue: 90000000
    },
    {
      title: 'Promise-to-pay tracking increases recovery',
      description: 'Customers who commit to dates have 65% follow-through',
      impact: 'High',
      recommendation: 'Implement promise-to-pay workflow with reminders',
      type: 'workflow',
      potential_revenue: 200000000
    }
  ]

  const workflowPerformance = [
    { name: 'Checkout Recovery', success: 68, avg_time: '2.5 hours', volume: 245, trend: 'up' },
    { name: 'Subscription Retry', success: 72, avg_time: '1.5 days', volume: 128, trend: 'up' },
    { name: 'Receivables Chase', success: 45, avg_time: '18 days', volume: 67, trend: 'stable' },
    { name: 'Mandate Retry', success: 85, avg_time: '3 days', volume: 89, trend: 'up' },
  ]

  const getImpactColor = (impact: string) => {
    switch(impact) {
      case 'High': return 'var(--error)'
      case 'Medium': return 'var(--warning)'
      case 'Low': return 'var(--info)'
      default: return 'var(--text-secondary)'
    }
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1><TrendingUp className="inline mr-2" />AI-Powered Insights</h1>
          <p>Actionable recommendations from recovery data analysis</p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid" style={{gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'}}>
        <div className="metric-card">
          <small>Total Potential Revenue</small>
          <strong style={{fontSize: '1.8rem', color: 'var(--success)'}}>
            {formatINR(insights.reduce((sum, i) => sum + i.potential_revenue, 0))}
          </strong>
          <span style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>From implementing insights</span>
        </div>
        <div className="metric-card">
          <small>Actionable Insights</small>
          <strong style={{fontSize: '1.8rem'}}>{insights.length}</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--success)'}}>Ready to implement</span>
        </div>
        <div className="metric-card">
          <small>Avg Recovery Time</small>
          <strong style={{fontSize: '1.8rem'}}>6.4 days</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--success)'}}>↓ 2.1 days this month</span>
        </div>
        <div className="metric-card">
          <small>Overall Success Rate</small>
          <strong style={{fontSize: '1.8rem'}}>67.5%</strong>
          <span style={{fontSize: '0.85rem', color: 'var(--success)'}}>↑ 8.2% this month</span>
        </div>
      </div>

      {/* AI Insights */}
      <section className="panel">
        <h3 style={{marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
          <Zap size={20} color="var(--warning)" />
          AI-Generated Insights
        </h3>
        <div style={{display: 'grid', gap: '1rem'}}>
          {insights.map((insight, idx) => (
            <div key={idx} style={{
              padding: '1.5rem',
              background: 'var(--surface)',
              borderRadius: '8px',
              borderLeft: `4px solid ${getImpactColor(insight.impact)}`
            }}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem'}}>
                <h4 style={{margin: 0}}>{insight.title}</h4>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  background: getImpactColor(insight.impact) + '20',
                  color: getImpactColor(insight.impact)
                }}>
                  {insight.impact} Impact
                </span>
              </div>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1rem'}}>{insight.description}</p>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div>
                  <strong style={{color: 'var(--success)'}}>↑ {formatINR(insight.potential_revenue)}</strong>
                  <span style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginLeft: '0.5rem'}}>
                    potential revenue
                  </span>
                </div>
                <button className="primary-button" style={{padding: '0.5rem 1rem', fontSize: '0.85rem'}}>
                  {insight.recommendation}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow Performance */}
      <section className="panel">
        <h3 style={{marginBottom: '1.5rem'}}>Workflow Performance Comparison</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Workflow</th>
                <th>Success Rate</th>
                <th>Avg Recovery Time</th>
                <th>Volume (7d)</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {workflowPerformance.map((wf, idx) => (
                <tr key={idx}>
                  <td><strong>{wf.name}</strong></td>
                  <td>
                    <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                      <strong style={{fontSize: '1.1rem'}}>{wf.success}%</strong>
                      <div style={{flex: 1, height: '6px', background: 'var(--surface)', borderRadius: '3px'}}>
                        <div style={{
                          width: `${wf.success}%`,
                          height: '100%',
                          background: wf.success > 70 ? 'var(--success)' : wf.success > 50 ? 'var(--warning)' : 'var(--error)',
                          borderRadius: '3px'
                        }} />
                      </div>
                    </div>
                  </td>
                  <td>{wf.avg_time}</td>
                  <td>{wf.volume} cases</td>
                  <td>
                    {wf.trend === 'up' ? (
                      <span style={{color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem'}}>
                        <ArrowUpRight size={16} /> Improving
                      </span>
                    ) : wf.trend === 'down' ? (
                      <span style={{color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.25rem'}}>
                        <ArrowDown size={16} /> Declining
                      </span>
                    ) : (
                      <span style={{color: 'var(--text-secondary)'}}>→ Stable</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Stats */}
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem'}}>
        <div className="panel" style={{padding: '1.5rem'}}>
          <h4 style={{marginBottom: '1rem'}}>Best Performing Channel</h4>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>WhatsApp</div>
          <div style={{color: 'var(--text-secondary)'}}>78% open rate, 45% click-through</div>
        </div>
        <div className="panel" style={{padding: '1.5rem'}}>
          <h4 style={{marginBottom: '1rem'}}>Optimal Recovery Window</h4>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>24-48 hours</div>
          <div style={{color: 'var(--text-secondary)'}}>After initial failure</div>
        </div>
        <div className="panel" style={{padding: '1.5rem'}}>
          <h4 style={{marginBottom: '1rem'}}>Cost per Recovery</h4>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem'}}>₹8.50</div>
          <div style={{color: 'var(--success)'}}>↓ 15% vs last month</div>
        </div>
      </div>

      <style jsx>{`
        .page-content {
          padding: 2rem;
          max-width: 1400px;
          margin: 0 auto;
        }
        .inline {
          display: inline;
          vertical-align: middle;
        }
      `}</style>
    </div>
  )
}
