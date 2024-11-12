import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { EXAMPLE_SCHEMAS } from '@/lib/constants';
import { Code2 } from 'lucide-react';

import { cn } from '../lib/utils';

const SchemaSelector = ({
  selectedType,
  onSchemaSelect,
  className,
}: {
  selectedType: string;
  onSchemaSelect: (value: string, type: string) => void;
  className?: string;
}) => (
  <div className={cn('mb-4', className)}>
    <Select
      value={selectedType}
      onValueChange={(value) => {
        const selectedSchema = (EXAMPLE_SCHEMAS as any)[value];
        onSchemaSelect(JSON.stringify(selectedSchema, null, 2), value);
      }}
    >
      <SelectTrigger className='w-[200px]'>
        <SelectValue placeholder='Select example schema' />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value='tpch'>TPC-H Schema</SelectItem>
        <SelectItem value='sports'>Sports Schema</SelectItem>
        <SelectItem value='customer'>Customer Schema</SelectItem>
      </SelectContent>
    </Select>
  </div>
);

export const SchemaDialog = ({
  schema,
  selectedType,
  onSchemaChange,
}: {
  schema: string;
  selectedType: string;
  onSchemaChange: (schema: string, type: string) => void;
}) => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant='outline' className='w-full'>
          <Code2 className='mr-2 h-4 w-4' />
          Schema
        </Button>
      </DialogTrigger>
      <DialogContent className='max-h-[90vh] max-w-4xl overflow-y-auto'>
        <DialogHeader>
          <DialogTitle className='flex items-center justify-between'>
            <span>Schema</span>
          </DialogTitle>
          <DialogDescription>
            Define your database schema in JSON format
          </DialogDescription>
        </DialogHeader>
        <div className='space-y-4'>
          <SchemaSelector
            className='mt-auto w-full'
            selectedType={selectedType}
            onSchemaSelect={onSchemaChange}
          />
          <Textarea
            value={schema}
            onChange={(e) => onSchemaChange(e.target.value, selectedType)}
            className='min-h-[60vh] font-mono'
            placeholder='Enter your schema JSON here...'
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};
