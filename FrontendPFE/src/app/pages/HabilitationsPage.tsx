import { useState, useEffect } from 'react';
import { 
  Key, ShieldCheck, ShieldAlert, Lock, User, 
  Search, Filter, X, CheckCircle, AlertTriangle, 
  RefreshCw, FileText, Server, Clock, Trash2, Ban
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/badge';

interface Profile {
  id: number;
  ticket_id: number;
  ticket_ref: string;
  employee_id: string;
  employee_name: string;
  employee_email: string;
  system_name: string;
  account_name: string;
  application: string;
  environments: string[];
  access_types: string[];
  status: 'ACTIVE' | 'REVOKED' | 'EXPIRED';
  created_at: string;
  revoked_at?: string;
  revoked_reason?: string;
  notification_sent: boolean;
}

export function HabilitationsPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  // Révocation modal
  const [showRevokeModal, setShowRevokeModal] = useState(false);
  const [profileToRevoke, setProfileToRevoke] = useState<Profile | null>(null);
  const [revokeReason, setRevokeReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  const token = localStorage.getItem('token');

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      let url = 'http://127.0.0.1:8000/profiles?limit=500';
      if (filterStatus !== 'ALL') {
        url += `&status=${filterStatus}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Erreur lors du chargement des habilitations');
      const data = await response.json();
      setProfiles(data.profiles || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, [filterStatus]);

  const handleRevoke = async () => {
    if (!profileToRevoke || !revokeReason.trim()) return;
    setActionLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/profiles/${profileToRevoke.id}/revoke?reason=${encodeURIComponent(revokeReason)}`, 
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la révocation');
      }
      
      // Update local state
      setShowRevokeModal(false);
      setProfileToRevoke(null);
      setRevokeReason('');
      fetchProfiles(); // Rafraîchir
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const toggleStatus = async (p: Profile) => {
    if (p.status === 'ACTIVE') {
      setProfileToRevoke(p);
      setShowRevokeModal(true);
    } else if (p.status === 'REVOKED') {
      if (!confirm(`Voulez-vous réactiver le compte ${p.account_name} ?`)) return;
      setActionLoading(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/profiles/${p.id}/reactivate`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) fetchProfiles();
        else alert('Erreur lors de la réactivation');
      } catch (e) {
        console.error(e);
      } finally {
        setActionLoading(false);
      }
    }
  };

  const getStatusBadge = (p: Profile) => {
    const status = p.status;
    let badge;
    switch (status) {
      case 'ACTIVE': badge = <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 font-bold hover:bg-red-100 hover:text-red-800 hover:border-red-300 transition-colors cursor-pointer" onClick={() => toggleStatus(p)} title="Cliquer pour révoquer"><CheckCircle size={12} className="mr-1" /> Actif</Badge>; break;
      case 'REVOKED': badge = <Badge className="bg-red-100 text-red-800 border-red-300 font-bold hover:bg-emerald-100 hover:text-emerald-800 hover:border-emerald-300 transition-colors cursor-pointer" onClick={() => toggleStatus(p)} title="Cliquer pour réactiver"><Ban size={12} className="mr-1" /> Révoqué</Badge>; break;
      case 'EXPIRED': badge = <Badge className="bg-orange-100 text-orange-800 border-orange-300 font-bold"><Clock size={12} className="mr-1" /> Expiré</Badge>; break;
      default: badge = <Badge className="bg-gray-100 text-gray-800 border-gray-300">{status}</Badge>;
    }
    return badge;
  };

  const filteredProfiles = profiles.filter(p => {
    if (!searchTerm) return true;
    const lower = searchTerm.toLowerCase();
    return p.employee_name?.toLowerCase().includes(lower) 
        || p.account_name.toLowerCase().includes(lower)
        || p.system_name?.toLowerCase().includes(lower)
        || p.application?.toLowerCase().includes(lower)
        || p.ticket_ref?.toLowerCase().includes(lower);
  });

  return (
    <div className="space-y-6">
      {/* Header Premium */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E2E8F0] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[#003087]/5 to-[#003087]/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-black text-[#1E2937] flex items-center gap-3 tracking-tight">
              <div className="p-3 bg-gradient-to-br from-[#003087] to-blue-600 rounded-xl text-white shadow-lg shadow-blue-900/20">
                <Key size={28} />
              </div>
              Gestion des Habilitations
            </h1>
            <p className="text-[#64748B] font-medium mt-2 max-w-2xl text-sm leading-relaxed">
              Supervision globale des profils d'accès générés via la plateforme. Visualisez les accès actifs, révoquez les habilitations compromettantes et auditez l'historique d'accès par système métier.
            </p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={fetchProfiles} 
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-[#E2E8F0] text-[#64748B] rounded-xl font-bold hover:bg-[#F8FAFC] hover:text-[#003087] transition-all shadow-sm"
              disabled={loading}
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
              Actualiser
            </button>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-[#E2E8F0] flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={18} className="text-[#94A3B8]" />
          </div>
          <input
            type="text"
            placeholder="Chercher par nom, compte technique, système ou ticket..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#003087]/20 focus:border-[#003087] transition-all text-sm font-medium"
          />
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 px-3 py-2 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0]">
            <Filter size={16} className="text-[#64748B]" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-transparent border-none focus:outline-none focus:ring-0 text-sm font-bold text-[#1E2937] py-0 cursor-pointer"
            >
              <option value="ALL">Tous les statuts</option>
              <option value="ACTIVE">Actifs</option>
              <option value="REVOKED">Révoqués</option>
              <option value="EXPIRED">Expirés</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards (Mini) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Habilitations Actives', val: profiles.filter(p => p.status === 'ACTIVE').length, icon: ShieldCheck, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: 'Accès Révoqués', val: profiles.filter(p => p.status === 'REVOKED').length, icon: ShieldAlert, color: 'text-red-600', bg: 'bg-red-50' },
          { label: 'Total Comptes Générés', val: profiles.length, icon: User, color: 'text-blue-600', bg: 'bg-blue-50' },
        ].map((stat, idx) => (
          <div key={idx} className="bg-white rounded-xl p-5 border border-[#E2E8F0] shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div>
              <div className="text-xs font-bold text-[#64748B] uppercase tracking-wider mb-1">{stat.label}</div>
              <div className="text-2xl font-black text-[#1E2937] leading-none">{stat.val}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tableau listant les habilitations */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#E2E8F0] overflow-hidden">
        {loading && profiles.length === 0 ? (
          <div className="p-12 text-center text-[#64748B]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#003087] mx-auto mb-4"></div>
            Chargement des habilitations...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500 font-medium">
            <AlertTriangle className="mx-auto mb-2 opacity-50" size={32} />
            {error}
          </div>
        ) : filteredProfiles.length === 0 ? (
          <div className="p-16 text-center text-[#64748B] bg-[#F8FAFC]/50">
            <Key size={48} className="mx-auto mb-4 opacity-20 text-[#003087]" />
            <p className="text-lg font-bold">Aucune habilitation trouvée.</p>
            <p className="text-sm mt-1">Générez des accès en approuvant des tickets.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-left text-xs font-black text-[#64748B] uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4 rounded-tl-xl">Employé & Compte</th>
                  <th className="px-6 py-4">Système Cible</th>
                  <th className="px-6 py-4">Détail des Accès</th>
                  <th className="px-6 py-4">Référence Origine</th>
                  <th className="px-6 py-4">Statut</th>
                  <th className="px-6 py-4 text-right rounded-tr-xl">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {filteredProfiles.map((p) => (
                  <tr key={p.id} className="hover:bg-[#F8FAFC] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm shrink-0">
                          {p.employee_name?.charAt(0) || 'U'}
                        </div>
                        <div>
                          <div className="font-bold text-[#1E2937]">{p.employee_name || 'Utilisateur'}</div>
                          <div className="text-xs text-[#64748B] font-mono mt-0.5">{p.account_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Server size={14} className="text-[#94A3B8]" />
                        <span className="font-bold text-[#334155]">{p.system_name || 'Non défini'}</span>
                      </div>
                      <div className="text-xs text-[#64748B] mt-1 line-clamp-1">{p.application}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-1 flex-wrap">
                        {p.environments?.map(env => (
                          <span key={env} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-bold border border-slate-200">
                            {env}
                          </span>
                        ))}
                      </div>
                      <div className="text-[10px] text-[#94A3B8] font-medium mt-1 truncate max-w-[150px]">
                        {p.access_types?.join(', ')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Link to={`/ticket/${p.ticket_id}`} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 text-[#003087] font-bold text-xs hover:bg-blue-100 hover:underline transition-colors border border-blue-100">
                        <FileText size={12} />
                        {p.ticket_ref}
                      </Link>
                      <div className="text-[10px] text-[#94A3B8] mt-1 whitespace-nowrap">
                        {new Date(p.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(p)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {p.status === 'ACTIVE' && (
                        <button
                          onClick={() => { setProfileToRevoke(p); setShowRevokeModal(true); }}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent shadow-sm hover:border-red-200 opacity-0 group-hover:opacity-100 focus:opacity-100"
                          title="Révoquer l'accès"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de révocation */}
      {showRevokeModal && profileToRevoke && (
        <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setShowRevokeModal(false)}></div>
          <div className="bg-white rounded-2xl p-6 md:p-8 max-w-md w-full relative z-10 shadow-2xl border border-[#E2E8F0] animate-in fade-in zoom-in duration-200">
            <button
              onClick={() => setShowRevokeModal(false)}
              className="absolute top-4 right-4 p-2 text-[#94A3B8] hover:text-[#1E2937] hover:bg-[#F1F5F9] rounded-xl transition-colors"
            >
              <X size={20} />
            </button>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-red-100 text-red-600 rounded-xl">
                <ShieldAlert size={28} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#1E2937]">Révoquer l'habilitation</h3>
                <p className="text-sm text-[#64748B]">Action immédiate et irréversible</p>
              </div>
            </div>

            <div className="bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] mb-6">
              <div className="text-xs text-[#64748B] font-bold uppercase tracking-widest mb-1">Compte Cible</div>
              <div className="font-mono text-sm font-bold text-[#1E2937] flex items-center gap-2">
                <Lock size={14} className="text-[#003087]" />
                {profileToRevoke.account_name} <span className="text-[#94A3B8] font-normal text-xs">({profileToRevoke.system_name})</span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-[#334155] mb-2">Motif de la révocation <span className="text-red-500">*</span></label>
                <textarea
                  value={revokeReason}
                  onChange={(e) => setRevokeReason(e.target.value)}
                  placeholder="Ex: Fin de mission, Risque de sécurité détecté..."
                  className="w-full px-4 py-3 bg-white border border-[#E2E8F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all text-sm resize-none min-h-[100px]"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRevokeModal(false)}
                  className="flex-1 py-2.5 px-4 bg-white text-[#64748B] border border-[#E2E8F0] rounded-xl font-bold hover:bg-[#F8FAFC] hover:text-[#1E2937] transition-colors"
                  disabled={actionLoading}
                >
                  Annuler
                </button>
                <button
                  type="button"
                  onClick={handleRevoke}
                  className="flex-1 py-2.5 px-4 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 hover:shadow-lg hover:shadow-red-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  disabled={actionLoading || !revokeReason.trim()}
                >
                  {actionLoading ? <RefreshCw size={18} className="animate-spin" /> : <Ban size={18} />}
                  Confirmer la Révocation
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
