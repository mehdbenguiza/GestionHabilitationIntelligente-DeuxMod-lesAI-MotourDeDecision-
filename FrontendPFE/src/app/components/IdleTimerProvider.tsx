import React, { ReactNode } from 'react';
import { useIdleTimer } from '../../hooks/useIdleTimer';
import { useAuth } from '../contexts/AuthContext';
import { IdleWarningModal } from './IdleWarningModal';

interface IdleTimerProviderProps {
  children: ReactNode;
  timeout?: number; // en millisecondes
}

export const IdleTimerProvider: React.FC<IdleTimerProviderProps> = ({ 
  children, 
  timeout = 30000 // 30 secondes
}) => {
  const { logout } = useAuth();
  
  const { showWarning, timeLeft, resetTimer } = useIdleTimer({
    timeout,
    onIdle: logout
  });

  return (
    <>
      <IdleWarningModal
        isOpen={showWarning}
        timeLeft={timeLeft}
        onStay={resetTimer}
        onLogout={logout}
      />
      {children}
    </>
  );
};