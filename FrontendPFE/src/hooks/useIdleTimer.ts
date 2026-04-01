import { useState, useEffect, useRef, useCallback } from 'react';

interface UseIdleTimerProps {
  timeout?: number; // en millisecondes
  warningTime?: number; // en millisecondes
  onIdle?: () => void;
  events?: string[];
}

export const useIdleTimer = ({
  timeout = 10000,
  warningTime = 5000,
  onIdle,
  events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
}: UseIdleTimerProps = {}) => {
  const [lastActivity, setLastActivity] = useState<number>(Date.now());
  const [showWarning, setShowWarning] = useState<boolean>(false);
  
  const timeoutRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const resetTimer = useCallback(() => {
    setLastActivity(Date.now());
    setShowWarning(false);
  }, []);

  const handleActivity = useCallback(() => {
    resetTimer();
  }, [resetTimer]);

  useEffect(() => {
    // Ajouter les écouteurs
    events.forEach(event => {
      window.addEventListener(event, handleActivity);
    });

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [events, handleActivity]);

  useEffect(() => {
    const checkIdle = () => {
      const now = Date.now();
      const timeSinceLastActivity = now - lastActivity;

      if (timeSinceLastActivity >= timeout - warningTime && 
          timeSinceLastActivity < timeout && 
          !showWarning) {
        setShowWarning(true);
      }

      if (timeSinceLastActivity >= timeout && onIdle) {
        onIdle();
      }
    };

    timeoutRef.current = setInterval(checkIdle, 1000);

    return () => {
      if (timeoutRef.current) {
        clearInterval(timeoutRef.current);
      }
    };
  }, [lastActivity, timeout, warningTime, onIdle, showWarning]);

  const timeLeft = Math.max(0, Math.ceil((timeout - (Date.now() - lastActivity)) / 1000));

  return {
    lastActivity,
    showWarning,
    timeLeft,
    resetTimer
  };
};