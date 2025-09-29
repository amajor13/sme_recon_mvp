import { BarChart3, CheckCircle2, ThumbsUp, MinusCircle, AlertTriangle, Target, Percent, TrendingUp, TrendingDown, Calculator } from 'lucide-react';
import { ReconciliationMetrics } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface MetricsPanelProps {
  metrics: ReconciliationMetrics;
}

interface MetricCard {
  label: string;
  value: string | number;
  icon: React.ComponentType<any>;
  type: 'success' | 'warning' | 'error' | 'info';
}

// MetricCard component
function MetricCard({ metric }: { metric: MetricCard }) {
  const IconComponent = metric.icon;
  
  const getBadgeVariant = (type: string) => {
    switch(type) {
      case 'success':
        return 'default' as const;
      case 'warning':
        return 'secondary' as const;
      case 'error':
        return 'destructive' as const;
      default:
        return 'outline' as const;
    }
  };

  const getIconColorClasses = (type: string) => {
    switch(type) {
      case 'success':
        return 'text-emerald-600 bg-emerald-50';
      case 'warning':
        return 'text-amber-600 bg-amber-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-blue-600 bg-blue-50';
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-lg ${getIconColorClasses(metric.type)}`}>
            <IconComponent className="w-4 h-4" />
          </div>
          <Badge variant={getBadgeVariant(metric.type)} className="text-xs">
            {metric.type}
          </Badge>
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            {metric.label}
          </p>
          <p className="text-2xl font-bold">
            {metric.value}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  // Format currency helper
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const metricCards: MetricCard[] = [
    // 1. Core Totals - Most Important
    {
      label: 'Total Records',
      value: metrics.total_records || 0,
      icon: Calculator,
      type: 'info'
    },
    {
      label: 'Total Matches',
      value: metrics.total_matches || 0,
      icon: CheckCircle2,
      type: 'success'
    },
    {
      label: 'Perfect Amount Matches',
      value: metrics.perfect_amount_matches || 0,
      icon: Target,
      type: 'success'
    },
    {
      label: 'Match Rate',
      value: `${(metrics.match_rate || 0).toFixed(1)}%`,
      icon: Percent,
      type: (metrics.match_rate || 0) >= 80 ? 'success' : (metrics.match_rate || 0) >= 60 ? 'warning' : 'error'
    },

    // 2. Match Quality Distribution
    {
      label: 'High Confidence',
      value: metrics.high_confidence || 0,
      icon: ThumbsUp,
      type: 'success'
    },
    {
      label: 'Medium Confidence',
      value: metrics.medium_confidence || 0,
      icon: MinusCircle,
      type: 'warning'
    },
    {
      label: 'Low Confidence',
      value: metrics.low_confidence || 0,
      icon: AlertTriangle,
      type: 'error'
    },
    {
      label: 'Average Score',
      value: `${((metrics.average_score || 0) * 100).toFixed(1)}%`,
      icon: Target,
      type: (metrics.average_score || 0) >= 0.95 ? 'success' : (metrics.average_score || 0) >= 0.85 ? 'warning' : 'error'
    },

    // 3. Financial Totals
    {
      label: 'GSTR2B Total',
      value: formatCurrency(metrics.gstr2b_total || 0),
      icon: TrendingUp,
      type: 'info'
    },
    {
      label: 'Tally Total',
      value: formatCurrency(metrics.tally_total || 0),
      icon: TrendingDown,
      type: 'info'
    },
    
    // 4. Variance & Differences
    {
      label: 'Total Variance',
      value: formatCurrency(metrics.total_variance || 0),
      icon: Calculator,
      type: (metrics.total_variance || 0) === 0 ? 'success' : 'warning'
    },
    {
      label: 'Largest Discrepancy',
      value: formatCurrency(metrics.largest_discrepancy || 0),
      icon: AlertTriangle,
      type: (metrics.largest_discrepancy || 0) === 0 ? 'success' : 'warning'
    }
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <CardTitle className="text-2xl">Reconciliation Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Core Metrics - Most Important */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wide">Core Statistics</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {metricCards.slice(0, 4).map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>
          </div>

          {/* Match Quality */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wide">Match Quality</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {metricCards.slice(4, 8).map((metric, index) => (
                <MetricCard key={index + 4} metric={metric} />
              ))}
            </div>
          </div>

          {/* Financial Overview */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-3 uppercase tracking-wide">Financial Overview</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {metricCards.slice(8).map((metric, index) => (
                <MetricCard key={index + 8} metric={metric} />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}