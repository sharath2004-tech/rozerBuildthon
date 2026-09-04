'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Play, Terminal, AlertCircle, Check, X } from 'lucide-react'

interface PaymentData {
  payment_id: string
  order_id: string
  customer_id: string
  amount_inr: number
  status: string
  failure_code: string
  method: string
  risk_score: number
  total_transactions: number
  success_rate: number
  max_recovery_amount: number
  max_risk_score: number
  max_retries: number
  current_retries: number
}

interface AgentLog {
  timestamp: string
  action: string
  reason: string
  policy_result: string
}

export default function PaymentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [payment, setPayment] = useState<PaymentData | null>(null)
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [isRunningAgent, setIsRunningAgent] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (params?.id) {
      loadPaymentData()
    }
  }, [params?.id])

  const loadPaymentData = async () => {
    setLoading(true)
    try {
      // Simulate API call - replace with actual backend endpoint
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // Mock data matching the screenshot
      setPayment({
        payment_id: `pay_${params?.id || 'unknown'}`,
        order_id: `order_${Math.floor(Math.random() * 1000)}`,
        customer_id: 'cust_Qmuy4q',
        amount_inr: 15128,
        status: 'FAILED',
        failure_code: 'NETWORK_ERROR',
        method: 'NETBANKING',
        risk_score: 0.86,
        total_transactions: 8,
        success_rate: 13,
        max_recovery_amount: 10000,
        max_risk_score: 0.80,
        max_retries: 2,
        current_retries: 2
      })
    } catch (error) {
      console.error('Failed to load payment:', error)
    } finally {
      setLoading(false)
    }
  }

  const runAIAgent = async () => {
    setIsRunningAgent(true)
    setAgentLogs([])
    
    try {
      // Simulate agent processing
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const newLog: AgentLog = {
        timestamp: new Date().toLocaleTimeString(),
        action: 'ESCALATE',
        reason: 'The payment amount exceeds the maximum recovery amount of 1,000,000 INR, making it impossible to retry the payment. Additionally, the retry count has already reached the maximum of 2 retries. Therefore, escalation is necessary as no safe recovery actions are available.',
        policy_result: 'ALLOWED'
      }
      
      setAgentLogs([newLog])
    } catch (error) {
      console.error('Agent execution failed:', error)
    } finally {
      setIsRunningAgent(false)
    }
  }

  if (loading) {
    return (
      <div className="payment-detail-page loading">
        <div className="loading-spinner">Loading payment details...</div>
      </div>
    )
  }

  if (!payment) {
    return (
      <div className="payment-detail-page error">
        <AlertCircle />
        <p>Payment not found</p>
      </div>
    )
  }

  return (
    <div className="payment-detail-page">
      <div className="payment-header">
        <button className="back-button" onClick={() => router.push('/')}>
          <ArrowLeft /> Back to Dashboard
        </button>
        
        <div className="payment-title-section">
          <h1>Payment Context</h1>
          <p className="payment-subtitle">
            ID: {payment.payment_id} / Order: {payment.order_id}
          </p>
        </div>
        
        <button 
          className="run-agent-button"
          onClick={runAIAgent}
          disabled={isRunningAgent}
        >
          <Play className={isRunningAgent ? 'spinning' : ''} />
          {isRunningAgent ? 'Running...' : 'Run AI Agent'}
        </button>
      </div>

      <div className="payment-content">
        <div className="payment-grid">
          {/* Payment Core */}
          <div className="payment-card">
            <h2 className="card-title">Payment Core</h2>
            <div className="card-content">
              <div className="info-row">
                <span className="info-label">Status</span>
                <span className="status-value failed">{payment.status}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Amount</span>
                <span className="info-value">₹{payment.amount_inr.toLocaleString('en-IN')}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Reason</span>
                <span className="failure-code">{payment.failure_code}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Method</span>
                <span className="info-value">{payment.method}</span>
              </div>
            </div>
          </div>

          {/* Risk Profile */}
          <div className="payment-card">
            <h2 className="card-title">Risk Profile</h2>
            <div className="card-content">
              <div className="info-row">
                <span className="info-label">Customer ID</span>
                <span className="info-value">{payment.customer_id}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Risk Score</span>
                <span className="risk-score">{payment.risk_score.toFixed(2)}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Total Transactions</span>
                <span className="info-value">{payment.total_transactions}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Historical Success Rate</span>
                <span className="info-value">{payment.success_rate}%</span>
              </div>
            </div>
          </div>

          {/* Policy Engine Limits */}
          <div className="payment-card">
            <h2 className="card-title">Policy Engine Limits</h2>
            <div className="card-content">
              <div className="info-row">
                <span className="info-label">Max Recovery Amount</span>
                <span className="info-value">₹{payment.max_recovery_amount.toLocaleString('en-IN')}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Max Risk Score</span>
                <span className="info-value">{payment.max_risk_score.toFixed(2)}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Max Retries</span>
                <span className="info-value">{payment.max_retries}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Current Payment Retries</span>
                <span className="info-value">{payment.current_retries}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Terminal */}
        {agentLogs.length > 0 && (
          <div className="agent-terminal">
            <div className="terminal-header">
              <div className="terminal-buttons">
                <span className="terminal-button red"></span>
                <span className="terminal-button yellow"></span>
                <span className="terminal-button green"></span>
              </div>
              <span className="terminal-title">agent-terminal — zsh</span>
            </div>
            
            <div className="terminal-content">
              {agentLogs.map((log, index) => (
                <div key={index} className="terminal-log">
                  <div className="log-timestamp">[{log.timestamp}]</div>
                  <div className="log-action">
                    <span className="log-label">agent.action:</span>
                    <span className="log-value action">{log.action}</span>
                  </div>
                  <div className="log-reason">
                    <span className="log-label">agent.reason:</span>
                    <div className="log-value reason">{log.reason}</div>
                  </div>
                  <div className="log-policy">
                    <span className="log-label">policy.result:</span>
                    <span className="log-value policy-allowed">{log.policy_result}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
