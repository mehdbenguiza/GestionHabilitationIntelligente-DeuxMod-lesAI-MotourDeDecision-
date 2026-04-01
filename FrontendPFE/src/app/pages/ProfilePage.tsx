import { useState, useEffect } from 'react';
import { User, Mail, Shield, Calendar, Clock, Lock, Eye, EyeOff, Save, X, History } from 'lucide-react';
import { Badge } from '../components/ui/badge';

interface UserData {
  fullName: string;
  email: string;
  role: string;
  createdAt: string;
  lastLogin: string | null;
  lastLoginIP: string | null;
  lastSessionDuration: string | null;
}

interface EditFormData {
  firstName: string;
  lastName: string;
  email: string;
}

interface PasswordFormData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

interface LoginHistoryEvent {
  id: string;
  action: string;
  date: string;
  ip: string;
  details?: string;
}

export function ProfilePage() {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loginHistory, setLoginHistory] = useState<LoginHistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Modal states
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form states
  const [editForm, setEditForm] = useState<EditFormData>({
    firstName: '',
    lastName: '',
    email: ''
  });

  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const getPasswordStrength = (password: string): { strength: number; label: string; color: string } => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    switch (strength) {
      case 0:
      case 1:
      case 2:
        return { strength: 33, label: 'Faible', color: 'bg-red-500' };
      case 3:
      case 4:
        return { strength: 66, label: 'Moyen', color: 'bg-orange-500' };
      case 5:
        return { strength: 100, label: 'Fort', color: 'bg-green-500' };
      default:
        return { strength: 0, label: '', color: 'bg-gray-300' };
    }
  };

  const passwordStrength = getPasswordStrength(passwordForm.newPassword);

  // Validation functions
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): boolean => {
    return password.length >= 8;
  };

  // Fetch user data and login history
  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError("Vous devez être connecté");
        setLoading(false);
        return;
      }

      try {
        // Fetch user profile
        const profileResponse = await fetch('http://127.0.0.1:8000/users/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!profileResponse.ok) {
          throw new Error("Erreur lors du chargement du profil");
        }

        const profileData = await profileResponse.json();
        
        // Extraire prénom et nom du fullName
        const nameParts = profileData.fullName?.split(' ') || ['', ''];
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';

        setUserData({
          fullName: profileData.fullName || '',
          email: profileData.email || '',
          role: profileData.role === 'SUPER_ADMIN' ? 'Super Admin' : 'Admin',
          createdAt: profileData.createdAt || new Date().toISOString(),
          lastLogin: profileData.lastLogin || null,
          lastLoginIP: profileData.lastLoginIP || null,
          lastSessionDuration: profileData.lastSessionDuration || null
        });

        setEditForm({
          firstName,
          lastName,
          email: profileData.email || ''
        });

        // Fetch login history
        const historyResponse = await fetch('http://127.0.0.1:8000/users/login-history?limit=10', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          setLoginHistory(historyData);
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateEmail(editForm.email)) {
      setError('Email invalide');
      return;
    }

    // Vérifier si l'email a changé
    if (editForm.email !== userData?.email) {
      setError("La modification de l'email n'est pas autorisée");
      return;
    }

    setLoading(true);
    setError('');
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/users/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          firstName: editForm.firstName,
          lastName: editForm.lastName,
          email: editForm.email
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erreur lors de la modification du profil");
      }

      setUserData(prev => prev ? {
        ...prev,
        fullName: `${editForm.firstName} ${editForm.lastName}`,
        email: editForm.email
      } : null);
      
      setSuccessMessage('Profil mis à jour avec succès');
      setShowEditModal(false);
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setPasswordError('');
    setPasswordSuccess('');
    
    // Validations
    if (!validatePassword(passwordForm.newPassword)) {
      setPasswordError('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('Les mots de passe ne correspondent pas');
      return;
    }

    setLoading(true);
    
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/users/change-password', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          oldPassword: passwordForm.oldPassword,
          newPassword: passwordForm.newPassword
        })
      });

      const data = await response.json();

      if (!response.ok) {
        // Gestion spécifique pour l'ancien mot de passe incorrect
        if (response.status === 400 && data.detail === "Ancien mot de passe incorrect") {
          setPasswordError('Ancien mot de passe incorrect');
        } else {
          throw new Error(data.detail || "Erreur lors du changement de mot de passe");
        }
        return;
      }

      setPasswordSuccess('Mot de passe changé avec succès');
      
      // Fermer la modal après 2 secondes
      setTimeout(() => {
        setShowPasswordModal(false);
        setPasswordForm({
          oldPassword: '',
          newPassword: '',
          confirmPassword: ''
        });
        setPasswordError('');
        setPasswordSuccess('');
      }, 2000);
      
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !userData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Chargement du profil...</p>
        </div>
      </div>
    );
  }

  if (error && !userData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p className="text-lg font-semibold mb-2">Erreur</p>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  if (!userData) return null;

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* En-tête */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Mon Profil</h1>
        <p className="text-gray-600">Gérez vos informations personnelles et paramètres de sécurité</p>
      </div>

      {/* Messages de notification */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
          {successMessage}
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonne principale */}
        <div className="lg:col-span-2 space-y-6">
          {/* Informations personnelles */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <User className="text-[#003087]" size={24} />
                Informations Personnelles
              </h2>
              <button
                onClick={() => setShowEditModal(true)}
                className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                Modifier Infos
              </button>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-sm text-gray-600 mb-1">Prénom</div>
                <div className="text-gray-900 font-semibold text-lg">{editForm.firstName}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">Nom</div>
                <div className="text-gray-900 font-semibold text-lg">{editForm.lastName}</div>
              </div>
              <div className="col-span-2">
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                  <Mail size={16} />
                  Email professionnel
                </div>
                <div className="text-gray-900 font-semibold">{userData.email}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                  <Shield size={16} />
                  Rôle
                </div>
                <Badge className="bg-orange-100 text-orange-800 border-orange-300 border px-3 py-1">
                  {userData.role}
                </Badge>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                  <Calendar size={16} />
                  Date de création
                </div>
                <div className="text-gray-900 font-semibold">
                  {new Date(userData.createdAt).toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric'
                  })}
                </div>
              </div>
              <div className="col-span-2">
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                  <Clock size={16} />
                  Dernière connexion
                </div>
                <div className="text-gray-900 font-semibold">
                  {userData.lastLogin
                    ? `${new Date(userData.lastLogin).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: 'long',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })} (IP: ${userData.lastLoginIP || 'Inconnue'})`
                    : 'Aucune connexion récente'}
                </div>
              </div>
              {userData.lastSessionDuration && userData.lastSessionDuration !== "0 min" && (
                <div className="col-span-2">
                  <div className="text-sm text-gray-600 mb-1">Dernière durée de session</div>
                  <div className="text-gray-900 font-semibold">{userData.lastSessionDuration}</div>
                </div>
              )}
            </div>
          </div>

          {/* Sécurité */}
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Lock className="text-[#003087]" size={24} />
                Sécurité
              </h2>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Mot de passe</div>
                    <div className="text-sm text-gray-600">
                      Dernière modification: {loginHistory.find(h => h.action === "Changement de mot de passe") 
                        ? new Date(loginHistory.find(h => h.action === "Changement de mot de passe")!.date).toLocaleDateString('fr-FR')
                        : 'Non disponible'}
                    </div>
                  </div>
                  <button
                    onClick={() => setShowPasswordModal(true)}
                    className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={loading}
                  >
                    Changer Mot de Passe
                  </button>
                </div>
              </div>

              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                    <Shield size={20} className="text-white" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Authentification sécurisée</div>
                    <div className="text-sm text-gray-600">
                      Votre compte est protégé par des mesures de sécurité avancées
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Colonne latérale - Historique */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <History size={20} className="text-[#003087]" />
              Historique d'Activité
            </h3>
            {loginHistory.length > 0 ? (
              <div className="space-y-4 max-h-[500px] overflow-y-auto">
                {loginHistory.map((event) => (
                  <div key={event.id} className="relative pl-6 pb-4 border-l-2 border-gray-200 last:border-0 last:pb-0">
                    <div className="absolute -left-[9px] top-0 w-4 h-4 bg-[#003087] rounded-full border-2 border-white"></div>
                    <div className="text-xs text-gray-600 mb-1">
                      {new Date(event.date).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="font-medium text-gray-900 text-sm mb-1">{event.action}</div>
                    <div className="text-xs text-gray-600">
                      IP: {event.ip}
                      {event.details && ` • ${event.details}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Aucun historique disponible</p>
            )}
          </div>
        </div>
      </div>

      {/* Modal Modifier Infos - Avec fond transparent */}
      {showEditModal && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
          {/* Overlay transparent */}
          <div className="fixed inset-0 bg-transparent"></div>
          
          {/* Modal */}
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl border-2 border-gray-200 relative z-10">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">Modifier les Informations</h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-6 space-y-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-2">
                  Prénom
                </label>
                <input
                  id="firstName"
                  type="text"
                  value={editForm.firstName}
                  onChange={(e) => setEditForm({ ...editForm, firstName: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-2">
                  Nom
                </label>
                <input
                  id="lastName"
                  type="text"
                  value={editForm.lastName}
                  onChange={(e) => setEditForm({ ...editForm, lastName: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-100 border border-gray-200 rounded-lg cursor-not-allowed"
                  disabled
                />
                <p className="text-xs text-gray-500 mt-1">L'email ne peut pas être modifié</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                  disabled={loading}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Save size={18} />
                      Sauvegarder
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Changer Mot de Passe - Avec fond transparent */}
      {showPasswordModal && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
          {/* Overlay transparent */}
          <div className="fixed inset-0 bg-transparent"></div>
          
          {/* Modal */}
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl border-2 border-gray-200 relative z-10">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">Changer le Mot de Passe</h3>
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  setPasswordForm({
                    oldPassword: '',
                    newPassword: '',
                    confirmPassword: ''
                  });
                  setPasswordError('');
                  setPasswordSuccess('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handlePasswordSubmit} className="p-6 space-y-4">
              {/* Messages d'erreur/succès dans la modal */}
              {passwordError && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                  {passwordError}
                </div>
              )}
              
              {passwordSuccess && (
                <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg text-sm">
                  {passwordSuccess}
                </div>
              )}

              <div>
                <label htmlFor="oldPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Ancien mot de passe
                </label>
                <div className="relative">
                  <input
                    id="oldPassword"
                    type={showOldPassword ? 'text' : 'password'}
                    value={passwordForm.oldPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, oldPassword: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowOldPassword(!showOldPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showOldPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
              
              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Nouveau mot de passe
                </label>
                <div className="relative">
                  <input
                    id="newPassword"
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordForm.newPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    required
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showNewPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {passwordForm.newPassword && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600">Force du mot de passe:</span>
                      <span className={`text-xs font-semibold ${passwordStrength.color.replace('bg-', 'text-')}`}>
                        {passwordStrength.label}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${passwordStrength.color} transition-all`}
                        style={{ width: `${passwordStrength.strength}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Minimum 8 caractères, avec majuscules, minuscules, chiffres et caractères spéciaux
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Confirmer le mot de passe
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={passwordForm.confirmPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">Les mots de passe ne correspondent pas</p>
                )}
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordForm({
                      oldPassword: '',
                      newPassword: '',
                      confirmPassword: ''
                    });
                    setPasswordError('');
                    setPasswordSuccess('');
                  }}
                  className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                  disabled={loading}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading || passwordForm.newPassword !== passwordForm.confirmPassword || !passwordForm.newPassword}
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mx-auto"></div>
                  ) : (
                    'Changer'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}