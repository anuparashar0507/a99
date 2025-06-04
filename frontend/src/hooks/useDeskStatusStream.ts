// Example React Hook for SSE
import { useState, useEffect, useRef } from 'react';

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export function useDeskStatusStream(deskId) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!deskId) {
        setStatus(null);
        setError(null);
        return;
    }

    // Assuming your API base URL and auth (e.g., token) are handled
    const url = `${BASE_URL}/sse/${deskId}/stream`; // Adjust path to your API endpoint

    console.log(`Connecting to SSE: ${url}`);
    // Use { withCredentials: true } if your auth relies on cookies
    const es = new EventSource(url, /* { withCredentials: true } */);
    eventSourceRef.current = es;

    es.onopen = () => {
      console.log(`SSE connection opened for desk ${deskId}`);
      setError(null);
    };

    es.addEventListener('status_update', (event) => {
      console.log('SSE status_update received:', event.data);
      try {
        const newStatus = JSON.parse(event.data);
        setStatus(newStatus);
      } catch (e) {
        console.error('Failed to parse SSE status data:', e);
        setError('Received invalid status data from server.');
      }
    });

     es.addEventListener('error', (event) => {
       // EventSource errors are often generic; inspect event for details if possible
       console.error('SSE connection error:', event);
       // Don't close automatically on generic error unless type indicates connection closed
       if (event.eventPhase === EventSource.CLOSED) {
          console.log(`SSE connection closed for desk ${deskId}`);
          setError('Connection closed by server or network error.');
          setStatus(prev => prev ? { ...prev, phase: 'not_running', status_text: 'error', message: 'Connection lost' } : null); // Update UI status
       } else {
           setError('An error occurred with the status stream.');
       }
        // Optionally attempt to reconnect or close based on error type
       es.close(); // Close on error for this example
       eventSourceRef.current = null;
     });

    // Cleanup function to close connection when component unmounts or deskId changes
    return () => {
      if (eventSourceRef.current) {
        console.log(`Closing SSE connection for desk ${deskId}`);
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [deskId]); // Reconnect if deskId changes

  return { status, error };
}

