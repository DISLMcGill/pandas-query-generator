import { useEffect, useRef, useState } from 'react';

import { useToast } from './use-toast';

export const usePyodideClient = () => {
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  const workerRef = useRef<Worker>();

  const { toast } = useToast();

  useEffect(() => {
    workerRef.current = new Worker(
      new URL('../workers/python.worker.ts', import.meta.url),
      { type: 'module' }
    );

    workerRef.current.onmessage = (event) => {
      const { type, payload } = event.data;

      switch (type) {
        case 'initialized':
          setInitialized(true);
          setLoading(false);
          break;
        case 'error':
          toast({
            variant: 'destructive',
            title: 'Error',
            description: payload,
          });
          setLoading(false);
          break;
      }
    };

    workerRef.current.postMessage({ type: 'init' });

    return () => {
      workerRef.current?.terminate();
    };
  }, [toast]);

  const runPython = async <T = unknown>(code: string): Promise<T> => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current || !initialized) {
        reject(new Error('Python environment not initialized'));
        return;
      }

      const handler = (event: MessageEvent) => {
        const { type, payload } = event.data;

        if (type === 'result') {
          workerRef.current?.removeEventListener('message', handler);
          resolve(payload as T);
        } else if (type === 'error') {
          workerRef.current?.removeEventListener('message', handler);
          reject(new Error(payload));
        }
      };

      workerRef.current.addEventListener('message', handler);
      workerRef.current.postMessage({ type: 'run', payload: { code } });
    });
  };

  return { loading, runPython };
};
