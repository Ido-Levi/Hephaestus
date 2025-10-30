import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { WebSocketProvider } from '@/context/WebSocketContext';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import Overview from '@/pages/Overview';
import Tasks from '@/pages/Tasks';
import Agents from '@/pages/Agents';
import Phases from '@/pages/Phases';
import Memories from '@/pages/Memories';
import Graph from '@/pages/Graph';
import Observability from '@/pages/Observability';
import Results from '@/pages/Results';
import Tickets from '@/pages/Tickets';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="overview" element={<Overview />} />
              <Route path="tasks" element={<Tasks />} />
              <Route path="agents" element={<Agents />} />
              <Route path="phases" element={<Phases />} />
              <Route path="memories" element={<Memories />} />
              <Route path="graph" element={<Graph />} />
              <Route path="observability" element={<Observability />} />
              <Route path="results" element={<Results />} />
              <Route path="tickets" element={<Tickets />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#333',
              color: '#fff',
            },
          }}
        />
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export default App;
