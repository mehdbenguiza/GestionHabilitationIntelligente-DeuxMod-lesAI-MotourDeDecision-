import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { BiatLogo } from '../components/BiatLogo';

export function LoginPage() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    remember: false
  });

  // Au chargement, vérifier s'il y a une session persistante
  useEffect(() => {
    const checkPersistentSession = async () => {
      const hasPersistentSession = localStorage.getItem('persistent_session') === 'true';
      if (hasPersistentSession) {
        try {
          const response = await fetch('http://127.0.0.1:8000/auth/refresh', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            navigate('/dashboard');
          } else {
            // Session expirée, nettoyer
            localStorage.removeItem('persistent_session');
            localStorage.removeItem('saved_username');
          }
        } catch (err) {
          console.error('Erreur de refresh:', err);
        }
      }
    };
    
    checkPersistentSession();
    
    // Pré-remplir le username si sauvegardé
    const savedUsername = localStorage.getItem('saved_username');
    if (savedUsername) {
      setFormData(prev => ({ ...prev, username: savedUsername }));
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Identifiants incorrects');
      }

      localStorage.setItem('token', data.access_token);
      
      // Gestion du "Se souvenir de moi"
      if (formData.remember) {
        localStorage.setItem('persistent_session', 'true');
        localStorage.setItem('saved_username', formData.username);
      } else {
        localStorage.removeItem('persistent_session');
        localStorage.removeItem('saved_username');
      }

      navigate('/dashboard');

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#003087] via-[#004099] to-[#00AEEF] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-2xl p-8">
          <div className="flex justify-center mb-8">
            <BiatLogo size="large" showText={true} />
          </div>

          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-[#1E2937] mb-2">
              Connexion au Dashboard
            </h1>
            <p className="text-sm text-[#64748B]">
              Espace réservé aux Admins et Super Admin
            </p>
          </div>

          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-[#1E2937] mb-2">
                Nom d'utilisateur
              </label>
              <input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                placeholder="Votre nom d'utilisateur"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#1E2937] mb-2">
                Mot de passe
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                  placeholder="Votre mot de passe"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#003087]"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.remember}
                  onChange={(e) => setFormData({ ...formData, remember: e.target.checked })}
                  className="w-4 h-4 text-[#003087] border-[#E2E8F0] rounded focus:ring-[#003087]"
                />
                <span className="text-sm text-[#64748B]">Se souvenir de moi</span>
              </label>

              <button
                type="button"
                onClick={() => navigate('/forgot-password')}
                className="text-sm text-[#003087] hover:text-[#00AEEF] font-medium bg-transparent border-none cursor-pointer"
              >
                Mot de passe oublié ?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors shadow-lg hover:shadow-xl disabled:opacity-70"
            >
              {loading ? 'Connexion en cours...' : 'Se connecter'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-white mt-6 opacity-90">
          © BIAT 2026 - Tous droits réservés
        </p>
      </div>
    </div>
  );
}