import { PyodideInterface, loadPyodide } from 'pyodide';
import { useEffect, useState } from 'react';

import { useToast } from './use-toast';

export const usePyodideClient = () => {
  const [client, setClient] = useState<PyodideInterface>();
  const [loading, setLoading] = useState(false);

  const { toast } = useToast();

  useEffect(() => {
    setLoading(true);
    loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full',
    }).then(async (pyodide: PyodideInterface) => {
      try {
        await pyodide.loadPackage('micropip');
        const micropip = pyodide.pyimport('micropip');
        await micropip.install('pqg');
        setClient(pyodide);
      } catch (err) {
        toast({
          variant: 'destructive',
          title: 'Error',
          description:
            err instanceof Error ? err.message : 'Failed to load Python client',
        });
      } finally {
        setLoading(false);
      }
    });
  }, [toast]);

  return { client, loading };
};
