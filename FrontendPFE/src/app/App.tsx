import { RouterProvider } from 'react-router';
import { router } from './routes';
import { SidebarProvider } from './contexts/SidebarContext';

export default function App() {
  return (
    <SidebarProvider>
      <RouterProvider router={router} />
    </SidebarProvider>
  );
}