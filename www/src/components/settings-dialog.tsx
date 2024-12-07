import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Settings } from '@/lib/types';
import { RotateCcw, Settings2 } from 'lucide-react';

const DEFAULT_SETTINGS: Settings = {
  enforceNonEmptyResults: false,
  groupbyProbability: 0.5,
  maxGroupbyColumns: 5,
  maxMerges: 2,
  maxProjectionColumns: 5,
  maxSelectionConditions: 5,
  multiLine: false,
  numQueries: 100,
  projectionProbability: 0.5,
  selectionProbability: 0.5,
};

const SettingsGroup = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <div className='space-y-4'>
    <h3 className='text-sm font-semibold text-muted-foreground'>{title}</h3>
    <hr />
    <div className='space-y-4 pl-1'>{children}</div>
  </div>
);

const SliderSetting = ({
  name,
  label,
  min,
  max,
  step,
  settings,
  onSettingChange,
}: {
  name: string;
  label: string;
  min: number;
  max: number;
  step: number;
  settings: Settings;
  onSettingChange: (setting: string, value: number | boolean) => void;
}) => (
  <div className='flex items-center space-x-2'>
    <Label className='w-[200px]'>{label}</Label>
    <div className='flex-1'>
      <Slider
        min={min}
        max={max}
        step={step}
        value={[settings[name as keyof Settings] as number]}
        onValueChange={([value]) => onSettingChange(name, value)}
      />
    </div>
    <span className='w-12 text-right'>{settings[name as keyof Settings]}</span>
  </div>
);

export const SettingsDialog = ({
  settings,
  onSettingChange,
}: {
  settings: Settings;
  onSettingChange: (setting: string, value: number | boolean) => void;
}) => {
  const handleReset = () => {
    Object.entries(DEFAULT_SETTINGS).forEach(([key, value]) => {
      onSettingChange(key, value);
    });
  };

  return (
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
        <div className='grid gap-6 py-4'>
          <SettingsGroup title='General'>
            <div className='flex items-center'>
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
            <div className='flex items-center'>
              <Label className='w-[200px]' htmlFor='enforceNonEmptyResults'>
                Ensure Non-Empty Results
              </Label>
              <Switch
                id='enforceNonEmptyResults'
                checked={settings.enforceNonEmptyResults}
                onCheckedChange={(checked) =>
                  onSettingChange('enforceNonEmptyResults', checked)
                }
              />
            </div>
          </SettingsGroup>
          <SettingsGroup title='Display'>
            <div className='flex items-center'>
              <Label className='w-[200px]' htmlFor='multiLine'>
                Multi-line
              </Label>
              <Switch
                id='multiLine'
                checked={settings.multiLine}
                onCheckedChange={(checked) =>
                  onSettingChange('multiLine', checked)
                }
              />
            </div>
          </SettingsGroup>
          <SettingsGroup title='Operation Probabilities'>
            <SliderSetting
              name='selectionProbability'
              label='Selection'
              min={0}
              max={1}
              step={0.01}
              settings={settings}
              onSettingChange={onSettingChange}
            />
            <SliderSetting
              name='projectionProbability'
              label='Projection'
              min={0}
              max={1}
              step={0.01}
              settings={settings}
              onSettingChange={onSettingChange}
            />
            <SliderSetting
              name='groupbyProbability'
              label='Group By'
              min={0}
              max={1}
              step={0.01}
              settings={settings}
              onSettingChange={onSettingChange}
            />
          </SettingsGroup>
          <SettingsGroup title='Operation Limits'>
            <SliderSetting
              name='maxSelectionConditions'
              label='Max Selection Conditions'
              min={1}
              max={20}
              step={1}
              settings={settings}
              onSettingChange={onSettingChange}
            />
            <SliderSetting
              name='maxProjectionColumns'
              label='Max Projection Columns'
              min={1}
              max={20}
              step={1}
              settings={settings}
              onSettingChange={onSettingChange}
            />
            <SliderSetting
              name='maxMerges'
              label='Max Merges'
              min={1}
              max={20}
              step={1}
              settings={settings}
              onSettingChange={onSettingChange}
            />
            <SliderSetting
              name='maxGroupbyColumns'
              label='Max Group By Columns'
              min={1}
              max={20}
              step={1}
              settings={settings}
              onSettingChange={onSettingChange}
            />
          </SettingsGroup>
        </div>
        <DialogFooter>
          <Button variant='outline' onClick={handleReset} className='gap-2'>
            <RotateCcw className='h-4 w-4' />
            Reset
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
