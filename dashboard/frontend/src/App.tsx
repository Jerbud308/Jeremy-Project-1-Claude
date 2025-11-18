import { useState, useEffect } from 'react'
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  AlertCircle,
  Building2
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

// ============================================================================
// TYPES
// ============================================================================

interface ComplianceFlag {
  check_id: string
  severity: string
  description: string
  justification: string
}

interface TransactionData {
  property_address?: string
  buyer_name?: string
  seller_name?: string
  purchase_price?: number
  earnest_money_amount?: number
  closing_date?: string
  extraction_confidence_score: number
}

interface ContractResult {
  id: string
  processed_at: string
  transaction_data: TransactionData
  compliance_status: string
  compliance_flags: ComplianceFlag[]
  processing_time_ms: number
}

interface DashboardStats {
  total_contracts: number
  pass_count: number
  warning_count: number
  fail_count: number
  pass_rate: number
  avg_processing_time_ms: number
  total_transaction_value: number
  critical_flags_count: number
  warning_flags_count: number
}

// ============================================================================
// API CLIENT
// ============================================================================

const API_BASE_URL = 'http://localhost:8000'

async function fetchStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/api/stats`)
  if (!response.ok) throw new Error('Failed to fetch stats')
  return response.json()
}

async function fetchContracts(): Promise<ContractResult[]> {
  const response = await fetch(`${API_BASE_URL}/api/contracts?limit=10`)
  if (!response.ok) throw new Error('Failed to fetch contracts')
  return response.json()
}

// ============================================================================
// COMPONENTS
// ============================================================================

function StatCard({ icon: Icon, title, value, subtitle, trend, colorClass }: any) {
  return (
    <div className="stat-card">
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-3xl font-bold mt-2 ${colorClass}`}>{value}</p>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`p-3 rounded-full ${colorClass.replace('text-', 'bg-').replace('600', '100')}`}>
            <Icon className={`w-8 h-8 ${colorClass}`} />
          </div>
        </div>
        {trend && (
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600 font-medium">{trend}</span>
            <span className="text-gray-500 ml-1">vs last period</span>
          </div>
        )}
      </div>
    </div>
  )
}

function ComplianceChart({ stats }: { stats: DashboardStats }) {
  const data = [
    { name: 'Pass', value: stats.pass_count, color: '#10b981' },
    { name: 'Warning', value: stats.warning_count, color: '#f59e0b' },
    { name: 'Fail', value: stats.fail_count, color: '#ef4444' }
  ]

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-900">Compliance Status Distribution</h3>
        <p className="text-sm text-gray-500 mt-1">Overall contract review outcomes</p>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.pass_count}</div>
            <div className="text-sm text-gray-600">Passed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.warning_count}</div>
            <div className="text-sm text-gray-600">Warnings</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.fail_count}</div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ContractsTable({ contracts }: { contracts: ContractResult[] }) {
  const getStatusBadge = (status: string) => {
    const badges: any = {
      PASS: <span className="badge-success">Pass</span>,
      WARNING: <span className="badge-warning">Warning</span>,
      FAIL: <span className="badge-error">Fail</span>
    }
    return badges[status] || <span className="badge">{status}</span>
  }

  const formatCurrency = (amount?: number) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recent Contracts</h3>
            <p className="text-sm text-gray-500 mt-1">Latest processed purchase agreements</p>
          </div>
          <button className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
            View All
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contract ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Property
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Purchase Price
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Flags
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Processed
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {contracts.map((contract) => (
              <tr key={contract.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {contract.id}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                  {contract.transaction_data.property_address || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                  {formatCurrency(contract.transaction_data.purchase_price)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(contract.compliance_status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {contract.compliance_flags.length > 0 ? (
                    <div className="flex items-center">
                      <AlertTriangle className="w-4 h-4 text-yellow-500 mr-1" />
                      <span className="text-gray-900">{contract.compliance_flags.length}</span>
                    </div>
                  ) : (
                    <span className="text-gray-400">None</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(contract.processed_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RiskSummary({ contracts }: { contracts: ContractResult[] }) {
  const criticalIssues = contracts.filter(c =>
    c.compliance_flags.some(f => f.severity === 'CRITICAL')
  )

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-900">Risk Summary</h3>
        <p className="text-sm text-gray-500 mt-1">Contracts requiring immediate attention</p>
      </div>
      <div className="card-body">
        {criticalIssues.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="text-lg font-medium text-gray-900">No Critical Issues</p>
            <p className="text-sm text-gray-500 mt-1">All contracts are within acceptable parameters</p>
          </div>
        ) : (
          <div className="space-y-3">
            {criticalIssues.slice(0, 5).map((contract) => (
              <div key={contract.id} className="border border-red-200 rounded-lg p-4 bg-red-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                      <span className="font-medium text-gray-900">{contract.id}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {contract.transaction_data.property_address}
                    </p>
                    <div className="mt-2 space-y-1">
                      {contract.compliance_flags
                        .filter(f => f.severity === 'CRITICAL')
                        .map((flag, idx) => (
                          <div key={idx} className="text-sm text-red-700">
                            • {flag.description}
                          </div>
                        ))}
                    </div>
                  </div>
                  <button className="ml-4 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors">
                    Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// MAIN APP
// ============================================================================

function App() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [contracts, setContracts] = useState<ContractResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [statsData, contractsData] = await Promise.all([
          fetchStats(),
          fetchContracts()
        ])
        setStats(statsData)
        setContracts(contractsData)
        setError(null)
      } catch (err) {
        setError('Failed to load dashboard data. Make sure the backend is running.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <p className="text-lg font-medium text-gray-900">Connection Error</p>
          <p className="text-sm text-gray-600 mt-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Building2 className="w-10 h-10 text-primary-600 mr-3" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Contract Compliance Dashboard
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  Executive Board Review | Real-time AI-Powered Analysis
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm text-gray-500">Last Updated</p>
                <p className="text-sm font-medium text-gray-900">
                  {new Date().toLocaleTimeString()}
                </p>
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={FileText}
            title="Total Contracts"
            value={stats.total_contracts}
            subtitle="Processed to date"
            colorClass="text-primary-600"
          />
          <StatCard
            icon={CheckCircle2}
            title="Pass Rate"
            value={`${stats.pass_rate}%`}
            subtitle={`${stats.pass_count} of ${stats.total_contracts} passed`}
            trend="+5.2%"
            colorClass="text-green-600"
          />
          <StatCard
            icon={DollarSign}
            title="Total Value"
            value={`$${(stats.total_transaction_value / 1000000).toFixed(1)}M`}
            subtitle="Transaction volume"
            colorClass="text-blue-600"
          />
          <StatCard
            icon={Clock}
            title="Avg Processing"
            value={`${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`}
            subtitle="Per contract"
            colorClass="text-purple-600"
          />
        </div>

        {/* Charts and Risk Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ComplianceChart stats={stats} />
          <RiskSummary contracts={contracts} />
        </div>

        {/* Contracts Table */}
        <ContractsTable contracts={contracts} />

        {/* Footer Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="card-body text-center">
              <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">{stats.critical_flags_count}</div>
              <div className="text-sm text-gray-600">Critical Flags</div>
            </div>
          </div>
          <div className="card">
            <div className="card-body text-center">
              <AlertCircle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">{stats.warning_flags_count}</div>
              <div className="text-sm text-gray-600">Warning Flags</div>
            </div>
          </div>
          <div className="card">
            <div className="card-body text-center">
              <TrendingUp className="w-8 h-8 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">
                {((stats.pass_count / stats.total_contracts) * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600">Compliance Rate</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
