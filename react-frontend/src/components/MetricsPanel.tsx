import { BarChart3, CheckCircle2, ThumbsUp, MinusCircle, AlertTriangle, Target, Percent, DollarSign, TrendingUp, TrendingDown, Calculator } from 'lucide-react';
import { ReconciliationMetrics } from '../types';
import { formatCurrency } from '../utils';
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

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  // Financial insights
  const totalGstr2b = metrics.total_gstr2b_amount || 0;
  const totalTally = metrics.total_tally_amount || 0;
  const totalDifference = metrics.total_amount_difference || 0;
  const largestDiscrepancy = metrics.largest_discrepancy || 0;
  const perfectMatches = metrics.perfect_matches || 0;
  const totalTransactions = metrics.total_transactions || 0;
  
  const metricCards: MetricCard[] = [
    // Match Quality Metrics
    {
      label: 'Total Matches',
      value: metrics.total_matches,
      icon: CheckCircle2,
      type: 'success'
    },
    {
      label: 'Perfect Amount Matches',
      value: perfectMatches,
      icon: Target,
      type: 'success'
    },
    {
      label: 'High Confidence',
      value: metrics.high_confidence,
      icon: ThumbsUp,
      type: 'success'
    },
    {
      label: 'Medium Confidence',
      value: metrics.medium_confidence,
      icon: MinusCircle,
      type: 'warning'
    },
    {
      label: 'Low Confidence',
      value: metrics.low_confidence,
      icon: AlertTriangle,
      type: 'error'
    },
    {
      label: 'Match Rate',
      value: `${((metrics.total_matches / Math.max(totalTransactions, 1)) * 100).toFixed(1)}%`,
      icon: Percent,
      type: 'info'
    },
    // Financial Metrics
    {
      label: 'GSTR2B Total',
      value: formatCurrency(totalGstr2b),
      icon: TrendingUp,
      type: 'info'
    },
    {
      label: 'Tally Total',
      value: formatCurrency(totalTally),
      icon: TrendingDown,
      type: 'info'
    },
    {
      label: 'Total Variance',
      value: formatCurrency(Math.abs(totalGstr2b - totalTally)),
      icon: Calculator,
      type: totalGstr2b === totalTally ? 'success' : 'warning'
    },
    {
      label: 'Amount Differences',
      value: formatCurrency(totalDifference),
      icon: DollarSign,
      type: totalDifference < 1000 ? 'success' : totalDifference < 10000 ? 'warning' : 'error'
    },
    {
      label: 'Largest Discrepancy',
      value: formatCurrency(largestDiscrepancy),
      icon: AlertTriangle,
      type: largestDiscrepancy < 100 ? 'success' : largestDiscrepancy < 1000 ? 'warning' : 'error'
    },
    {
      label: 'Average Score',
      value: `${(metrics.average_score * 100).toFixed(1)}%`,
      icon: Target,
      type: metrics.average_score >= 0.95 ? 'success' : metrics.average_score >= 0.85 ? 'warning' : 'error'
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {metricCards.map((metric, index) => {
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
              <Card key={index} className="hover:shadow-md transition-shadow duration-200">
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
          })}
        </div>
      </CardContent>
    </Card>
  );
}