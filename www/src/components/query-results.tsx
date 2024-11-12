import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Code2, History } from 'lucide-react';

import { QueryStatistics } from '../lib/types';
import { QueryStatisticsDisplay } from './query-statistics-display';

export const QueryResults = ({
  queries,
  statistics,
}: {
  queries: string[];
  statistics: QueryStatistics;
}) => (
  <Tabs defaultValue='queries' className='w-full'>
    <TabsList className='grid w-full grid-cols-2'>
      <TabsTrigger value='queries'>Generated Queries</TabsTrigger>
      <TabsTrigger value='stats'>Statistics</TabsTrigger>
    </TabsList>
    <TabsContent value='queries'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center'>
            <Code2 className='mr-2 h-4 w-4' />
            Generated Queries
            <span className='ml-2 text-sm text-muted-foreground'>
              ({queries.length} queries)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className='h-[500px] w-full rounded-md border p-4'>
            <div className='space-y-6'>
              {queries.map((query, index) => (
                <div key={index} className='font-mono text-sm'>
                  <div className='mb-1 text-muted-foreground'>
                    Query {index + 1}:
                  </div>
                  <pre className='whitespace-pre-wrap break-words'>{query}</pre>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </TabsContent>
    <TabsContent value='stats'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center'>
            <History className='mr-2 h-4 w-4' />
            Query Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <QueryStatisticsDisplay statistics={statistics} />
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
);
