import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, User, Users, Briefcase, Server, ShieldCheck, 
  Brain, TrendingUp, Clock, CheckCircle, XCircle, AlertTriangle, 
  RefreshCw, Mail, Calendar, ThumbsUp, ThumbsDown, Sparkles,
  AlertCircle, Shield, Database, Key, FileCode, Cpu
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
    application?: string;
    resource?: string;
    criticite?: string;
    user_seniority?: string;
    request_reason?: string;
    manager_approval_status?: string;
    justification?: string;
  };
  created_at: string;
  rejected_reason?: string;
  rejected_by?: string;
  rejected_at?: string;
  assigned_to?: string;
  ai_level?: string;
  ai_confidence?: number;
  ai_probabilities?: { BASE: number; SENSITIVE: number; CRITICAL: number };
  ai_explanation?: string;
  ai_risk_factors?: Record<string, [number, string]>;
  ai_source?: string;
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

  // Feedback Like/Dislike
  const [existingFeedback, setExistingFeedback] = useState<any>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackVote, setFeedbackVote] = useState<'like'|'dislike'|null>(null);
  const [feedbackReasonVote, setFeedbackReasonVote] = useState<'like'|'dislike'|null>(null);
  const [correctedLevel, setCorrectedLevel] = useState('');
  const [correctedReason, setCorrectedReason] = useState('');
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  const token = localStorage.getItem('token');

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
        if (response.status === 404) throw new Error('Ticket introuvable');
        throw new Error('Erreur lors du chargement');
      }

      const data = await response.json();
      setTicket(data);

      // Construire l'historique à partir des données disponibles
      const hist: any[] = [
        { id: 1, action: 'Ticket créé', acteur: 'Système', details: 'Demande enregistrée', date: data.created_at },
      ];

      // Ajouter l'entrée IA si on a les données
      if (data.ai_level) {
        const niveauFr = data.ai_level === 'BASE' ? 'Base' : data.ai_level === 'SENSITIVE' ? 'Sensible' : 'Critique';
        hist.push({
          id: 2,
          action: 'Analyse IA',
          acteur: 'Moteur IA',
          details: `Classification : ${niveauFr} — Confiance : ${data.ai_confidence ?? 0}%`,
          date: data.classification?.processed_at || data.created_at
        });
      }

      // Ajouter l'entrée d'assignation si ticket assigné
      if (data.assigned_to && data.assigned_at) {
        const dest = data.assigned_to === 'SUPER_ADMIN' ? 'Super Admin' : data.assigned_to === 'ADMIN' ? 'Admin' : data.assigned_to;
        hist.push({
          id: 3,
          action: 'Assignation automatique',
          acteur: 'Moteur de décision',
          details: `Ticket assigné à ${dest}`,
          date: data.assigned_at
        });
      }

      // Ajouter le rejet si applicable
      if (data.status === 'REJECTED' && data.rejected_at) {
        hist.push({
          id: 4,
          action: 'Ticket rejeté',
          acteur: data.rejected_by || 'Administrateur',
          details: `Motif : ${data.rejected_reason || 'Non précisé'}`,
          date: data.rejected_at
        });
      }

      setHistorique(hist);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  const fetchExistingFeedback = async () => {
    if (!token || !id) return;
    try {
      const r = await fetch(`http://127.0.0.1:8000/feedback/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (r.ok) {
        const d = await r.json();
        if (d.has_feedback) {
          setExistingFeedback(d);
          setFeedbackVote(d.classification_vote);
          setFeedbackReasonVote(d.reason_vote);
        }
      }
    } catch (e) { console.error(e); }
  };

  const handleLike = async () => {
    if (!ticket) return;
    setFeedbackLoading(true);
    try {
      const r = await fetch(`http://127.0.0.1:8000/feedback/${ticket.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          classification_vote: 'like',
          reason_vote: 'like', // Par défaut
        })
      });
      if (r.ok) {
        setFeedbackSuccess(true);
        setFeedbackVote('like');
        setExistingFeedback({
          has_feedback: true,
          classification_vote: 'like',
          reason_vote: 'like',
        });
        // Auto-refresh stats si on est en communication avec le backend
      }
    } finally { setFeedbackLoading(false); }
  };

  const submitFeedback = async () => {
    if (!feedbackVote || !ticket) return;
    if (feedbackVote === 'dislike' && !correctedLevel) return;
    setFeedbackLoading(true);
    try {
      const r = await fetch(`http://127.0.0.1:8000/feedback/${ticket.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          classification_vote: feedbackVote,
          reason_vote: feedbackReasonVote,
          corrected_level: feedbackVote === 'dislike' ? correctedLevel : undefined,
          corrected_reason: feedbackVote === 'dislike' ? correctedReason : undefined,
        })
      });
      if (r.ok) {
        setFeedbackSuccess(true);
        setShowFeedbackModal(false);
        setExistingFeedback({
          has_feedback: true,
          classification_vote: feedbackVote,
          reason_vote: feedbackReasonVote,
        });
      }
    } finally { setFeedbackLoading(false); }
  };
    fetchUserInfo();
    fetchTicket();
    fetchExistingFeedback();
  }, [id]);

  const canActOnTicket = (): boolean => {
    if (!ticket || !userInfo) return false;
    if (userInfo.role === 'SUPER_ADMIN') return true;
    if (userInfo.role === 'ADMIN') {
      return ticket.assigned_to === 'ADMIN' || ticket.assigned_to === 'ADMIN,SUPER_ADMIN' || (ticket.status === 'NEW' && !ticket.assigned_to);
    }
    return false;
  };

  const handleApprove = async () => {
    if (!ticket || !canActOnTicket()) return;
    setActionLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution: 'Demande approuvée' })
      });
      if (!response.ok) throw new Error('Erreur lors de l\'approbation');
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
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Erreur lors du rejet');
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
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Erreur lors de l\'escalade');
      await fetchTicket();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const getNiveauAcces = (): string => {
    if (!ticket) return 'Base';
    if (ticket.ai_level) {
      return ticket.ai_level === 'BASE' ? 'Base' : 
             ticket.ai_level === 'SENSITIVE' ? 'Sensible' : 'Critique';
    }
    return 'Base';
  };

  const getConfianceScore = (): number => {
    return ticket?.ai_confidence || 0;
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

  const getProbabilities = () => {
    // ✅ Lit directement ai_probabilities depuis le ticket (champ plat renvoyé par l'API)
    if (ticket?.ai_probabilities && Object.keys(ticket.ai_probabilities).length > 0) {
      return ticket.ai_probabilities as { BASE: number; SENSITIVE: number; CRITICAL: number };
    }
    // Fallback : essayer depuis classification imbriqué
    const cls = (ticket as any)?.classification;
    if (cls?.probabilities && Object.keys(cls.probabilities).length > 0) {
      return cls.probabilities as { BASE: number; SENSITIVE: number; CRITICAL: number };
    }
    return null;
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
          <button onClick={() => navigate('/tickets')} className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]">
            Retour à la liste
          </button>
        </div>
      </div>
    );
  }

  const userCanAct = canActOnTicket();
  const probabilities = getProbabilities();

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/tickets')} className="p-2 hover:bg-white rounded-lg transition-colors">
          <ArrowLeft size={24} className="text-[#64748B]" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Détail du Ticket</h1>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xl font-semibold text-[#003087]">{ticket.ref}</span>
            <Badge className={`${getStatutBadgeColor(ticket.status)} border`}>
              {getStatutFrancais(ticket.status)}
            </Badge>
            {ticket.assigned_to && (
              <Badge className="bg-purple-100 text-purple-800 border-purple-300 border">
                Assigné à: {ticket.assigned_to === 'SUPER_ADMIN' ? 'Super Admin' : 'Admin'}
              </Badge>
            )}
            {ticket.ai_level && (
              <Badge className={`${getNiveauBadgeColor(getNiveauAcces())} border`}>
                <Brain size={14} className="mr-1 inline" />
                IA: {getNiveauAcces()} ({getConfianceScore()}%)
              </Badge>
            )}
          </div>
        </div>
        <button onClick={fetchTicket} className="p-2 hover:bg-white rounded-lg transition-colors" title="Actualiser">
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
        <div className="lg:col-span-2 space-y-6">
          {/* Informations demandeur - inchangé */}
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-2">
              <User className="text-[#003087]" size={24} />
              Informations Demandeur
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div><div className="text-sm text-[#64748B] mb-1">Nom complet</div><div className="text-[#1E2937] font-semibold">{ticket.employee_name}</div></div>
              <div><div className="text-sm text-[#64748B] mb-1">Email</div><div className="text-[#1E2937] font-semibold flex items-center gap-2"><Mail size={16} />{ticket.employee_email}</div></div>
              <div><div className="text-sm text-[#64748B] mb-1">Équipe</div><div className="text-[#1E2937] font-semibold flex items-center gap-2"><Users size={16} />{ticket.team_name}</div></div>
              <div><div className="text-sm text-[#64748B] mb-1">Rôle</div><div className="text-[#1E2937] font-semibold flex items-center gap-2"><Briefcase size={16} />{ticket.role || 'Non spécifié'}</div></div>
              <div><div className="text-sm text-[#64748B] mb-1">Date de création</div><div className="text-[#1E2937] font-semibold flex items-center gap-2"><Calendar size={16} />{new Date(ticket.created_at).toLocaleString('fr-FR')}</div></div>
              <div><div className="text-sm text-[#64748B] mb-1">Environnements</div><div className="flex gap-1 flex-wrap">{ticket.requested_environments?.map((env) => (<Badge key={env} className="bg-blue-50 text-blue-700 border-blue-200 border"><Server size={12} className="mr-1" />{env}</Badge>))}</div></div>
            </div>
          </div>

          {/* ── Analyse IA ──────────────────────────────────────────────── */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-sm">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-[#1E2937] flex items-center gap-2">
                <Brain className="text-[#003087]" size={24} />
                Analyse IA
              </h2>
              {ticket.ai_source === 'human_correction' && (
                <Badge className="bg-amber-100 text-amber-800 border-amber-300 border flex items-center gap-1">
                  <Shield size={12} /> Correction humaine appliquée
                </Badge>
              )}
            </div>

            <div className="space-y-4">
              {/* Niveau + Confiance */}
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

              {/* Probabilités */}
              {probabilities && (
                <div className="bg-white rounded-lg p-4 border border-purple-200">
                  <div className="text-sm text-[#64748B] mb-2 font-semibold">Probabilités détaillées</div>
                  <div className="space-y-2">
                    <div><div className="flex justify-between text-sm"><span>Base</span><span>{probabilities.BASE}%</span></div><Progress value={probabilities.BASE} className="h-2 bg-gray-200" /></div>
                    <div><div className="flex justify-between text-sm"><span>Sensible</span><span>{probabilities.SENSITIVE}%</span></div><Progress value={probabilities.SENSITIVE} className="h-2 bg-gray-200" /></div>
                    <div><div className="flex justify-between text-sm"><span>Critique</span><span>{probabilities.CRITICAL}%</span></div><Progress value={probabilities.CRITICAL} className="h-2 bg-gray-200" /></div>
                  </div>
                </div>
              )}

              {/* ── RAISON DE CLASSEMENT ── */}
              <div className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="text-sm text-[#64748B] mb-3 font-semibold flex items-center gap-2">
                  <Sparkles size={14} className="text-purple-500" />
                  Raison de classement
                </div>
                {ticket.ai_explanation ? (
                  <div className="space-y-3">
                    <p className="text-[#1E2937] text-sm leading-relaxed whitespace-pre-line">
                      {ticket.ai_explanation}
                    </p>
                    {/* Facteurs de risque (breakdown) */}
                    {ticket.ai_risk_factors && Object.keys(ticket.ai_risk_factors).length > 0 && (
                      <div className="mt-3 space-y-2 border-t border-gray-100 pt-3">
                        <div className="text-xs font-semibold text-[#64748B] mb-2">Facteurs détectés</div>
                        {Object.entries(ticket.ai_risk_factors)
                          .sort(([, a], [, b]) => Math.abs(b[0]) - Math.abs(a[0]))
                          .map(([key, [pts, desc]]) => (
                            <div key={key} className="flex items-center gap-3">
                              <span className={`text-xs font-bold w-14 text-right shrink-0 ${pts > 0 ? 'text-red-500' : 'text-green-600'}`}>
                                {pts > 0 ? `+${pts}` : pts} pts
                              </span>
                              <div className="flex-1">
                                <div className="text-xs text-[#1E2937] mb-1">{desc}</div>
                                <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${pts > 30 ? 'bg-red-500' : pts > 0 ? 'bg-amber-400' : 'bg-green-400'}`}
                                    style={{ width: `${Math.min(Math.abs(pts), 50) * 2}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-[#64748B] text-sm italic">Aucune explication disponible (modèle non chargé)</p>
                )}
              </div>

              {/* ── FEEDBACK LIKE / DISLIKE ── */}
              <div className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="text-sm text-[#64748B] mb-3 font-semibold flex items-center gap-2">
                  <Cpu size={14} className="text-purple-500" />
                  Votre avis sur cette classification
                </div>
                {feedbackSuccess && (
                  <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
                    <CheckCircle size={14} /> Feedback enregistré — merci !
                  </div>
                )}
                {existingFeedback ? (
                  <div className={`p-4 rounded-xl border-2 transition-all duration-500 flex items-center justify-between ${
                    existingFeedback.classification_vote === 'like' 
                      ? 'bg-green-50 border-green-200 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
                      : 'bg-red-50 border-red-200 shadow-[0_0_15px_rgba(239,68,68,0.1)]'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        existingFeedback.classification_vote === 'like' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                      }`}>
                        {existingFeedback.classification_vote === 'like' ? <ThumbsUp size={20} className="fill-current" /> : <ThumbsDown size={20} className="fill-current" />}
                      </div>
                      <div>
                        <div className={`font-bold ${existingFeedback.classification_vote === 'like' ? 'text-green-700' : 'text-red-700'}`}>
                          {existingFeedback.classification_vote === 'like' ? 'Classification validée' : 'Correction suggérée'}
                        </div>
                        <div className="text-xs text-[#64748B]">
                          Vote enregistré le {existingFeedback.created_at ? new Date(existingFeedback.created_at).toLocaleDateString() : 'à l\'instant'}
                        </div>
                      </div>
                    </div>
                    <button onClick={() => { setExistingFeedback(null); setFeedbackSuccess(false); }}
                      className="px-3 py-1.5 text-xs font-medium border border-[#E2E8F0] rounded-lg hover:bg-white transition-colors text-[#64748B]">
                      Changer mon avis
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-4">
                    <button
                      onClick={handleLike}
                      disabled={feedbackLoading}
                      className="flex-1 py-3 border-2 border-green-300 text-green-700 rounded-xl font-bold hover:bg-green-500 hover:text-white hover:border-green-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50 group hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] shadow-sm bg-white"
                    >
                      {feedbackLoading && feedbackVote === 'like' ? <RefreshCw size={20} className="animate-spin" /> : <ThumbsUp size={20} className="group-hover:scale-125 transition-transform" />}
                      Classification correcte
                    </button>
                    <button
                      onClick={() => { setFeedbackVote('dislike'); setShowFeedbackModal(true); setCorrectedLevel(ticket.ai_level || ''); }}
                      disabled={feedbackLoading}
                      className="flex-1 py-3 border-2 border-red-300 text-red-700 rounded-xl font-bold hover:bg-red-500 hover:text-white hover:border-red-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50 group hover:shadow-[0_0_20px_rgba(239,68,68,0.3)] shadow-sm bg-white"
                    >
                      <ThumbsDown size={20} className="group-hover:scale-125 transition-transform" /> 
                      Inexacte / Corriger
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Accès demandés */}
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-2"><ShieldCheck className="text-[#003087]" size={24} />Accès Demandés</h2>
            <div className="p-4 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0]">
              <div className="font-semibold text-[#1E2937] mb-2">Types d'accès demandés</div>
              <div className="flex gap-2 flex-wrap">{ticket.requested_access_details?.access_types?.map((type, idx) => (<Badge key={idx} className="bg-gray-100 text-gray-700 border-gray-200">{type}</Badge>))}</div>
              {ticket.requested_access_details?.justification && (<><div className="font-semibold text-[#1E2937] mt-4 mb-2">Justification</div><div className="text-[#64748B]">{ticket.requested_access_details.justification}</div></>)}
              <div className="font-semibold text-[#1E2937] mt-4 mb-2">Description</div><div className="text-[#64748B]">{ticket.description}</div>
            </div>
          </div>
        </div>

        {/* Colonne latérale - Actions */}
        <div className="lg:sticky lg:top-24 space-y-6 self-start lg:h-fit">
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="text-lg font-bold text-[#1E2937] mb-4">Actions</h3>
            <div className="space-y-3">
              {(ticket.status === 'NEW' || ticket.status === 'ASSIGNED') && userCanAct && (
                <>
                  <button onClick={handleApprove} disabled={actionLoading} className="w-full py-3 bg-[#10B981] text-white rounded-lg font-semibold hover:bg-[#059669] transition-colors flex items-center justify-center gap-2 disabled:opacity-50">
                    <CheckCircle size={20} /> {actionLoading ? 'Traitement...' : 'Approuver'}
                  </button>
                  <button onClick={() => setShowRejectModal(true)} disabled={actionLoading} className="w-full py-3 bg-[#EF4444] text-white rounded-lg font-semibold hover:bg-[#DC2626] transition-colors flex items-center justify-center gap-2 disabled:opacity-50">
                    <XCircle size={20} /> Rejeter
                  </button>
                </>
              )}
              {(ticket.status === 'NEW' || ticket.status === 'ASSIGNED') && !userCanAct && (
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <p className="text-gray-600 text-sm">Ce ticket n'est pas assigné à votre rôle</p>
                  <p className="text-gray-500 text-xs mt-1">Assigné à: {ticket.assigned_to === 'SUPER_ADMIN' ? 'Super Admin' : ticket.assigned_to?.includes('ADMIN') ? 'Admin' : 'En attente'}</p>
                </div>
              )}
              {ticket.status === 'APPROVED' && (<div className="p-4 bg-green-50 rounded-lg text-center"><CheckCircle className="mx-auto mb-2 text-green-600" size={32} /><p className="text-green-800 font-semibold">Ticket approuvé</p><p className="text-green-600 text-sm">Les accès ont été attribués</p></div>)}
              {ticket.status === 'REJECTED' && (<div className="p-4 bg-red-50 rounded-lg text-center"><XCircle className="mx-auto mb-2 text-red-600" size={32} /><p className="text-red-800 font-semibold">Ticket rejeté</p></div>)}
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="text-lg font-bold text-[#1E2937] mb-4 flex items-center gap-2"><Clock size={20} />Historique</h3>
            <div className="space-y-4 max-h-[50vh] overflow-y-auto">
              {historique.map((event) => (
                <div key={event.id} className="relative pl-6 pb-4 border-l-2 border-[#E2E8F0] last:border-0 last:pb-0">
                  <div className="absolute -left-[9px] top-0 w-4 h-4 bg-[#003087] rounded-full border-2 border-white"></div>
                  <div className="text-xs text-[#64748B] mb-1">{new Date(event.date).toLocaleString('fr-FR')}</div>
                  <div className="font-semibold text-[#1E2937] text-sm mb-1">{event.action}</div>
                  <div className="text-sm text-[#64748B]"><span className="font-medium">{event.acteur}</span> - {event.details}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-[#1E2937] mb-4">Motif de rejet</h3>
            <p className="text-sm text-[#64748B] mb-4">Veuillez indiquer la raison du rejet de cette demande (obligatoire)</p>
            <textarea value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} placeholder="Expliquez pourquoi cette demande est rejetée..." className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#EF4444] focus:border-transparent resize-none h-32" required />
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowRejectModal(false)} className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors">Annuler</button>
              <button onClick={handleReject} disabled={!rejectReason.trim() || actionLoading} className="flex-1 py-2.5 bg-[#EF4444] text-white rounded-lg font-semibold hover:bg-[#DC2626] transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                {actionLoading ? 'Traitement...' : 'Confirmer le rejet'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── FEEDBACK MODAL (DISLIKE) ── */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-2xl border border-purple-100 anim-fade-in">
            <div className="flex items-center gap-3 mb-4 text-[#003087]">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Brain size={24} />
              </div>
              <h3 className="text-xl font-bold">Améliorer l'Intelligence IA</h3>
            </div>
            
            <p className="text-sm text-[#64748B] mb-6">
              Votre feedback est précieux. En corrigeant cette classification, vous aidez le modèle à mieux comprendre les risques spécifiques de votre environnement.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-[#1E2937] mb-2">
                  Quelle est la classification correcte ?
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { val: 'BASE', lab: 'Base', color: 'bg-green-50 text-green-700 border-green-200' },
                    { val: 'SENSITIVE', lab: 'Sensible', color: 'bg-amber-50 text-amber-700 border-amber-200' },
                    { val: 'CRITICAL', lab: 'Critique', color: 'bg-red-50 text-red-700 border-red-200' },
                  ].map(lvl => (
                    <button
                      key={lvl.val}
                      onClick={() => setCorrectedLevel(lvl.val)}
                      className={`py-2 px-3 rounded-lg border-2 text-sm font-bold transition-all ${
                        correctedLevel === lvl.val 
                          ? `${lvl.color.replace('border-', 'border-')} ring-2 ring-offset-1 ring-blue-500` 
                          : 'bg-white text-gray-500 border-gray-100 hover:border-gray-300'
                      }`}
                    >
                      {lvl.lab}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-[#1E2937] mb-2">
                  Pourquoi la classification actuelle est erronée ?
                </label>
                <textarea 
                  value={correctedReason} 
                  onChange={(e) => setCorrectedReason(e.target.value)} 
                  placeholder="Ex: 'Cet accès sur PRD est critique même pour un développeur senior...'" 
                  className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent resize-none h-28 text-sm" 
                  required 
                />
                <p className="text-[10px] text-[#94A3B8] mt-1 italic">
                  * Cette raison sera intégrée dans la bibliothèque de corrections et re-utilisée par l'IA.
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button 
                onClick={() => setShowFeedbackModal(false)} 
                className="flex-1 py-2.5 bg-gray-50 text-[#64748B] rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Annuler
              </button>
              <button 
                onClick={submitFeedback} 
                disabled={!correctedLevel || (feedbackVote === 'dislike' && !correctedReason.trim()) || feedbackLoading} 
                className="flex-[2] py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {feedbackLoading ? <RefreshCw size={18} className="animate-spin" /> : <Sparkles size={18} />}
                Enregistrer la correction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}