import { ReactNode, useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

interface SuperAdminRouteProps {
  children: ReactNode;
}

export const SuperAdminRoute = ({ children }: SuperAdminRouteProps) => {
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthorization = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setIsAuthorized(false);
        setLoading(false);
        return;
      }

      try {
        const response = await fetch('http://127.0.0.1:8000/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const userData = await response.json();
          // Vérifier si le rôle est SUPER_ADMIN
          setIsAuthorized(userData.role === 'SUPER_ADMIN');
        } else {
          setIsAuthorized(false);
        }
      } catch (error) {
        console.error('Erreur de vérification:', error);
        setIsAuthorized(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuthorization();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Vérification des autorisations...</p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    // Rediriger vers le dashboard ou page d'accueil avec un message
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};