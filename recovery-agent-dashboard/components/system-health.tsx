'use client'

import { useState } from 'react'
import { Activity, CheckCircle, XCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react'

interface HealthCheck {
  status: string
  message: string
  connected: boolean
  timestamp?: string
  [key: string]: any
}

interface HealthResults {
  timestamp: string
  checks: {
    groq: HealthCheck
    razorpay: HealthCheck
    database: HealthCheck
    webhook: HealthCheck
    agent: HealthCheck
    end_to_end: HealthCheck
  }
  overall: {
    healthy: boolean
    total_checks: number
    successful_checks: number
    failed_checks: number
    health_percentage: number
  }
}

export default function SystemHealth() {
  const [healthResults, setHealthResults] = useState<HealthResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runHealthChecks = async () => {
    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/system/health`)
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`)
      }
      
      const data = await response.json()
      setHealthResults(data)
    } catch (err: any) {
      setError(err.message || 'Failed to run health checks')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string, connected: boolean) => {
    if (status === 'success' && connected) {
      return <CheckCircle className="h-5 w-5 text-green-600" />
    } else if (status === 'warning') {
      return <AlertCircle className="h-5 w-5 text-yellow-600" />
    } else {
      return <XCircle className="h-5 w-5 text-red-600" />
    }
  }

  const getStatusText = (status: string, connected: boolean) => {
    if (status === 'success' && connected) return '🟢 Connected'
    if (status === 'warning') return '🟡 Warning'
    return '🔴 Failed'
  }

  const getStatusColor = (status: string, connected: boolean) => {
    if (status === 'success' && connected) return 'text-green-700 bg-green-50'
    if (status === 'warning') return 'text-yellow-700 bg-yellow-50'
    return 'text-red-700 bg-red-50'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="h-8 w-8 text-blue-600" />
            System Health
          </h1>
          <p className="text-gray-600 mt-1">
            Check connectivity and integration status of all services
          </p>
        </div>
        <button
          onClick={runHealthChecks}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Running Tests...
            </>
          ) : (
            <>
              <RefreshCw className="h-5 w-5" />
              Run Full System Test
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800">
            <XCircle className="h-5 w-5" />
            <span className="font-medium">Error:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Quick Status Grid */}
      {healthResults && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Razorpay */}
            <div className={`p-4 rounded-lg border ${getStatusColor(
              healthResults.checks.razorpay.status,
              healthResults.checks.razorpay.connected
            )}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(
                    healthResults.checks.razorpay.status,
                    healthResults.checks.razorpay.connected
                  )}
                  <span className="font-semibold">Razorpay API</span>
                </div>
                <span className="text-sm">
                  {getStatusText(
                    healthResults.checks.razorpay.status,
                    healthResults.checks.razorpay.connected
                  )}
                </span>
              </div>
              <p className="text-sm mt-2">{healthResults.checks.razorpay.message}</p>
              {healthResults.checks.razorpay.mode && (
                <p className="text-xs mt-1">
                  Mode: <span className="font-mono">{healthResults.checks.razorpay.mode}</span>
                </p>
              )}
            </div>

            {/* Groq AI */}
            <div className={`p-4 rounded-lg border ${getStatusColor(
              healthResults.checks.groq.status,
              healthResults.checks.groq.connected
            )}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(
                    healthResults.checks.groq.status,
                    healthResults.checks.groq.connected
                  )}
                  <span className="font-semibold">Groq AI</span>
                </div>
                <span className="text-sm">
                  {getStatusText(
                    healthResults.checks.groq.status,
                    healthResults.checks.groq.connected
                  )}
                </span>
              </div>
              <p className="text-sm mt-2">{healthResults.checks.groq.message}</p>
              {healthResults.checks.groq.model && (
                <p className="text-xs mt-1">
                  Model: <span className="font-mono">{healthResults.checks.groq.model}</span>
                </p>
              )}
            </div>

            {/* Database */}
            <div className={`p-4 rounded-lg border ${getStatusColor(
              healthResults.checks.database.status,
              healthResults.checks.database.connected
            )}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(
                    healthResults.checks.database.status,
                    healthResults.checks.database.connected
                  )}
                  <span className="font-semibold">Database</span>
                </div>
                <span className="text-sm">
                  {getStatusText(
                    healthResults.checks.database.status,
                    healthResults.checks.database.connected
                  )}
                </span>
              </div>
              <p className="text-sm mt-2">{healthResults.checks.database.message}</p>
              {healthResults.checks.database.database_type && (
                <p className="text-xs mt-1">
                  Type: <span className="font-mono">{healthResults.checks.database.database_type}</span>
                </p>
              )}
            </div>
          </div>

          {/* Detailed Status */}
          <div className="bg-white border rounded-lg">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold">Detailed Health Status</h2>
              <p className="text-sm text-gray-600 mt-1">
                Last checked: {new Date(healthResults.timestamp).toLocaleString()}
              </p>
            </div>

            <div className="divide-y">
              {/* Webhook */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(
                      healthResults.checks.webhook.status,
                      healthResults.checks.webhook.connected
                    )}
                    <h3 className="font-semibold">Webhook Processing</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(
                    healthResults.checks.webhook.status,
                    healthResults.checks.webhook.connected
                  )}`}>
                    {healthResults.checks.webhook.status}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{healthResults.checks.webhook.message}</p>
                {healthResults.checks.webhook.test_payment_id && (
                  <div className="mt-2 text-xs text-gray-600 space-y-1">
                    <p>Test Payment ID: <code className="bg-gray-100 px-2 py-1 rounded">{healthResults.checks.webhook.test_payment_id}</code></p>
                    <p>Classified as: <code className="bg-gray-100 px-2 py-1 rounded">{healthResults.checks.webhook.classified_as}</code></p>
                  </div>
                )}
              </div>

              {/* Agent */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(
                      healthResults.checks.agent.status,
                      healthResults.checks.agent.connected
                    )}
                    <h3 className="font-semibold">Agent Reasoning</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(
                    healthResults.checks.agent.status,
                    healthResults.checks.agent.connected
                  )}`}>
                    {healthResults.checks.agent.status}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{healthResults.checks.agent.message}</p>
                {healthResults.checks.agent.test_scenario && (
                  <div className="mt-2 text-xs text-gray-600 space-y-1">
                    <p>Test Scenario: {healthResults.checks.agent.test_scenario}</p>
                    <p>Recommended Action: <code className="bg-gray-100 px-2 py-1 rounded">{healthResults.checks.agent.recommended_action}</code></p>
                    <p>Disposition: <code className="bg-gray-100 px-2 py-1 rounded">{healthResults.checks.agent.disposition}</code></p>
                    <p>Rule: <code className="bg-gray-100 px-2 py-1 rounded">{healthResults.checks.agent.rule_applied}</code></p>
                  </div>
                )}
              </div>

              {/* End-to-End */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(
                      healthResults.checks.end_to_end.status,
                      healthResults.checks.end_to_end.connected
                    )}
                    <h3 className="font-semibold">End-to-End Flow</h3>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(
                    healthResults.checks.end_to_end.status,
                    healthResults.checks.end_to_end.connected
                  )}`}>
                    {healthResults.checks.end_to_end.steps_passed} / {healthResults.checks.end_to_end.steps_total} passed
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-3">{healthResults.checks.end_to_end.message}</p>
                
                {healthResults.checks.end_to_end.steps && (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
                    {Object.entries(healthResults.checks.end_to_end.steps).map(([step, passed]: [string, any]) => (
                      <div key={step} className={`px-3 py-2 rounded ${passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                        {passed ? '✓' : '✗'} {step.replace('_', ' ')}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Overall Summary */}
          <div className={`p-6 rounded-lg border-2 ${
            healthResults.overall.healthy
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  {healthResults.overall.healthy ? (
                    <>
                      <CheckCircle className="h-6 w-6 text-green-600" />
                      <span className="text-green-900">System Healthy</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-6 w-6 text-red-600" />
                      <span className="text-red-900">System Issues Detected</span>
                    </>
                  )}
                </h3>
                <p className={`text-sm mt-1 ${healthResults.overall.healthy ? 'text-green-700' : 'text-red-700'}`}>
                  {healthResults.overall.successful_checks} of {healthResults.overall.total_checks} checks passed
                  ({healthResults.overall.health_percentage.toFixed(1)}%)
                </p>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${healthResults.overall.healthy ? 'text-green-700' : 'text-red-700'}`}>
                  {healthResults.overall.health_percentage.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">Health Score</div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Initial State */}
      {!healthResults && !loading && !error && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed">
          <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Run System Health Check
          </h3>
          <p className="text-gray-600 mb-6">
            Click the button above to test all integrations and verify system health
          </p>
          <div className="text-sm text-gray-500 space-y-1">
            <p>✓ Tests real API connectivity</p>
            <p>✓ Verifies webhook processing</p>
            <p>✓ Checks agent reasoning</p>
            <p>✓ Validates end-to-end flow</p>
          </div>
        </div>
      )}
    </div>
  )
}
