import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, User, Users, Briefcase, Server, ShieldCheck, 
  Brain, TrendingUp, Clock, CheckCircle, XCircle, AlertTriangle, 
  RefreshCw, Mail, Calendar 
} from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';

interface Ticket {
  id: number;
  ref: string;
  status: string;
  employee_id: string;
  employee_name: string;
  employee_email: string;
  team_name: string;
  role: string;
  description: string;
  requested_environments: string[];
  requested_access_details: {
    access_types?: string[];
    criticite?: string;
    justification?: string;
  };
  created_at: string;
  rejected_reason?: string;
  rejected_by?: string;
  rejected_at?: string;
  assigned_to?: string;  // ✅ NOUVEAU : champ d'assignation
}

interface UserInfo {
  role: string;
  username: string;
}

export function TicketDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [historique, setHistorique] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const token = localStorage.getItem('token');

  // Récupérer les infos de l'utilisateur connecté
  const fetchUserInfo = async () => {
    if (!token) return;
    try {
      const response = await fetch('http://127.0.0.1:8000/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUserInfo({ role: data.role, username: data.username });
      }
    } catch (err) {
      console.error('Erreur chargement user:', err);
    }
  };

  const fetchTicket = async () => {
    if (!token) {
      setError('Non authentifié');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Ticket introuvable');
        }
        throw new Error('Erreur lors du chargement');
      }

      const data = await response.json();
      setTicket(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserInfo();
    fetchTicket();
  }, [id]);

  // Vérifier si l'utilisateur peut agir sur ce ticket
  const canActOnTicket = (): boolean => {
    if (!ticket || !userInfo) return false;
    
    // Super Admin peut agir sur tous les tickets
    if (userInfo.role === 'SUPER_ADMIN') return true;
    
    // Admin peut agir sur les tickets qui lui sont assignés
    if (userInfo.role === 'ADMIN') {
      return ticket.assigned_to === 'ADMIN' || 
             (ticket.status === 'NEW' && !ticket.assigned_to);
    }
    
    return false;
  };

  const handleApprove = async () => {
    if (!ticket || !canActOnTicket()) return;
    setActionLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resolution: 'Demande approuvée' })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'approbation');
      }

      await fetchTicket();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!ticket || !canActOnTicket() || !rejectReason.trim()) return;
    setActionLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/reject?reason=${encodeURIComponent(rejectReason)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors du rejet');
      }

      setShowRejectModal(false);
      await fetchTicket();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!ticket || !canActOnTicket()) return;
    setActionLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/escalate?escalate_to=SUPER_ADMIN`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'escalade');
      }

      await fetchTicket();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const getNiveauAcces = (): string => {
    if (!ticket) return 'Base';
    const details = ticket.requested_access_details;
    if (details?.criticite === 'CRITIQUE') return 'Critique';
    if (details?.criticite === 'SENSIBLE') return 'Sensible';
    return 'Base';
  };

  const getConfianceScore = (): number => {
    const niveau = getNiveauAcces();
    if (niveau === 'Base') return 92;
    if (niveau === 'Sensible') return 78;
    return 65;
  };

  const getIAExplanation = (): string => {
    const niveau = getNiveauAcces();
    const details = ticket?.requested_access_details;
    const accessTypes = details?.access_types?.join(', ') || 'accès';
    const envs = ticket?.requested_environments?.join(', ') || 'environnement';
    
    if (niveau === 'Critique') {
      return `Demande d'accès critique (${accessTypes}) sur ${envs}. Nécessite validation Super Admin pour des raisons de sécurité.`;
    }
    if (niveau === 'Sensible') {
      return `Demande d'accès sensible (${accessTypes}) sur ${envs}. Validation Admin requise.`;
    }
    return `Demande d'accès standard (${accessTypes}) sur ${envs}. Auto-approbation possible.`;
  };

  const getStatutBadgeColor = (statut: string) => {
    switch (statut) {
      case 'NEW': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'ASSIGNED': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'APPROVED': return 'bg-green-100 text-green-800 border-green-300';
      case 'REJECTED': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatutFrancais = (status: string) => {
    switch (status) {
      case 'NEW': return 'En attente';
      case 'ASSIGNED': return 'Assigné';
      case 'APPROVED': return 'Approuvé';
      case 'REJECTED': return 'Rejeté';
      default: return status;
    }
  };

  const getNiveauBadgeColor = (niveau: string) => {
    switch (niveau) {
      case 'Base': return 'bg-green-100 text-green-800 border-green-300';
      case 'Sensible': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Critique': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du ticket...</p>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg inline-block mb-4">
          {error || 'Ticket introuvable'}
        </div>
        <div>
          <button
            onClick={() => navigate('/tickets')}
            className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]"
          >
            Retour à la liste
          </button>
        </div>
      </div>
    );
  }

  const userCanAct = canActOnTicket();

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/tickets')}
          className="p-2 hover:bg-white rounded-lg transition-colors"
        >
          <ArrowLeft size={24} className="text-[#64748B]" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Détail du Ticket</h1>
          <div className="flex items-center gap-3">
            <span className="text-xl font-semibold text-[#003087]">{ticket.ref}</span>
            <Badge className={`${getStatutBadgeColor(ticket.status)} border`}>
              {getStatutFrancais(ticket.status)}
            </Badge>
            {ticket.assigned_to && (
              <Badge className="bg-purple-100 text-purple-800 border-purple-300 border">
                Assigné à: {ticket.assigned_to === 'SUPER_ADMIN' ? 'Super Admin' : 'Admin'}
              </Badge>
            )}
          </div>
        </div>
        <button
          onClick={fetchTicket}
          className="p-2 hover:bg-white rounded-lg transition-colors"
          title="Actualiser"
        >
          <RefreshCw size={20} className="text-[#64748B]" />
        </button>
      </div>

      {ticket.status === 'REJECTED' && ticket.rejected_reason && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-red-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-red-800">Motif du rejet</p>
              <p className="text-red-700 mt-1">{ticket.rejected_reason}</p>
              {ticket.rejected_by && (
                <p className="text-red-600 text-sm mt-2">
                  Rejeté par : {ticket.rejected_by} le {new Date(ticket.rejected_at!).toLocaleString('fr-FR')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonne principale - inchangée */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-2">
              <User className="text-[#003087]" size={24} />
              Informations Demandeur
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-sm text-[#64748B] mb-1">Nom complet</div>
                <div className="text-[#1E2937] font-semibold">{ticket.employee_name}</div>
              </div>
              <div>
                <div className="text-sm text-[#64748B] mb-1">Email</div>
                <div className="text-[#1E2937] font-semibold flex items-center gap-2">
                  <Mail size={16} />
                  {ticket.employee_email}
                </div>
              </div>
              <div>
                <div className="text-sm text-[#64748B] mb-1">Équipe</div>
                <div className="text-[#1E2937] font-semibold flex items-center gap-2">
                  <Users size={16} />
                  {ticket.team_name}
                </div>
              </div>
              <div>
                <div className="text-sm text-[#64748B] mb-1">Rôle</div>
                <div className="text-[#1E2937] font-semibold flex items-center gap-2">
                  <Briefcase size={16} />
                  {ticket.role || 'Non spécifié'}
                </div>
              </div>
              <div>
                <div className="text-sm text-[#64748B] mb-1">Date de création</div>
                <div className="text-[#1E2937] font-semibold flex items-center gap-2">
                  <Calendar size={16} />
                  {new Date(ticket.created_at).toLocaleString('fr-FR')}
                </div>
              </div>
              <div>
                <div className="text-sm text-[#64748B] mb-1">Environnements</div>
                <div className="flex gap-1 flex-wrap">
                  {ticket.requested_environments?.map((env) => (
                    <Badge key={env} className="bg-blue-50 text-blue-700 border-blue-200 border">
                      <Server size={12} className="mr-1" />
                      {env}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-sm">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-2">
              <Brain className="text-[#003087]" size={24} />
              Analyse IA
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-[#64748B] mb-1">Niveau prédit</div>
                  <Badge className={`${getNiveauBadgeColor(getNiveauAcces())} border text-base py-1 px-3`}>
                    {getNiveauAcces()}
                  </Badge>
                </div>
                <div className="text-right">
                  <div className="text-sm text-[#64748B] mb-1">Score de confiance</div>
                  <div className="text-2xl font-bold text-[#003087]">{getConfianceScore()}%</div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#64748B]">Confiance du modèle</span>
                  <TrendingUp size={16} className={getConfianceScore() > 80 ? 'text-[#10B981]' : 'text-[#F59E0B]'} />
                </div>
                <Progress value={getConfianceScore()} className="h-3" />
              </div>
              <div className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="text-sm text-[#64748B] mb-2 font-semibold">Explication détaillée</div>
                <div className="text-[#1E2937]">{getIAExplanation()}</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-2">
              <ShieldCheck className="text-[#003087]" size={24} />
              Accès Demandés
            </h2>
            <div className="space-y-3">
              <div className="p-4 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0]">
                <div className="font-semibold text-[#1E2937] mb-2">Types d'accès demandés</div>
                <div className="flex gap-2 flex-wrap">
                  {ticket.requested_access_details?.access_types?.map((type, idx) => (
                    <Badge key={idx} className="bg-gray-100 text-gray-700 border-gray-200">
                      {type}
                    </Badge>
                  ))}
                </div>
                {ticket.requested_access_details?.justification && (
                  <>
                    <div className="font-semibold text-[#1E2937] mt-4 mb-2">Justification</div>
                    <div className="text-[#64748B]">{ticket.requested_access_details.justification}</div>
                  </>
                )}
                <div className="font-semibold text-[#1E2937] mt-4 mb-2">Description</div>
                <div className="text-[#64748B]">{ticket.description}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Colonne latérale - Actions */}
        <div className="lg:sticky lg:top-24 space-y-6 self-start lg:h-fit">
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="text-lg font-bold text-[#1E2937] mb-4">Actions</h3>
            <div className="space-y-3">
              {ticket.status === 'NEW' && userCanAct && (
                <>
                  <button
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="w-full py-3 bg-[#10B981] text-white rounded-lg font-semibold hover:bg-[#059669] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircle size={20} />
                    {actionLoading ? 'Traitement...' : 'Approuver'}
                  </button>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={actionLoading}
                    className="w-full py-3 bg-[#EF4444] text-white rounded-lg font-semibold hover:bg-[#DC2626] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <XCircle size={20} />
                    Rejeter
                  </button>
                  <button
                    onClick={handleEscalate}
                    disabled={actionLoading}
                    className="w-full py-3 bg-[#F59E0B] text-white rounded-lg font-semibold hover:bg-[#D97706] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <AlertTriangle size={20} />
                    Escalader vers Super Admin
                  </button>
                </>
              )}
              {ticket.status === 'NEW' && !userCanAct && (
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <p className="text-gray-600 text-sm">Ce ticket n'est pas assigné à votre rôle</p>
                  <p className="text-gray-500 text-xs mt-1">
                    Assigné à: {ticket.assigned_to === 'SUPER_ADMIN' ? 'Super Admin' : 
                               ticket.assigned_to === 'ADMIN' ? 'Admin' : 'En attente d\'assignation'}
                  </p>
                </div>
              )}
              {ticket.status === 'APPROVED' && (
                <div className="p-4 bg-green-50 rounded-lg text-center">
                  <CheckCircle className="mx-auto mb-2 text-green-600" size={32} />
                  <p className="text-green-800 font-semibold">Ticket approuvé</p>
                  <p className="text-green-600 text-sm">Les accès ont été attribués</p>
                </div>
              )}
              {ticket.status === 'REJECTED' && (
                <div className="p-4 bg-red-50 rounded-lg text-center">
                  <XCircle className="mx-auto mb-2 text-red-600" size={32} />
                  <p className="text-red-800 font-semibold">Ticket rejeté</p>
                </div>
              )}
            </div>
          </div>

          {/* Historique */}
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="text-lg font-bold text-[#1E2937] mb-4 flex items-center gap-2">
              <Clock size={20} />
              Historique
            </h3>
            <div className="space-y-4 max-h-[50vh] overflow-y-auto">
              {historique.map((event) => (
                <div key={event.id} className="relative pl-6 pb-4 border-l-2 border-[#E2E8F0] last:border-0 last:pb-0">
                  <div className="absolute -left-[9px] top-0 w-4 h-4 bg-[#003087] rounded-full border-2 border-white"></div>
                  <div className="text-xs text-[#64748B] mb-1">
                    {new Date(event.date).toLocaleString('fr-FR')}
                  </div>
                  <div className="font-semibold text-[#1E2937] text-sm mb-1">{event.action}</div>
                  <div className="text-sm text-[#64748B]">
                    <span className="font-medium">{event.acteur}</span> - {event.details}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modal de rejet */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-[#1E2937] mb-4">Motif de rejet</h3>
            <p className="text-sm text-[#64748B] mb-4">
              Veuillez indiquer la raison du rejet de cette demande (obligatoire)
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Expliquez pourquoi cette demande est rejetée..."
              className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#EF4444] focus:border-transparent resize-none h-32"
              required
            />
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleReject}
                disabled={!rejectReason.trim() || actionLoading}
                className="flex-1 py-2.5 bg-[#EF4444] text-white rounded-lg font-semibold hover:bg-[#DC2626] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? 'Traitement...' : 'Confirmer le rejet'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}