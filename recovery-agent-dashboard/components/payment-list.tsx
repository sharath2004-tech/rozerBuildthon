'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ExternalLink, AlertCircle } from 'lucide-react'
import { formatINR, formatDate } from '@/lib/api'

interface Payment {
  payment_id: string
  customer_id: string
  amount_inr: number
  status: string
  failure_code: string
  risk_score: number
  created_at: string
}

export default function PaymentList() {
  const router = useRouter()
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPayments()
  }, [])

  const loadPayments = async () => {
    setLoading(true)
    try {
      // Mock data for now - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const mockPayments: Payment[] = [
        {
          payment_id: 'pay_6wkgjkr',
          customer_id: 'cust_Qmuy4q',
          amount_inr: 1512800,
          status: 'FAILED',
          failure_code: 'NETWORK_ERROR',
          risk_score: 0.86,
          created_at: new Date().toISOString()
        },
        {
          payment_id: 'pay_7xlhkms',
          customer_id: 'cust_Rnvz5r',
          amount_inr: 879900,
          status: 'FAILED',
          failure_code: 'INSUFFICIENT_FUNDS',
          risk_score: 0.42,
          created_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          payment_id: 'pay_8ymiln',
          customer_id: 'cust_Sowb6s',
          amount_inr: 2345000,
          status: 'FAILED',
          failure_code: 'BANK_TIMEOUT',
          risk_score: 0.67,
          created_at: new Date(Date.now() - 7200000).toISOString()
        }
      ]
      
      setPayments(mockPayments)
    } catch (error) {
      console.error('Failed to load payments:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePaymentClick = (paymentId: string) => {
    // Extract the short ID from payment_id (e.g., "pay_6wkgjkr" -> "6wkgjkr")
    const shortId = paymentId.replace('pay_', '')
    router.push(`/payment/${shortId}`)
  }

  if (loading) {
    return (
      <div className="panel">
        <div className="section-title">
          <div>
            <p className="eyebrow">Recent Activity</p>
            <h2>Failed Payments Requiring Action</h2>
          </div>
        </div>
        <div className="empty-state">
          <p>Loading payments...</p>
        </div>
      </div>
    )
  }

  return (
    <section className="panel table-panel">
      <div className="section-title">
        <div>
          <p className="eyebrow">Recent Activity</p>
          <h2>Failed Payments Requiring Action</h2>
          <p className="section-copy">Click on any payment to view details and run AI agent analysis</p>
        </div>
      </div>
      
      <div className="table-wrap">
        {payments.length === 0 ? (
          <div className="empty-state">
            <AlertCircle />
            <p>No failed payments found</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Failure Code</th>
                <th>Risk Score</th>
                <th>Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {payments.map(payment => (
                <tr 
                  key={payment.payment_id}
                  onClick={() => handlePaymentClick(payment.payment_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td><code>{payment.payment_id}</code></td>
                  <td>
                    <div className="customer">
                      <span className="avatar small">
                        {payment.customer_id.substring(5, 7).toUpperCase()}
                      </span>
                      <strong>{payment.customer_id}</strong>
                    </div>
                  </td>
                  <td><b>{formatINR(payment.amount_inr)}</b></td>
                  <td>
                    <span className="status-badge failed">{payment.status}</span>
                  </td>
                  <td><small style={{ color: '#ef4444' }}>{payment.failure_code}</small></td>
                  <td>
                    <span className={`risk-badge ${
                      payment.risk_score > 0.7 ? 'high' :
                      payment.risk_score > 0.4 ? 'medium' : 'low'
                    }`}>
                      {payment.risk_score.toFixed(2)}
                    </span>
                  </td>
                  <td><small>{formatDate(payment.created_at)}</small></td>
                  <td>
                    <ExternalLink style={{ width: '14px', color: '#64748b' }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
