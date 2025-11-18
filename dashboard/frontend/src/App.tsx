import { useState, useEffect } from 'react'
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  AlertCircle,
  Building2,
  Activity,
  BarChart3
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Badge } from './components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './components/ui/table'

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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

function StatCard({ icon: Icon, title, value, subtitle, trend, gradient }: any) {
  return (
    <Card className="overflow-hidden border-none shadow-lg hover:shadow-xl transition-all duration-300">
      <div className={`bg-gradient-to-br ${gradient} p-6 text-white`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium opacity-90">{title}</p>
            <p className="text-4xl font-bold mt-2">{value}</p>
            {subtitle && (
              <p className="text-sm opacity-80 mt-1">{subtitle}</p>
            )}
          </div>
          <div className="p-3 rounded-full bg-white/20 backdrop-blur-sm">
            <Icon className="w-7 h-7" />
          </div>
        </div>
        {trend && (
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 mr-1" />
            <span className="font-medium">{trend}</span>
            <span className="ml-1 opacity-80">vs last period</span>
          </div>
        )}
      </div>
    </Card>
  )
}

function ComplianceChart({ stats }: { stats: DashboardStats }) {
  const data = [
    { name: 'Pass', value: stats.pass_count, color: '#10b981' },
    { name: 'Warning', value: stats.warning_count, color: '#f59e0b' },
    { name: 'Fail', value: stats.fail_count, color: '#ef4444' }
  ]

  return (
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          Compliance Distribution
        </CardTitle>
        <CardDescription>Overall contract review outcomes</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={90}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <RechartsTooltip />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg bg-green-50">
            <div className="text-3xl font-bold text-green-600">{stats.pass_count}</div>
            <div className="text-sm text-green-700 font-medium mt-1">Passed</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-yellow-50">
            <div className="text-3xl font-bold text-yellow-600">{stats.warning_count}</div>
            <div className="text-sm text-yellow-700 font-medium mt-1">Warnings</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-red-50">
            <div className="text-3xl font-bold text-red-600">{stats.fail_count}</div>
            <div className="text-sm text-red-700 font-medium mt-1">Failed</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ContractsTable({ contracts }: { contracts: ContractResult[] }) {
  const getStatusBadge = (status: string) => {
    const badges: any = {
      PASS: <Badge variant="success">Pass</Badge>,
      WARNING: <Badge variant="warning">Warning</Badge>,
      FAIL: <Badge variant="error">Fail</Badge>
    }
    return badges[status] || <Badge>{status}</Badge>
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
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              Recent Contracts
            </CardTitle>
            <CardDescription>Latest processed purchase agreements</CardDescription>
          </div>
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-md">
            View All
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="font-semibold">Contract ID</TableHead>
              <TableHead className="font-semibold">Property</TableHead>
              <TableHead className="font-semibold">Purchase Price</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Flags</TableHead>
              <TableHead className="font-semibold">Processed</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {contracts.map((contract) => (
              <TableRow key={contract.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">{contract.id}</TableCell>
                <TableCell className="max-w-xs truncate">
                  {contract.transaction_data.property_address || 'N/A'}
                </TableCell>
                <TableCell className="font-semibold">
                  {formatCurrency(contract.transaction_data.purchase_price)}
                </TableCell>
                <TableCell>{getStatusBadge(contract.compliance_status)}</TableCell>
                <TableCell>
                  {contract.compliance_flags.length > 0 ? (
                    <div className="flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      <span className="font-medium">{contract.compliance_flags.length}</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">None</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(contract.processed_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function RiskSummary({ contracts }: { contracts: ContractResult[] }) {
  const criticalIssues = contracts.filter(c =>
    c.compliance_flags.some(f => f.severity === 'CRITICAL')
  )

  return (
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Risk Summary
        </CardTitle>
        <CardDescription>Contracts requiring immediate attention</CardDescription>
      </CardHeader>
      <CardContent>
        {criticalIssues.length === 0 ? (
          <div className="text-center py-8">
            <div className="mx-auto w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <p className="text-lg font-semibold text-foreground">No Critical Issues</p>
            <p className="text-sm text-muted-foreground mt-2">All contracts are within acceptable parameters</p>
          </div>
        ) : (
          <div className="space-y-3">
            {criticalIssues.slice(0, 5).map((contract) => (
              <div key={contract.id} className="border-2 border-red-200 rounded-lg p-4 bg-red-50/50 hover:bg-red-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-red-600" />
                      <span className="font-semibold text-foreground">{contract.id}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {contract.transaction_data.property_address}
                    </p>
                    <div className="mt-3 space-y-2">
                      {contract.compliance_flags
                        .filter(f => f.severity === 'CRITICAL')
                        .map((flag, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-red-600 mt-1.5"></div>
                            <span className="text-sm text-red-900">{flag.description}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                  <button className="ml-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors shadow-md">
                    Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
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
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-6 text-lg font-medium text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-white to-orange-50">
        <Card className="max-w-md shadow-2xl">
          <CardContent className="pt-6 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
              <AlertCircle className="w-10 h-10 text-red-600" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Connection Error</h3>
            <p className="text-sm text-muted-foreground mb-6">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-medium shadow-lg"
            >
              Retry Connection
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-border shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg">
                <Building2 className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Contract Compliance Dashboard
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Executive Board Review • Real-time AI-Powered Analysis
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Last Updated</p>
                <p className="text-sm font-semibold text-foreground">
                  {new Date().toLocaleTimeString()}
                </p>
              </div>
              <div className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={FileText}
            title="Total Contracts"
            value={stats.total_contracts}
            subtitle="Processed to date"
            gradient="from-blue-600 to-blue-700"
          />
          <StatCard
            icon={CheckCircle2}
            title="Pass Rate"
            value={`${stats.pass_rate}%`}
            subtitle={`${stats.pass_count} of ${stats.total_contracts} passed`}
            trend="+5.2%"
            gradient="from-green-600 to-emerald-700"
          />
          <StatCard
            icon={DollarSign}
            title="Total Value"
            value={`$${(stats.total_transaction_value / 1000000).toFixed(1)}M`}
            subtitle="Transaction volume"
            gradient="from-purple-600 to-indigo-700"
          />
          <StatCard
            icon={Clock}
            title="Avg Processing"
            value={`${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`}
            subtitle="Per contract"
            gradient="from-orange-600 to-red-700"
          />
        </div>

        {/* Charts and Risk Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ComplianceChart stats={stats} />
          <RiskSummary contracts={contracts} />
        </div>

        {/* Contracts Table */}
        <ContractsTable contracts={contracts} />

        {/* Footer Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-red-50 to-white border-red-100">
            <CardContent className="pt-6">
              <div className="mx-auto w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mb-3">
                <AlertTriangle className="w-7 h-7 text-red-600" />
              </div>
              <div className="text-4xl font-bold text-red-600">{stats.critical_flags_count}</div>
              <div className="text-sm font-medium text-red-700 mt-2">Critical Flags</div>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-yellow-50 to-white border-yellow-100">
            <CardContent className="pt-6">
              <div className="mx-auto w-14 h-14 rounded-full bg-yellow-100 flex items-center justify-center mb-3">
                <AlertCircle className="w-7 h-7 text-yellow-600" />
              </div>
              <div className="text-4xl font-bold text-yellow-600">{stats.warning_flags_count}</div>
              <div className="text-sm font-medium text-yellow-700 mt-2">Warning Flags</div>
            </CardContent>
          </Card>
          <Card className="text-center shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-green-50 to-white border-green-100">
            <CardContent className="pt-6">
              <div className="mx-auto w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mb-3">
                <TrendingUp className="w-7 h-7 text-green-600" />
              </div>
              <div className="text-4xl font-bold text-green-600">
                {((stats.pass_count / stats.total_contracts) * 100).toFixed(0)}%
              </div>
              <div className="text-sm font-medium text-green-700 mt-2">Compliance Rate</div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

export default App
