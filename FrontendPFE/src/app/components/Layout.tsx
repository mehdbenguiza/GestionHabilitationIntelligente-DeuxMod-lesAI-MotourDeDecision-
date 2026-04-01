import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { useSidebar } from '../contexts/SidebarContext';
import { useIdleTimer } from '../../hooks/useIdleTimer';
import { IdleWarningModal } from '../components/IdleWarningModal';

export function Layout() {
  const { isCollapsed } = useSidebar();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('http://127.0.0.1:8000/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      localStorage.removeItem('token');
      navigate('/login');
    }
  };

  const { showWarning, timeLeft, resetTimer } = useIdleTimer({
    timeout: 30000, // 30 secondes
    onIdle: handleLogout
  });

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <Topbar />
      
      <IdleWarningModal
        isOpen={showWarning}
        timeLeft={timeLeft}
        onStay={resetTimer}
        onLogout={handleLogout}
      />
      
      <main className={`${isCollapsed ? 'ml-[60px]' : 'ml-[280px]'} mt-16 p-8 transition-all duration-300`}>
        <Outlet />
      </main>
    </div>
  );
}