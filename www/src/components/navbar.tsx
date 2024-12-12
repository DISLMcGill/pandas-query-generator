import { Button } from '@/components/ui/button';
import { Book, Github } from 'lucide-react';

import { ModeToggle } from './mode-toggle';

export const Navbar = () => (
  <div className='flex items-center justify-between bg-card p-4'>
    <div>
      <a href='/pandas-query-generator'>
        <p className='text-3xl font-semibold'>Pandas Query Generator 🐼</p>
      </a>
      <p className='text-md text-muted-foreground'>
        A web interface for the{' '}
        <a href='https://pypi.org/project/pqg/' target='blank'>
          <p className='inline font-bold'>pqg</p>
        </a>{' '}
        Python pacakge
      </p>
    </div>
    <div className='flex items-center space-x-4'>
      <Button variant='outline' size='icon' asChild>
        <a href='/pandas-query-generator/docs/index.html' target='_blank'>
          <Book className='h-4 w-4' />
        </a>
      </Button>
      <Button variant='outline' size='icon' asChild>
        <a
          href='https://github.com/DISLMcGill/pandas-query-generator'
          target='_blank'
        >
          <Github className='h-4 w-4' />
        </a>
      </Button>
      <ModeToggle />
    </div>
  </div>
);
