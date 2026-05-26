import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Default handlers — tests override per-suite with server.use(...)
const handlers = [
  http.all('http://localhost:8000/api/v1/*', () => {
    return HttpResponse.json({ error: 'no handler registered for this path' }, { status: 500 });
  }),
];

export const server = setupServer(...handlers);
export { http, HttpResponse };
