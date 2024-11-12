import { Button } from '@/components/ui/button';
import { Github } from 'lucide-react';

import { ModeToggle } from './mode-toggle';

export const Navbar = () => (
  <div className='flex items-center justify-between bg-card p-4'>
    <div>
      <p className='text-3xl font-semibold'>Pandas Query Generator 🐼</p>
      <p className='text-md text-muted-foreground'>
        An interactive web demonstration
      </p>
    </div>
    <div className='flex items-center space-x-4'>
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
