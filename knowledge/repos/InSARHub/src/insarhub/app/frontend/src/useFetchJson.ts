import { useEffect, useState } from 'react'

// Fetch-on-mount/dep-change JSON GET with loading/error state — for the common
// case of a single GET whose JSON body is either the data or a `{ detail }` error.
export function useFetchJson<T = any>(url: string, deps: any[]) {
  const [data,    setData]    = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    fetch(url)
      .then(r => r.json())
      .then(d => {
        if (d?.detail) { setError(d.detail); setLoading(false); return }
        setData(d)
        setLoading(false)
      })
      .catch(e => { setError(String(e)); setLoading(false) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error }
}
