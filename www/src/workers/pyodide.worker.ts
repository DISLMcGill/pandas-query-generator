import { PyodideInterface, loadPyodide } from 'pyodide';

let pyodide: PyodideInterface;

type WorkerMessage =
  | { type: 'init' }
  | { type: 'run'; payload: { code: string } };

type WorkerResponse =
  | { type: 'status'; payload: 'loading' | 'ready' }
  | { type: 'error'; payload: string }
  | { type: 'result'; payload: string };

self.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const { type } = event.data;

  try {
    switch (type) {
      case 'init':
        if (!pyodide) {
          self.postMessage({
            type: 'status',
            payload: 'loading',
          } satisfies WorkerResponse);

          pyodide = await loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full',
          });

          await pyodide.loadPackage('micropip');

          const micropip = pyodide.pyimport('micropip');
          await micropip.install('pqg');

          self.postMessage({
            type: 'status',
            payload: 'ready',
          } satisfies WorkerResponse);
        }
        break;
      case 'run':
        if (!pyodide) throw new Error('Pyodide not initialized');

        self.postMessage({
          type: 'result',
          payload: pyodide.runPython(event.data.payload.code),
        } satisfies WorkerResponse);

        break;
      default:
        throw new Error(`Unknown message type: ${type satisfies never}`);
    }
  } catch (error) {
    self.postMessage({
      type: 'error',
      payload: error instanceof Error ? error.message : 'Unknown error',
    } satisfies WorkerResponse);
  }
};
