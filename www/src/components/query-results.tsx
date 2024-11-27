import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { Check, Code2, Copy, History } from 'lucide-react';
import { useState } from 'react';

import { QueryStatistics } from '../lib/types';
import { QueryStatisticsDisplay } from './query-statistics-display';

const QueryRow = ({ query, index }: { query: string; index: number }) => {
  const { toast } = useToast();
  const [copying, setCopying] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(query);
      setCopying(true);
      toast({
        title: 'Query copied to clipboard',
        description: `Query #${index + 1} has been copied to your clipboard.`,
      });
      setTimeout(() => setCopying(false), 1000);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to copy',
        description: 'Could not copy query to clipboard.',
      });
    }
  };

  return (
    <tr
      onClick={copyToClipboard}
      className='group cursor-pointer border-b transition-colors hover:bg-muted/50'
    >
      <td className='w-[60px] p-4 text-center font-mono text-muted-foreground'>
        {index + 1}
      </td>
      <td className='relative max-w-0 p-4'>
        <div className='flex w-full items-center gap-2'>
          <div className='w-full overflow-hidden'>
            <pre className='overflow-hidden text-ellipsis whitespace-pre-wrap break-all font-mono text-sm'>
              {query}
            </pre>
          </div>
          <Button
            size='icon'
            variant='ghost'
            className={cn(
              'shrink-0 opacity-0 transition-opacity group-hover:opacity-100',
              copying && 'text-green-500'
            )}
            onClick={(e) => {
              e.stopPropagation();
              copyToClipboard();
            }}
          >
            {copying ? (
              <Check className='h-4 w-4' />
            ) : (
              <Copy className='h-4 w-4' />
            )}
          </Button>
        </div>
      </td>
    </tr>
  );
};

const QueryTable = ({ queries }: { queries: string[] }) => (
  <div className='relative overflow-hidden rounded-md border'>
    <table className='w-full table-fixed border-collapse text-sm'>
      <colgroup>
        <col style={{ width: '60px' }} />
        <col style={{ width: 'calc(100% - 60px)' }} />
      </colgroup>
      <thead>
        <tr className='border-b bg-muted/50'>
          <th className='p-4 text-center font-medium text-muted-foreground'>
            #
          </th>
          <th className='p-4 text-left font-medium text-muted-foreground'>
            Query
          </th>
        </tr>
      </thead>
      <tbody>
        {queries.map((query, index) => (
          <QueryRow index={index} key={index} query={query} />
        ))}
      </tbody>
    </table>
  </div>
);

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
          <ScrollArea className='h-[500px] w-full'>
            <QueryTable queries={queries} />
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
