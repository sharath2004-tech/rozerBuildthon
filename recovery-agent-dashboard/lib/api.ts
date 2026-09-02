/**
 * API Client for Backend Integration
 * Connects to FastAPI backend on http://localhost:8000
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Type definitions for backend responses
export interface RecoveryMetrics {
  total_attempted: number
  total_recovered: number
  recovery_rate: number
  roi: number
  total_cost: number
  active_cases: number
  period: string
}

export interface BatchResult {
  batch_id: string
  workflow_type: string
  total_cases: number
  amount_attempted: number
  amount_recovered: number
  recovery_rate: number
  roi: number
  total_cost: number
  completed_at: string
}

export interface ComplianceStats {
  total_checked: number
  blocked_count: number
  block_reasons: Record<string, number>
  period: string
}

export interface QueueItem {
  queue_id: number
  payment_id: string
  customer_id: string
  amount_inr: number
  reason: string
  created_at: string
  status: string
}

// API Functions

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend not responding')
  return res.json()
}

export async function getRecoveryMetrics(period: string = '7d'): Promise<RecoveryMetrics> {
  const res = await fetch(`${API_BASE}/analytics/recovery-metrics?period=${period}`)
  if (!res.ok) throw new Error('Failed to fetch recovery metrics')
  return res.json()
}

export async function getBatchResults(period: string = '7d', limit: number = 50): Promise<{ batches: BatchResult[]; period: string }> {
  const res = await fetch(`${API_BASE}/analytics/batch-results?period=${period}&limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch batch results')
  return res.json()
}

export async function getComplianceStats(period: string = '7d'): Promise<ComplianceStats> {
  const res = await fetch(`${API_BASE}/analytics/compliance-stats?period=${period}`)
  if (!res.ok) throw new Error('Failed to fetch compliance stats')
  return res.json()
}

export async function getQueue(): Promise<{ count: number; items: QueueItem[] }> {
  const res = await fetch(`${API_BASE}/queue`)
  if (!res.ok) throw new Error('Failed to fetch queue')
  return res.json()
}

export async function resolveQueue(queueId: number, resolution: 'approved' | 'rejected', resolvedBy: string) {
  const res = await fetch(`${API_BASE}/queue/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      queue_id: queueId,
      resolution,
      resolved_by: resolvedBy
    })
  })
  if (!res.ok) throw new Error('Failed to resolve queue item')
  return res.json()
}

export async function getLLMProviders() {
  const res = await fetch(`${API_BASE}/llm/providers`)
  if (!res.ok) throw new Error('Failed to fetch LLM providers')
  return res.json()
}

export async function getPolicyGates() {
  const res = await fetch(`${API_BASE}/policy/gates`)
  if (!res.ok) throw new Error('Failed to fetch policy gates')
  return res.json()
}

export async function getRuleMetrics() {
  const res = await fetch(`${API_BASE}/metrics/rules`)
  if (!res.ok) throw new Error('Failed to fetch rule metrics')
  return res.json()
}

// Utility: Format INR currency
export function formatINR(paise: number): string {
  const rupees = paise / 100
  return `₹${rupees.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

// Utility: Format compact INR (e.g., ₹1.2L)
export function formatCompactINR(paise: number): string {
  const rupees = paise / 100
  if (rupees >= 10000000) return `₹${(rupees / 10000000).toFixed(2)}Cr` // Crores
  if (rupees >= 100000) return `₹${(rupees / 100000).toFixed(2)}L` // Lakhs
  if (rupees >= 1000) return `₹${(rupees / 1000).toFixed(1)}K` // Thousands
  return `₹${rupees.toFixed(0)}`
}

// Utility: Format date
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
