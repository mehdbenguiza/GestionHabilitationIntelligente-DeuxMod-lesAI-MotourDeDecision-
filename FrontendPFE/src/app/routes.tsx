// src/app/router.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import React from "react";

import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { DashboardPage } from './pages/DashboardPage';
import { TicketsPage } from './pages/TicketsPage';
import { TicketDetailPage } from './pages/TicketDetailPage';
import { SupervisionPage } from './pages/SupervisionPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { AdminsPage } from './pages/AdminsPage';
import { ProfilePage } from './pages/ProfilePage';
import { AILabPage } from './pages/AILabPage';
import { HabilitationsPage } from './pages/HabilitationsPage';

// Importer les loaders
import { requireAuthLoader, requireSuperAdminLoader } from '../utils/authLoaders';

export const router = createBrowserRouter([
  
  // Redirection racine vers login
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },

  // Page login (publique)
  {
    path: '/login',
    element: <LoginPage />,
  },

  // Page mot de passe oublié (publique)
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },

  // Dashboard avec Layout (routes protégées)
  {
    path: '/',
    element: <Layout />,
    loader: requireAuthLoader, // Vérifie l'authentification pour toutes les routes enfants
    children: [
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'tickets',
        element: <TicketsPage />,
      },
      {
        path: 'ticket/:id',
        element: <TicketDetailPage />,
      },
      {
        path: 'supervision',
        element: <SupervisionPage />,
      },
      {
        path: 'audit-logs',
        element: <AuditLogsPage />,
      },
      {
        path: 'admins',
        element: <AdminsPage />,
        loader: requireSuperAdminLoader, // Surcharge le loader pour vérifier le rôle Super Admin
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'habilitations',
        element: <HabilitationsPage />,
      },
      {
        path: 'ai-lab',
        element: <AILabPage />,
        loader: requireSuperAdminLoader,
      },
    ],
  },
]);