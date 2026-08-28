type Listener = (isLoading: boolean) => void;

let activeRequests = 0;
const listeners = new Set<Listener>();

export function beginRequest(): void {
  activeRequests += 1;
  if (activeRequests === 1) {
    listeners.forEach((listener) => listener(true));
  }
}

export function endRequest(): void {
  activeRequests = Math.max(0, activeRequests - 1);
  if (activeRequests === 0) {
    listeners.forEach((listener) => listener(false));
  }
}

export function subscribeToLoading(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
