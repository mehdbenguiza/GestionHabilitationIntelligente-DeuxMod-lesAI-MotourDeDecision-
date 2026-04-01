import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, UserPlus, Shield, Clock, Mail, Eye, EyeOff, Edit, AlertCircle, RefreshCw } from 'lucide-react';
import { Badge } from '../components/ui/badge';

interface Admin {
  id: number;
  username: string;
  fullName: string;
  email: string;
  role: 'ADMIN' | 'SUPER_ADMIN';
  isActive: boolean;
  lastLogin: string | null;
  createdAt: string;
}

export function AdminsPage() {
  const navigate = useNavigate();
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState<Admin | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ admin: Admin; action: 'activate' | 'deactivate' } | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    fullName: '',
    email: '',
    role: 'ADMIN' as 'ADMIN' | 'SUPER_ADMIN',
    password: ''
  });

  const token = localStorage.getItem('token');

  // Récupérer la liste des admins
  const fetchAdmins = async () => {
    if (!token) {
      setError('Non authentifié');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/users/admins', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Accès non autorisé. Seul le Super Admin peut gérer les admins.');
        }
        throw new Error('Erreur lors du chargement');
      }

      const data = await response.json();
      setAdmins(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  // Créer un nouvel admin
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/register', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: formData.username,
          fullName: formData.fullName,
          email: formData.email,
          role: formData.role,
          password: formData.password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erreur lors de la création');
      }

      setShowAddModal(false);
      setFormData({ username: '', fullName: '', email: '', role: 'ADMIN', password: '' });
      fetchAdmins(); // Recharger la liste
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    }
  };

  // Modifier un admin
  const handleEdit = (admin: Admin) => {
    setSelectedAdmin(admin);
    setFormData({
      username: admin.username,
      fullName: admin.fullName,
      email: admin.email,
      role: admin.role,
      password: ''
    });
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`http://127.0.0.1:8000/users/admins/${selectedAdmin?.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          fullName: formData.fullName,
          email: formData.email,
          role: formData.role
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Erreur lors de la modification');
      }

      setShowEditModal(false);
      setSelectedAdmin(null);
      fetchAdmins();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    }
  };

  // Activer/Désactiver un admin
  const handleStatusToggle = (admin: Admin) => {
    const action = admin.isActive ? 'deactivate' : 'activate';
    setConfirmAction({ admin, action });
    setShowConfirmModal(true);
  };

  const confirmStatusToggle = async () => {
    if (!confirmAction) return;

    try {
      const response = await fetch(`http://127.0.0.1:8000/users/admins/${confirmAction.admin.id}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          isActive: confirmAction.action === 'activate'
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Erreur lors du changement de statut');
      }

      setShowConfirmModal(false);
      setConfirmAction(null);
      fetchAdmins();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setShowConfirmModal(false);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    return role === 'SUPER_ADMIN'
      ? 'bg-orange-100 text-orange-800 border-orange-300'
      : 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const getRoleLabel = (role: string) => {
    return role === 'SUPER_ADMIN' ? 'Super Admin' : 'Admin';
  };

  if (loading && admins.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des administrateurs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Gestion des Admins</h1>
          <p className="text-[#64748B]">Configuration des utilisateurs administrateurs (Super Admin uniquement)</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchAdmins}
            className="flex items-center gap-2 px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg hover:bg-[#E2E8F0] transition-colors"
          >
            <RefreshCw size={20} />
            Actualiser
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors shadow-lg"
          >
            <UserPlus size={20} />
            Ajouter un Admin
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <Users size={24} className="text-[#003087]" />
            </div>
          </div>
          <div className="text-3xl font-bold text-[#1E2937] mb-1">{admins.length}</div>
          <div className="text-sm text-[#64748B]">Total Admins</div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <Shield size={24} className="text-[#10B981]" />
            </div>
          </div>
          <div className="text-3xl font-bold text-[#1E2937] mb-1">
            {admins.filter(a => a.isActive).length}
          </div>
          <div className="text-sm text-[#64748B]">Admins Actifs</div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
              <Shield size={24} className="text-[#F59E0B]" />
            </div>
          </div>
          <div className="text-3xl font-bold text-[#1E2937] mb-1">
            {admins.filter(a => a.role === 'SUPER_ADMIN').length}
          </div>
          <div className="text-sm text-[#64748B]">Super Admins</div>
        </div>
      </div>

      {/* Liste des admins */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[#E2E8F0]">
          <div className="flex items-center gap-2">
            <Users className="text-[#003087]" size={24} />
            <h2 className="text-xl font-bold text-[#1E2937]">Liste des Administrateurs</h2>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F8FAFC]">
              <tr className="border-b border-[#E2E8F0]">
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Nom</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Email</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Rôle</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Statut</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Dernière Connexion</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Actions</th>
               </tr>
            </thead>
            <tbody>
              {admins.map((admin) => (
                <tr key={admin.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#003087] rounded-full flex items-center justify-center text-white font-semibold">
                        {admin.fullName.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </div>
                      <span className="font-semibold text-[#1E2937]">{admin.fullName}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-[#64748B] flex items-center gap-2">
                    <Mail size={16} />
                    {admin.email}
                  </td>
                  <td className="py-4 px-6">
                    <Badge className={getRoleBadgeColor(admin.role)}>
                      <Shield size={14} className="mr-1" />
                      {getRoleLabel(admin.role)}
                    </Badge>
                  </td>
                  <td className="py-4 px-6">
                    {admin.isActive ? (
                      <Badge className="bg-green-100 text-green-800 border-green-300 border">
                        Actif
                      </Badge>
                    ) : (
                      <Badge className="bg-gray-100 text-gray-800 border-gray-300 border">
                        Inactif
                      </Badge>
                    )}
                  </td>
                  <td className="py-4 px-6 text-[#64748B] text-sm flex items-center gap-2">
                    <Clock size={16} />
                    {admin.lastLogin
                      ? new Date(admin.lastLogin).toLocaleDateString('fr-FR', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : 'Jamais connecté'}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleEdit(admin)}
                        className="p-2 text-[#003087] hover:bg-blue-50 rounded-lg transition-colors"
                        title="Modifier"
                      >
                        <Edit size={18} />
                      </button>
                      {admin.isActive ? (
                        <button 
                          onClick={() => handleStatusToggle(admin)}
                          className="px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors"
                        >
                          Désactiver
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleStatusToggle(admin)}
                          className="px-3 py-1.5 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors"
                        >
                          Activer
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {admins.length === 0 && !loading && (
          <div className="text-center py-12 text-[#64748B]">
            Aucun administrateur trouvé
          </div>
        )}
      </div>

      {/* Modal d'ajout */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full shadow-2xl">
            <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserPlus className="text-[#003087]" size={24} />
                <h3 className="text-xl font-bold text-[#1E2937]">Ajouter un Administrateur</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors text-[#64748B]"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#1E2937] mb-2">Nom d'utilisateur</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                    placeholder="Nom d'utilisateur"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#1E2937] mb-2">Nom complet</label>
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                    placeholder="Prénom Nom"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  placeholder="prenom.nom@biat.com.tn"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Rôle</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'ADMIN' | 'SUPER_ADMIN' })}
                  className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                >
                  <option value="ADMIN">Admin</option>
                  <option value="SUPER_ADMIN">Super Admin</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Mot de passe</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    placeholder="Mot de passe"
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
                <p className="text-xs text-[#64748B] mt-1">
                  L'utilisateur devra changer ce mot de passe à sa première connexion
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors"
                >
                  Ajouter
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de modification */}
      {showEditModal && selectedAdmin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full shadow-2xl">
            <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Edit className="text-[#003087]" size={24} />
                <h3 className="text-xl font-bold text-[#1E2937]">Modifier l'Administrateur</h3>
              </div>
              <button
                onClick={() => { setShowEditModal(false); setSelectedAdmin(null); }}
                className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors text-[#64748B]"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Nom d'utilisateur</label>
                <input
                  type="text"
                  value={formData.username}
                  disabled
                  className="w-full px-4 py-2.5 bg-gray-100 border border-[#E2E8F0] rounded-lg cursor-not-allowed"
                />
                <p className="text-xs text-[#64748B] mt-1">Le nom d'utilisateur ne peut pas être modifié</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Nom complet</label>
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-2">Rôle</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'ADMIN' | 'SUPER_ADMIN' })}
                  className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                >
                  <option value="ADMIN">Admin</option>
                  <option value="SUPER_ADMIN">Super Admin</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setSelectedAdmin(null); }}
                  className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors"
                >
                  Sauvegarder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de confirmation */}
      {showConfirmModal && confirmAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl">
            <div className="p-6">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle size={24} className="text-[#F59E0B]" />
              </div>
              <h3 className="text-xl font-bold text-[#1E2937] text-center mb-2">Êtes-vous sûr ?</h3>
              <p className="text-[#64748B] text-center mb-6">
                Voulez-vous vraiment {confirmAction.action === 'activate' ? 'activer' : 'désactiver'} l'administrateur <strong>{confirmAction.admin.fullName}</strong> ?
                {confirmAction.action === 'deactivate' && (
                  <span className="block mt-2 text-red-600 text-sm">
                    ⚠️ L'utilisateur ne pourra plus se connecter.
                  </span>
                )}
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowConfirmModal(false); setConfirmAction(null); }}
                  className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={confirmStatusToggle}
                  className={`flex-1 py-2.5 text-white rounded-lg font-semibold transition-colors ${
                    confirmAction.action === 'activate' 
                      ? 'bg-[#10B981] hover:bg-[#059669]' 
                      : 'bg-[#EF4444] hover:bg-[#DC2626]'
                  }`}
                >
                  Confirmer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}