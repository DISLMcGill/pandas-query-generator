import { loadPyodide, PyodideInterface } from "pyodide"
import { useEffect, useState } from "react"

const App = () => {
  const [client, setClient] = useState<PyodideInterface | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);

    loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.3/full',
    }).then(async (pyodide: PyodideInterface) => {
      try {
        await pyodide.loadPackage("pqg");
        setClient(pyodide);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load Python client");
      } finally {
        setLoading(false);
      }
    });
  }, []);

  return (
    <p className='m-2'>{loading ? 'Loading python...' : 'Loaded!'}</p>
  )
}

export default App
