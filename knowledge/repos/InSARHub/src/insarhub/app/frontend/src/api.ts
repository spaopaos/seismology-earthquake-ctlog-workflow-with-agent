// Shared backend base URL — in dev, Vite's proxy also forwards /api/* to the
// backend, but hitting it directly avoids relying on that proxy being present.
export const API = import.meta.env.DEV ? 'http://localhost:8080' : ''
