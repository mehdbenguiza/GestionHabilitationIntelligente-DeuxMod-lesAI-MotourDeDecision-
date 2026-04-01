import { redirect } from 'react-router-dom';

export async function requireSuperAdminLoader() {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return redirect('/login');
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      localStorage.removeItem('token');
      return redirect('/login');
    }

    const userData = await response.json();
    
    // Vérifier si l'utilisateur est SUPER_ADMIN
    if (userData.role !== 'SUPER_ADMIN') {
      // Rediriger vers le dashboard si ce n'est pas un super admin
      return redirect('/dashboard');
    }

    // Retourner les données utilisateur pour les utiliser dans le composant
    return { user: userData, isSuperAdmin: true };
  } catch (error) {
    console.error('Erreur de vérification:', error);
    return redirect('/login');
  }
}

// Loader pour vérifier simplement l'authentification (pour les routes protégées normales)
export async function requireAuthLoader() {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return redirect('/login');
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      localStorage.removeItem('token');
      return redirect('/login');
    }

    const userData = await response.json();
    return { user: userData };
  } catch (error) {
    console.error('Erreur de vérification:', error);
    return redirect('/login');
  }
}