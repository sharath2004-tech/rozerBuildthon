'use client'

import { useState } from 'react'
import { 
  Beaker, 
  CreditCard, 
  ShoppingCart, 
  RefreshCw, 
  DollarSign,
  CheckCircle,
  Play,
  RotateCcw,
  TrendingUp,
  AlertTriangle,
  ArrowDown,
  Loader,
  ChevronRight,
  X,
  Check,
  Circle
} from 'lucide-react'
import { formatINR } from '@/lib/api'

interface DemoMetrics {
  transactions_analyzed: number
  revenue_analyzed: number
  revenue_at_risk: number
  potential_recovery: number
  actions_recommended: number
  simulated_recovery: number
  recovery_rate: number
}

interface RecoveryCase {
  payment_id: string
  amount: number
  risk_score: number
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
  failure_reason: string
  customer_type: string
  previous_attempts: number
  recovery_probability: number
  recommended_action: string
  reason: string
  confidence: number
  status: 'simulated' | 'pending' | 'recovered' | 'no_action'
  recovered_amount: number
  pipeline_stage?: string
}

const scenarios = [
  {
    id: 'payment_failure',
    icon: CreditCard,
    title: 'Payment Failure',
    description: 'Simulate failed payments and let the agent determine the appropriate recovery strategy.',
    color: 'blue'
  },
  {
    id: 'checkout_abandonment',
    icon: ShoppingCart,
    title: 'Checkout Abandonment',
    description: 'Simulate customers who started checkout but did not complete payment.',
    color: 'purple'
  },
  {
    id: 'repeated_failure',
    icon: RefreshCw,
    title: 'Repeated Payment Failure',
    description: 'Test whether the agent avoids blindly retrying payments that repeatedly fail.',
    color: 'orange'
  },
  {
    id: 'high_value',
    icon: DollarSign,
    title: 'High Value Revenue Risk',
    description: 'Test how the system prioritizes high-value revenue opportunities.',
    color: 'green'
  },
  {
    id: 'low_priority',
    icon: Circle,
    title: 'Low Priority Case',
    description: 'Demonstrate that the agent does not treat every failed payment as equally important.',
    color: 'gray'
  },
  {
    id: 'already_recovered',
    icon: CheckCircle,
    title: 'Already Recovered',
    description: 'Test whether the system recognizes already recovered revenue.',
    color: 'teal'
  }
]

const pipelineStages = [
  { name: 'Payment Events', icon: '📥' },
  { name: 'Risk Detection', icon: '🔍' },
  { name: 'Risk Analysis', icon: '⚠️' },
  { name: 'Agent Decision', icon: '🧠' },
  { name: 'Intervention Selection', icon: '🎯' },
  { name: 'Recovery Action', icon: '⚡' },
  { name: 'Recovery Outcome', icon: '📈' }
]

export default function DemoMode() {
  const [metrics, setMetrics] = useState<DemoMetrics>({
    transactions_analyzed: 0,
    revenue_analyzed: 0,
    revenue_at_risk: 0,
    potential_recovery: 0,
    actions_recommended: 0,
    simulated_recovery: 0,
    recovery_rate: 0
  })

  const [cases, setCases] = useState<RecoveryCase[]>([])
  const [selectedCase, setSelectedCase] = useState<RecoveryCase | null>(null)
  const [loading, setLoading] = useState(false)
  const [pipelineActive, setPipelineActive] = useState(false)
  const [currentStage, setCurrentStage] = useState(0)
  const [toast, setToast] = useState('')

  // Custom input state
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [customInput, setCustomInput] = useState({
    amount: 25000,
    failure_code: 'INSUFFICIENT_FUNDS',
    retry_count: 1,
    customer_type: 'returning',
    hours_since_failure: 2
  })

  const showToast = (message: string) => {
    setToast(message)
    setTimeout(() => setToast(''), 3000)
  }

  const runScenario = async (scenarioId: string) => {
    setLoading(true)
    setPipelineActive(true)
    setCurrentStage(0)

    try {
      // Animate through pipeline stages
      for (let i = 0; i < pipelineStages.length; i++) {
        setCurrentStage(i)
        await new Promise(resolve => setTimeout(resolve, 600))
      }

      // Generate scenario-specific data
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/demo/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenarioId })
      })

      if (response.ok) {
        const data = await response.json()
        setCases(data.cases)
        setMetrics(data.metrics)
        showToast(`✓ ${data.cases.length} recovery cases simulated`)
      } else {
        // Fallback to local simulation
        const localData = generateLocalScenario(scenarioId)
        setCases(localData.cases)
        setMetrics(localData.metrics)
        showToast(`✓ ${localData.cases.length} recovery cases simulated (local)`)
      }
    } catch (error) {
      // Fallback to local simulation
      const localData = generateLocalScenario(scenarioId)
      setCases(localData.cases)
      setMetrics(localData.metrics)
      showToast(`✓ ${localData.cases.length} recovery cases simulated (local)`)
    } finally {
      setLoading(false)
      setTimeout(() => setPipelineActive(false), 1000)
    }
  }

  const runCustomAnalysis = async () => {
    setLoading(true)
    setPipelineActive(true)
    setCurrentStage(0)

    try {
      // Animate through pipeline stages
      for (let i = 0; i < pipelineStages.length; i++) {
        setCurrentStage(i)
        await new Promise(resolve => setTimeout(resolve, 600))
      }

      // Map customer type to lifetime payments
      const lifetimeMap: Record<string, any> = {
        'new': { lifetime_payments: 0, lifetime_recoveries: 0 },
        'returning': { lifetime_payments: 5, lifetime_recoveries: 4 },
        'premium': { lifetime_payments: 12, lifetime_recoveries: 11 }
      }
      
      const customerData = lifetimeMap[customInput.customer_type] || lifetimeMap.returning

      // Call backend with custom values
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/demo/custom-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_id: `pay_custom_${Date.now()}`,
          customer_id: `cust_custom_${Date.now()}`,
          amount_inr: customInput.amount,
          rail: 'UPI',
          failure_code: customInput.failure_code,
          retry_count: customInput.retry_count,
          hours_since_failure: customInput.hours_since_failure,
          prior_actions_24h: 0,
          ...customerData,
          has_messaging_consent: true,
          is_dnd_registered: false,
          already_recovered: false,
          action_in_flight: false,
          idempotency_key: `custom_${Date.now()}`
        })
      })

      if (response.ok) {
        const data = await response.json()
        setCases([data.case])
        setMetrics(data.metrics)
        setShowCustomForm(false)
        showToast(`✓ Custom analysis complete - ${data.case.recommended_action}`)
      } else {
        showToast('❌ Backend unavailable - try preset scenarios')
      }
    } catch (error) {
      showToast('❌ Error analyzing custom input')
    } finally {
      setLoading(false)
      setTimeout(() => setPipelineActive(false), 1000)
    }
  }

  const runFullSimulation = async () => {
    setLoading(true)
    setPipelineActive(true)
    setCurrentStage(0)

    try {
      // Animate through pipeline stages
      for (let i = 0; i < pipelineStages.length; i++) {
        setCurrentStage(i)
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/demo/full-simulation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      if (response.ok) {
        const data = await response.json()
        setCases(data.cases)
        setMetrics(data.metrics)
        showToast(`✓ Full recovery simulation completed - ${data.cases.length} cases analyzed`)
      } else {
        const fullData = generateFullSimulation()
        setCases(fullData.cases)
        setMetrics(fullData.metrics)
        showToast(`✓ Full simulation completed - ${fullData.cases.length} cases analyzed`)
      }
    } catch (error) {
      const fullData = generateFullSimulation()
      setCases(fullData.cases)
      setMetrics(fullData.metrics)
      showToast(`✓ Full simulation completed - ${fullData.cases.length} cases analyzed`)
    } finally {
      setLoading(false)
      setTimeout(() => setPipelineActive(false), 1000)
    }
  }

  const resetSimulation = () => {
    setMetrics({
      transactions_analyzed: 0,
      revenue_analyzed: 0,
      revenue_at_risk: 0,
      potential_recovery: 0,
      actions_recommended: 0,
      simulated_recovery: 0,
      recovery_rate: 0
    })
    setCases([])
    setSelectedCase(null)
    setPipelineActive(false)
    setCurrentStage(0)
    showToast('✓ Simulation reset')
  }

  const generateLocalScenario = (scenarioId: string) => {
    // Generate scenario-specific test cases
    const scenarios: Record<string, any> = {
      payment_failure: {
        cases: [
          {
            payment_id: 'pay_demo_001',
            amount: 2500000,
            risk_score: 75,
            risk_level: 'HIGH',
            failure_reason: 'Insufficient funds',
            customer_type: 'Returning',
            previous_attempts: 1,
            recovery_probability: 0.68,
            recommended_action: 'Retry Payment',
            reason: 'Recent failure with recoverable reason',
            confidence: 85,
            status: 'recovered',
            recovered_amount: 2500000
          }
        ]
      },
      checkout_abandonment: {
        cases: [
          {
            payment_id: 'pay_demo_002',
            amount: 1200000,
            risk_score: 82,
            risk_level: 'HIGH',
            failure_reason: 'Checkout abandoned',
            customer_type: 'Returning',
            previous_attempts: 0,
            recovery_probability: 0.72,
            recommended_action: 'Send Recovery Reminder',
            reason: 'High-value cart with strong customer history',
            confidence: 88,
            status: 'recovered',
            recovered_amount: 1200000
          }
        ]
      },
      repeated_failure: {
        cases: [
          {
            payment_id: 'pay_demo_003',
            amount: 800000,
            risk_score: 45,
            risk_level: 'MEDIUM',
            failure_reason: 'Card declined (4 times)',
            customer_type: 'Returning',
            previous_attempts: 4,
            recovery_probability: 0.32,
            recommended_action: 'Suggest Alternate Payment Method',
            reason: 'Multiple failures suggest card issue',
            confidence: 76,
            status: 'pending',
            recovered_amount: 0
          }
        ]
      },
      high_value: {
        cases: [
          {
            payment_id: 'pay_demo_004',
            amount: 5000000,
            risk_score: 92,
            risk_level: 'HIGH',
            failure_reason: 'Network error',
            customer_type: 'Premium',
            previous_attempts: 1,
            recovery_probability: 0.89,
            recommended_action: 'Priority Retry',
            reason: 'High-value customer with temporary technical failure',
            confidence: 94,
            status: 'recovered',
            recovered_amount: 5000000
          }
        ]
      },
      low_priority: {
        cases: [
          {
            payment_id: 'pay_demo_005',
            amount: 19900,
            risk_score: 28,
            risk_level: 'LOW',
            failure_reason: 'Payment timeout',
            customer_type: 'New',
            previous_attempts: 1,
            recovery_probability: 0.22,
            recommended_action: 'No Action',
            reason: 'Low-value new customer with minimal success probability',
            confidence: 71,
            status: 'no_action',
            recovered_amount: 0
          }
        ]
      },
      already_recovered: {
        cases: [
          {
            payment_id: 'pay_demo_006',
            amount: 1500000,
            risk_score: 0,
            risk_level: 'LOW',
            failure_reason: 'Already recovered',
            customer_type: 'Returning',
            previous_attempts: 0,
            recovery_probability: 1.0,
            recommended_action: 'No Action',
            reason: 'Revenue already recovered - no intervention needed',
            confidence: 100,
            status: 'recovered',
            recovered_amount: 1500000
          }
        ]
      }
    }

    const scenarioData = scenarios[scenarioId] || scenarios.payment_failure
    const totalRevenue = scenarioData.cases.reduce((sum: number, c: any) => sum + c.amount, 0)
    const recoveredRevenue = scenarioData.cases.reduce((sum: number, c: any) => sum + c.recovered_amount, 0)
    const atRisk = totalRevenue - recoveredRevenue

    return {
      cases: scenarioData.cases,
      metrics: {
        transactions_analyzed: scenarioData.cases.length,
        revenue_analyzed: totalRevenue,
        revenue_at_risk: atRisk,
        potential_recovery: totalRevenue * 0.7,
        actions_recommended: scenarioData.cases.filter((c: any) => c.recommended_action !== 'No Action').length,
        simulated_recovery: recoveredRevenue,
        recovery_rate: totalRevenue > 0 ? (recoveredRevenue / totalRevenue) * 100 : 0
      }
    }
  }

  const generateFullSimulation = () => {
    const fullCases: RecoveryCase[] = [
      {
        payment_id: 'pay_demo_101',
        amount: 2500000,
        risk_score: 87,
        risk_level: 'HIGH',
        failure_reason: 'Failed payment',
        customer_type: 'Returning',
        previous_attempts: 1,
        recovery_probability: 0.82,
        recommended_action: 'Retry Payment',
        reason: 'High-value recent failure with strong customer history',
        confidence: 91,
        status: 'recovered',
        recovered_amount: 2500000
      },
      {
        payment_id: 'pay_demo_102',
        amount: 1200000,
        risk_score: 78,
        risk_level: 'HIGH',
        failure_reason: 'Abandoned checkout',
        customer_type: 'Returning',
        previous_attempts: 0,
        recovery_probability: 0.75,
        recommended_action: 'Send Recovery Reminder',
        reason: 'High-value cart abandonment - strong recovery potential',
        confidence: 85,
        status: 'recovered',
        recovered_amount: 1200000
      },
      {
        payment_id: 'pay_demo_103',
        amount: 800000,
        risk_score: 52,
        risk_level: 'MEDIUM',
        failure_reason: 'Card declined',
        customer_type: 'Returning',
        previous_attempts: 3,
        recovery_probability: 0.45,
        recommended_action: 'Suggest Alternate Method',
        reason: 'Multiple declines suggest payment method issue',
        confidence: 72,
        status: 'pending',
        recovered_amount: 0
      },
      {
        payment_id: 'pay_demo_104',
        amount: 5000000,
        risk_score: 94,
        risk_level: 'HIGH',
        failure_reason: 'Network error',
        customer_type: 'Premium',
        previous_attempts: 1,
        recovery_probability: 0.92,
        recommended_action: 'Priority Retry',
        reason: 'Critical high-value customer - technical failure',
        confidence: 96,
        status: 'recovered',
        recovered_amount: 5000000
      },
      {
        payment_id: 'pay_demo_105',
        amount: 450000,
        risk_score: 48,
        risk_level: 'MEDIUM',
        failure_reason: 'Insufficient funds',
        customer_type: 'New',
        previous_attempts: 2,
        recovery_probability: 0.38,
        recommended_action: 'Delayed Retry',
        reason: 'Wait for potential fund availability',
        confidence: 68,
        status: 'pending',
        recovered_amount: 0
      },
      {
        payment_id: 'pay_demo_106',
        amount: 19900,
        risk_score: 25,
        risk_level: 'LOW',
        failure_reason: 'Timeout',
        customer_type: 'New',
        previous_attempts: 1,
        recovery_probability: 0.18,
        recommended_action: 'No Action',
        reason: 'Low-value with minimal recovery probability',
        confidence: 82,
        status: 'no_action',
        recovered_amount: 0
      },
      {
        payment_id: 'pay_demo_107',
        amount: 1500000,
        risk_score: 0,
        risk_level: 'LOW',
        failure_reason: 'Already recovered',
        customer_type: 'Returning',
        previous_attempts: 0,
        recovery_probability: 1.0,
        recommended_action: 'No Action',
        reason: 'Payment already successful - no intervention needed',
        confidence: 100,
        status: 'recovered',
        recovered_amount: 1500000
      },
      {
        payment_id: 'pay_demo_108',
        amount: 3200000,
        risk_score: 81,
        risk_level: 'HIGH',
        failure_reason: 'Bank decline',
        customer_type: 'Returning',
        previous_attempts: 1,
        recovery_probability: 0.73,
        recommended_action: 'Retry Payment',
        reason: 'Temporary bank issue with high recovery potential',
        confidence: 87,
        status: 'recovered',
        recovered_amount: 3200000
      }
    ]

    const totalRevenue = fullCases.reduce((sum, c) => sum + c.amount, 0)
    const recoveredRevenue = fullCases.reduce((sum, c) => sum + c.recovered_amount, 0)
    const atRisk = fullCases.filter(c => c.status !== 'recovered' && c.status !== 'no_action')
                            .reduce((sum, c) => sum + c.amount, 0)

    return {
      cases: fullCases,
      metrics: {
        transactions_analyzed: fullCases.length,
        revenue_analyzed: totalRevenue,
        revenue_at_risk: atRisk,
        potential_recovery: atRisk * 0.68,
        actions_recommended: fullCases.filter(c => c.recommended_action !== 'No Action').length,
        simulated_recovery: recoveredRevenue,
        recovery_rate: totalRevenue > 0 ? (recoveredRevenue / totalRevenue) * 100 : 0
      }
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Beaker className="h-8 w-8 text-purple-600" />
          <h1 className="text-3xl font-bold text-gray-900">Revenue Recovery Simulator</h1>
          <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
            SAFE SIMULATION
          </span>
        </div>
        <p className="text-gray-600">
          Explore how Rozer detects revenue risk, analyzes payment behavior, chooses recovery strategies and executes bounded recovery workflows.
        </p>
      </div>

      {/* Metrics Dashboard */}
      {cases.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Transactions Analyzed</div>
            <div className="text-2xl font-bold text-gray-900">{metrics.transactions_analyzed}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Revenue Analyzed</div>
            <div className="text-2xl font-bold text-gray-900">{formatINR(metrics.revenue_analyzed)}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Revenue At Risk</div>
            <div className="text-2xl font-bold text-orange-600">{formatINR(metrics.revenue_at_risk)}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Potential Recovery</div>
            <div className="text-2xl font-bold text-blue-600">{formatINR(metrics.potential_recovery)}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Actions Recommended</div>
            <div className="text-2xl font-bold text-gray-900">{metrics.actions_recommended}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Simulated Recovery</div>
            <div className="text-2xl font-bold text-green-600">{formatINR(metrics.simulated_recovery)}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Recovery Rate</div>
            <div className="text-2xl font-bold text-green-600">{metrics.recovery_rate.toFixed(1)}%</div>
          </div>
          <div className="bg-white p-4 rounded-lg border shadow-sm flex items-center justify-center">
            <button
              onClick={resetSimulation}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium"
            >
              <RotateCcw size={18} />
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Pipeline Visualization */}
      {pipelineActive && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Pipeline</h3>
          <div className="flex items-center justify-between">
            {pipelineStages.map((stage, index) => (
              <div key={index} className="flex flex-col items-center">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl mb-2 transition-all ${
                  index <= currentStage 
                    ? 'bg-blue-600 text-white scale-110' 
                    : 'bg-gray-200 text-gray-400'
                }`}>
                  {index < currentStage ? '✓' : stage.icon}
                </div>
                <div className={`text-xs text-center max-w-[80px] ${
                  index <= currentStage ? 'text-gray-900 font-medium' : 'text-gray-500'
                }`}>
                  {stage.name}
                </div>
                {index < pipelineStages.length - 1 && (
                  <ArrowDown className={`absolute mt-16 ${
                    index < currentStage ? 'text-blue-600' : 'text-gray-300'
                  }`} size={20} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {cases.length === 0 && !loading && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 p-12 rounded-lg border-2 border-dashed border-purple-200 text-center mb-8">
          <Beaker className="h-16 w-16 text-purple-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to simulate</h3>
          <p className="text-gray-600 mb-6">
            Choose a recovery scenario to see how Rozer detects revenue risk and selects the right intervention.
          </p>
        </div>
      )}

      {/* Full Simulation Button */}
      <div className="bg-white p-6 rounded-lg border shadow-sm mb-8">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Full Recovery Simulation</h3>
            <p className="text-gray-600 mb-4">
              Generate a realistic set of payment events and let the complete Rozer recovery pipeline analyze them automatically.
            </p>
          </div>
          <button
            onClick={runFullSimulation}
            disabled={loading}
            className="ml-4 flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-md"
          >
            {loading ? (
              <>
                <Loader className="animate-spin" size={20} />
                Running...
              </>
            ) : (
              <>
                <Play size={20} />
                Run Full Recovery
              </>
            )}
          </button>
        </div>
      </div>

      {/* Custom Analysis Form */}
      <div className="bg-gradient-to-br from-green-50 to-teal-50 p-6 rounded-lg border-2 border-green-200 shadow-sm mb-8">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">💡 Custom Payment Analysis</h3>
            <p className="text-gray-600">
              Enter your own payment details and let the AI agent evaluate recovery probability and recommend actions in real-time.
            </p>
          </div>
          <button
            onClick={() => setShowCustomForm(!showCustomForm)}
            className="ml-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
          >
            {showCustomForm ? 'Hide Form' : 'Analyze Custom Payment'}
          </button>
        </div>

        {showCustomForm && (
          <div className="bg-white p-6 rounded-lg border mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Amount Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Payment Amount (₹)
                </label>
                <input
                  type="number"
                  value={customInput.amount}
                  onChange={(e) => setCustomInput({...customInput, amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="25000"
                  min="0"
                />
                <p className="text-xs text-gray-500 mt-1">Enter amount in rupees (e.g., 25000 for ₹25,000)</p>
              </div>

              {/* Failure Code */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Failure Reason
                </label>
                <select
                  value={customInput.failure_code}
                  onChange={(e) => setCustomInput({...customInput, failure_code: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
                  <option value="CARD_DECLINED">Card Declined</option>
                  <option value="NETWORK_ERROR">Network Error</option>
                  <option value="BANK_OFFLINE">Bank Offline</option>
                  <option value="AUTHENTICATION_FAILED">Authentication Failed</option>
                  <option value="CHECKOUT_ABANDONED">Checkout Abandoned</option>
                  <option value="PAYMENT_TIMEOUT">Payment Timeout</option>
                </select>
              </div>

              {/* Customer Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer Type
                </label>
                <select
                  value={customInput.customer_type}
                  onChange={(e) => setCustomInput({...customInput, customer_type: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="new">New Customer (0 previous payments)</option>
                  <option value="returning">Returning Customer (5 payments, 4 successful)</option>
                  <option value="premium">Premium Customer (12 payments, 11 successful)</option>
                </select>
              </div>

              {/* Retry Count */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Previous Retry Attempts
                </label>
                <input
                  type="number"
                  value={customInput.retry_count}
                  onChange={(e) => setCustomInput({...customInput, retry_count: parseInt(e.target.value) || 0})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="1"
                  min="0"
                  max="5"
                />
                <p className="text-xs text-gray-500 mt-1">How many times has recovery been attempted? (0-5)</p>
              </div>

              {/* Hours Since Failure */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Since Failure (hours)
                </label>
                <input
                  type="number"
                  value={customInput.hours_since_failure}
                  onChange={(e) => setCustomInput({...customInput, hours_since_failure: parseFloat(e.target.value) || 0})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  placeholder="2"
                  min="0"
                  step="0.5"
                />
                <p className="text-xs text-gray-500 mt-1">How long ago did the payment fail? (e.g., 2.5)</p>
              </div>
            </div>

            {/* Analyze Button */}
            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                The agent will analyze your input using real recovery rules, scoring algorithms, and policy gates.
              </p>
              <button
                onClick={runCustomAnalysis}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {loading ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp size={20} />
                    Analyze Payment
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Scenario Cards */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Choose a Recovery Scenario</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className="bg-white p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center bg-${scenario.color}-100`}>
                  <scenario.icon className={`h-6 w-6 text-${scenario.color}-600`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">{scenario.title}</h3>
                  <p className="text-sm text-gray-600">{scenario.description}</p>
                </div>
              </div>
              <button
                onClick={() => runScenario(scenario.id)}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg font-medium disabled:opacity-50"
              >
                Run Scenario
                <ChevronRight size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Recovery Cases Table */}
      {cases.length > 0 && (
        <div className="bg-white rounded-lg border shadow-sm overflow-hidden mb-8">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Recovery Cases</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent Decision</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {cases.map((c) => (
                  <tr
                    key={c.payment_id}
                    onClick={() => setSelectedCase(c)}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-6 py-4">
                      <code className="text-sm text-gray-900">{c.payment_id}</code>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold">{formatINR(c.amount)}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        c.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                        c.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {c.risk_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{c.failure_reason}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{c.recommended_action}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        c.status === 'recovered' ? 'bg-green-100 text-green-800' :
                        c.status === 'pending' ? 'bg-blue-100 text-blue-800' :
                        c.status === 'no_action' ? 'bg-gray-100 text-gray-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {c.status === 'recovered' ? 'Recovered' :
                         c.status === 'pending' ? 'Pending' :
                         c.status === 'no_action' ? 'No Action' : 'Simulated'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Case Details Modal */}
      {selectedCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Recovery Case Details</h2>
              <button
                onClick={() => setSelectedCase(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Transaction Info */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Transaction</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">Payment ID</div>
                    <code className="text-sm font-semibold">{selectedCase.payment_id}</code>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Amount</div>
                    <div className="text-lg font-bold">{formatINR(selectedCase.amount)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Payment Method</div>
                    <div className="text-sm font-semibold">UPI</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Status</div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      selectedCase.status === 'recovered' ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {selectedCase.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Customer Context */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Customer Context</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">Customer Type</div>
                    <div className="text-sm font-semibold">{selectedCase.customer_type}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Previous Attempts</div>
                    <div className="text-sm font-semibold">{selectedCase.previous_attempts}</div>
                  </div>
                </div>
              </div>

              {/* Risk Analysis */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Risk Analysis</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Risk Score</span>
                    <span className="text-2xl font-bold">{selectedCase.risk_score}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        selectedCase.risk_level === 'HIGH' ? 'bg-red-600' :
                        selectedCase.risk_level === 'MEDIUM' ? 'bg-yellow-600' :
                        'bg-gray-600'
                      }`}
                      style={{ width: `${selectedCase.risk_score}%` }}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <div className="text-sm text-gray-500">Risk Level</div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        selectedCase.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                        selectedCase.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedCase.risk_level}
                      </span>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Recovery Probability</div>
                      <div className="text-sm font-semibold">{(selectedCase.recovery_probability * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Agent Reasoning */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Agent Reasoning</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700">{selectedCase.reason}</p>
                </div>
              </div>

              {/* Intervention */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Intervention</h3>
                <div className="bg-white border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-lg font-semibold text-gray-900">{selectedCase.recommended_action}</div>
                      <div className="text-sm text-gray-500 mt-1">Confidence: {selectedCase.confidence}%</div>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </div>
              </div>

              {/* Result */}
              {selectedCase.recovered_amount > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Result</h3>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <Check className="h-5 w-5 text-green-600" />
                      <span className="text-sm font-semibold text-green-900">
                        Simulated Recovery: {formatINR(selectedCase.recovered_amount)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <Check size={20} />
          {toast}
        </div>
      )}
    </div>
  )
}
