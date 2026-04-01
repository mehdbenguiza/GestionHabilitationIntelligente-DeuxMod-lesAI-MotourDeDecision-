// src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './app/routes';
import { SidebarProvider } from './app/contexts/SidebarContext'; // 👈 AJOUTE ÇA
import './styles/index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SidebarProvider>   {/* 👈 ENVELOPPE ICI */}
      <RouterProvider router={router} />
    </SidebarProvider>
  </StrictMode>
);