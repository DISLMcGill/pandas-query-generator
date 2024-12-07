import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const calculateMeanStd = (values: number[]) => {
  if (values.length === 0) {
    return { mean: 0, std: 0, max: 0 };
  }

  const mean = values.reduce((a, b) => a + b) / values.length;

  const variance =
    values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (values.length - 1);

  return {
    max: Math.max(...values),
    mean,
    std: values.length > 1 ? Math.sqrt(variance) : 0,
  };
};

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
