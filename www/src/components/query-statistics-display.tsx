import { Card, CardContent } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts';

import { QueryStatistics } from '../lib/types';
import { calculateMeanStd, cn } from '../lib/utils';

const StatCard = ({
  title,
  children,
  className,
  tooltip,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  tooltip?: string;
}) => (
  <div className={cn('rounded-lg border p-4', className)}>
    <h3 className='mb-2 flex items-center gap-2 text-lg font-semibold'>
      {title}
      {tooltip && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className='h-4 w-4 text-muted-foreground transition-colors hover:text-foreground' />
            </TooltipTrigger>
            <TooltipContent className='max-w-xs'>
              <p>{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </h3>
    {children}
  </div>
);

const StatRow = ({
  label,
  value,
  target,
}: {
  label: string;
  value: string | number;
  target?: string | number;
  help?: string;
}) => (
  <div className='flex items-center justify-between py-1'>
    <span className='text-muted-foreground'>{label}</span>
    <div className='flex items-center gap-2'>
      <span className='font-medium'>{value}</span>
      {target && (
        <>
          <span className='text-muted-foreground'>vs</span>
          <span className='text-muted-foreground'>{target}</span>
        </>
      )}
    </div>
  </div>
);

const QueryStatisticsChart = ({
  statistics,
  className,
}: {
  statistics: QueryStatistics;
  className?: string;
}) => {
  const mergeProbability =
    (statistics.query_structure.max_merges /
      (statistics.query_structure.max_merges + 1)) *
    100;

  const probabilityData = [
    {
      name: 'Selection',
      target: statistics.query_structure.selection_probability * 100,
      actual:
        (statistics.queries_with_selection / statistics.total_queries) * 100,
    },
    {
      name: 'Projection',
      target: statistics.query_structure.projection_probability * 100,
      actual:
        (statistics.queries_with_projection / statistics.total_queries) * 100,
    },
    {
      name: 'Merge',
      target: mergeProbability,
      actual: (statistics.queries_with_merge / statistics.total_queries) * 100,
    },
    {
      name: 'Group By',
      target: statistics.query_structure.groupby_aggregation_probability * 100,
      actual:
        (statistics.queries_with_groupby / statistics.total_queries) * 100,
    },
  ];

  const operationCountsData = statistics.selection_conditions.map(
    (count, index) => ({
      queryIndex: index + 1,
      selectionConditions: count,
      projectionColumns: statistics.projection_columns[index] || 0,
      mergeCount: statistics.merge_count[index] || 0,
      groupByColumns: statistics.groupby_columns[index] || 0,
    })
  );

  return (
    <Card className={cn('w-full', className)}>
      <CardContent className='p-8'>
        <div className='space-y-8'>
          <div>
            <h3 className='mb-4 text-lg font-semibold'>
              Operation Probabilities
            </h3>
            <div className='h-64'>
              <ResponsiveContainer width='100%' height='100%'>
                <BarChart data={probabilityData}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='name' />
                  <YAxis unit='%' />
                  <RechartsTooltip
                    formatter={(value) => `${value.toFixed(1)}`}
                    labelStyle={{ color: 'black' }}
                  />
                  <Legend />
                  <Bar
                    dataKey='target'
                    fill='hsl(var(--chart-1))'
                    name='Target %'
                  />
                  <Bar
                    dataKey='actual'
                    fill='hsl(var(--chart-2))'
                    name='Actual %'
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div>
            <h3 className='mb-4 text-lg font-semibold'>
              Operation Counts Distribution
            </h3>
            <div className='h-64'>
              <ResponsiveContainer width='100%' height='100%'>
                <LineChart data={operationCountsData}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis
                    dataKey='queryIndex'
                    label={{
                      value: 'Query Index',
                      position: 'insideBottom',
                      offset: -5,
                    }}
                  />
                  <YAxis
                    label={{
                      value: 'Count',
                      angle: -90,
                      position: 'insideLeft',
                    }}
                  />
                  <RechartsTooltip />
                  <Legend />
                  <Line
                    type='monotone'
                    dataKey='selectionConditions'
                    stroke='hsl(var(--chart-2))'
                    name='Selection Conditions'
                    dot={false}
                  />
                  <Line
                    type='monotone'
                    dataKey='projectionColumns'
                    stroke='hsl(var(--chart-3))'
                    name='Projection Columns'
                    dot={false}
                  />
                  <Line
                    type='monotone'
                    dataKey='mergeCount'
                    stroke='hsl(var(--chart-4))'
                    name='Merge Count'
                    dot={false}
                  />
                  <Line
                    type='monotone'
                    dataKey='groupByColumns'
                    stroke='hsl(var(--chart-5))'
                    name='Group By Columns'
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const QueryStatisticsDisplay = ({
  statistics,
}: {
  statistics: QueryStatistics;
}) => {
  const selectionStats = calculateMeanStd(statistics.selection_conditions);
  const projectionStats = calculateMeanStd(statistics.projection_columns);
  const groupByStats = calculateMeanStd(statistics.groupby_columns);
  const mergeStats = calculateMeanStd(statistics.merge_count);

  const getPercentage = (count: number) =>
    ((count / statistics.total_queries) * 100).toFixed(1);

  return (
    <div className='space-y-6'>
      <div className='grid grid-cols-1 gap-4 md:grid-cols-2'>
        <StatCard
          title='Operation Probabilities'
          tooltip="Shows the percentage of queries that include each operation type. 'Actual' percentages are calculated as (queries with operation / total queries) × 100. 'Target' values are the probabilities set in the settings."
        >
          <div className='space-y-2'>
            <StatRow
              label='Selection'
              value={`${getPercentage(statistics.queries_with_selection)}%`}
              target={`${(statistics.query_structure.selection_probability * 100).toFixed(1)}%`}
            />
            <StatRow
              label='Projection'
              value={`${getPercentage(statistics.queries_with_projection)}%`}
              target={`${(statistics.query_structure.projection_probability * 100).toFixed(1)}%`}
            />
            <StatRow
              label='Merge'
              value={`${getPercentage(statistics.queries_with_merge)}%`}
              target={`${((statistics.query_structure.max_merges / (statistics.query_structure.max_merges + 1)) * 100).toFixed(1)}%`}
            />
            <StatRow
              label='Group By'
              value={`${getPercentage(statistics.queries_with_groupby)}%`}
              target={`${(statistics.query_structure.groupby_aggregation_probability * 100).toFixed(1)}%`}
            />
          </div>
        </StatCard>

        <StatCard
          title='Operation Counts'
          tooltip="Shows statistics for the number of operations in each query. Values are shown as mean ± standard deviation. 'Target' values show the maximum allowed counts set in the settings."
        >
          <div className='space-y-2'>
            <StatRow
              label='Selection Conditions'
              value={`${selectionStats.mean.toFixed(1)} ± ${selectionStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_selection_conditions}
            />
            <StatRow
              label='Projection Columns'
              value={`${projectionStats.mean.toFixed(1)} ± ${projectionStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_projection_columns}
            />
            <StatRow
              label='Merges'
              value={`${mergeStats.mean.toFixed(1)} ± ${mergeStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_merges}
            />
            <StatRow
              label='Group By Columns'
              value={`${groupByStats.mean.toFixed(1)} ± ${groupByStats.std.toFixed(1)}`}
              target={statistics.query_structure.max_groupby_columns}
            />
          </div>
        </StatCard>
        <QueryStatisticsChart className='col-span-2' statistics={statistics} />
        <StatCard title='Execution Results' className='md:col-span-2'>
          <div className='grid grid-cols-1 gap-4 md:grid-cols-3'>
            <div className='flex flex-col items-center justify-center rounded-lg border bg-background p-4'>
              <div className='text-2xl font-bold'>
                {statistics.total_queries}
              </div>
              <div className='text-center text-sm text-muted-foreground'>
                Total Queries
              </div>
            </div>
            <div className='flex flex-col items-center justify-center rounded-lg border bg-background p-4'>
              <div className='text-2xl font-bold text-green-500'>
                {(
                  (statistics.execution_results.successful /
                    statistics.total_queries) *
                  100
                ).toFixed(1)}
                %
              </div>
              <div className='text-center text-sm text-muted-foreground'>
                Success Rate
              </div>
            </div>
            <div className='flex flex-col items-center justify-center rounded-lg border bg-background p-4'>
              <div className='text-2xl font-bold text-yellow-500'>
                {(
                  (statistics.execution_results.empty /
                    statistics.total_queries) *
                  100
                ).toFixed(1)}
                %
              </div>
              <div className='text-center text-sm text-muted-foreground'>
                Empty Result Sets
              </div>
            </div>
          </div>
          {Object.keys(statistics.execution_results.errors).length > 0 && (
            <div className='mt-4'>
              <h4 className='mb-2 font-semibold'>Errors</h4>
              <div className='space-y-1'>
                {Object.entries(statistics.execution_results.errors).map(
                  ([error, count]) => (
                    <div key={error} className='flex justify-between text-sm'>
                      <span className='text-muted-foreground'>{error}</span>
                      <span>{count}</span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </StatCard>
      </div>
    </div>
  );
};
