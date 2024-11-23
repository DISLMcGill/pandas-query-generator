import { PyodideInterface, loadPyodide } from 'pyodide';

let pyodide: PyodideInterface | undefined;

function makeCloneable(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Map) {
    return Object.fromEntries(obj);
  }

  if (Array.isArray(obj)) {
    return obj.map(makeCloneable);
  }

  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => [key, makeCloneable(value)])
  );
}

const initializePyodide = async () => {
  pyodide = await loadPyodide({
    indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full',
  });

  await pyodide.loadPackage('micropip');
  const micropip = pyodide.pyimport('micropip');
  await micropip.install('pqg');

  self.postMessage({ type: 'initialized' });
};

self.onmessage = async (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'init':
      try {
        await initializePyodide();
      } catch (error) {
        self.postMessage({
          type: 'error',
          payload: error instanceof Error ? error.message : 'Failed to initialize Pyodide',
        });
      }
      break;

    case 'run':
      if (!pyodide) {
        self.postMessage({
          type: 'error',
          payload: 'Pyodide not initialized',
        });
        return;
      }

      try {
        const result = pyodide.runPython(payload.code);
        const cloneableResult = makeCloneable(result.toJs());
        self.postMessage({
          type: 'result',
          payload: cloneableResult,
        });
      } catch (error) {
        self.postMessage({
          type: 'error',
          payload: error instanceof Error ? error.message : 'Failed to execute Python code',
        });
      }
      break;
  }
};

export {};
