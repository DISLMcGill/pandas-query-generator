import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Settings } from '@/lib/types';
import { Settings2 } from 'lucide-react';

export const SettingsDialog = ({
  settings,
  onSettingChange,
}: {
  settings: Settings;
  onSettingChange: (setting: string, value: number) => void;
}) => (
  <Dialog>
    <DialogTrigger asChild>
      <Button variant='outline' className='w-full'>
        <Settings2 className='mr-2 h-4 w-4' />
        Settings
      </Button>
    </DialogTrigger>
    <DialogContent className='max-w-2xl'>
      <DialogHeader>
        <DialogTitle>Settings</DialogTitle>
        <DialogDescription>
          Customize the parameters for generating pandas queries
        </DialogDescription>
      </DialogHeader>
      <div className='grid gap-4 py-4'>
        <div className='flex items-center space-x-2'>
          <Label className='w-[200px]'>Number of Queries</Label>
          <Input
            type='number'
            min={1}
            max={100000}
            value={settings.numQueries}
            onChange={(e) => {
              const value = parseInt(e.target.value);
              if (!isNaN(value) && value > 0 && value <= 100000) {
                onSettingChange('numQueries', value);
              }
            }}
            className='w-24'
          />
        </div>
        {[
          {
            name: 'selectionProbability',
            label: 'Selection Probability',
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: 'projectionProbability',
            label: 'Projection Probability',
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: 'groupbyProbability',
            label: 'Group By Probability',
            min: 0,
            max: 1,
            step: 0.1,
          },
          {
            name: 'maxGroupbyColumns',
            label: 'Max Group By Columns',
            min: 1,
            max: 10,
            step: 1,
          },
          {
            name: 'maxMerges',
            label: 'Max Merges',
            min: 1,
            max: 20,
            step: 1,
          },
          {
            name: 'maxProjectionColumns',
            label: 'Max Projection Columns',
            min: 1,
            max: 20,
            step: 1,
          },
          {
            name: 'maxSelectionConditions',
            label: 'Max Selection Conditions',
            min: 1,
            max: 20,
            step: 1,
          },
        ].map((slider) => (
          <div key={slider.name} className='flex items-center space-x-2'>
            <Label className='w-[200px]'>{slider.label}</Label>
            <div className='flex-1'>
              <Slider
                min={slider.min}
                max={slider.max}
                step={slider.step}
                value={[settings[slider.name as keyof Settings]]}
                onValueChange={([value]) => onSettingChange(slider.name, value)}
              />
            </div>
            <span className='w-12 text-right'>
              {settings[slider.name as keyof Settings]}
            </span>
          </div>
        ))}
      </div>
    </DialogContent>
  </Dialog>
);
