import { useEffect, useRef, useState } from 'react';

import { useToast } from './use-toast';

type WorkerStatus = 'idle' | 'loading' | 'ready' | 'error';

type WorkerResponse =
  | { type: 'status'; payload: WorkerStatus }
  | { type: 'error'; payload: string }
  | { type: 'result'; payload: string };

export const usePyodideWorker = () => {
  const [status, setStatus] = useState<WorkerStatus>('idle');

  const workerRef = useRef<Worker>();

  const { toast } = useToast();

  useEffect(() => {
    workerRef.current = new Worker(
      new URL('../workers/pyodide.worker.ts', import.meta.url),
      {
        type: 'module',
      }
    );

    workerRef.current.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const { type, payload } = event.data;

      switch (type) {
        case 'status':
          setStatus(payload);
          break;
        case 'error':
          toast({
            variant: 'destructive',
            title: 'Error',
            description: payload,
          });
          setStatus('error');
          break;
      }
    };

    workerRef.current.postMessage({ type: 'init' });

    return () => {
      workerRef.current?.terminate();
    };
  }, [toast]);

  const runPython = async <T>(code: string): Promise<T> => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current || status !== 'ready') {
        reject(new Error('Worker not ready'));
        return;
      }

      const handler = (event: MessageEvent<WorkerResponse>) => {
        const { type, payload } = event.data;

        if (type === 'result') {
          workerRef.current?.removeEventListener('message', handler);
          resolve(JSON.parse(payload) as T);
        } else if (type === 'error') {
          workerRef.current?.removeEventListener('message', handler);
          reject(new Error(payload));
        }
      };

      workerRef.current.addEventListener('message', handler);
      workerRef.current.postMessage({ type: 'run', payload: { code } });
    });
  };

  return {
    error: status === 'error',
    loading: status === 'loading',
    ready: status === 'ready',
    runPython,
  };
};
