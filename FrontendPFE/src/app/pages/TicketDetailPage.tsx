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
  ai_consistency?: string;
  ai_recommended_action?: string;
  classification?: {
    predicted_level: string;
    confidence: number;
    probabilities: Record<string, number>;
    explanation: string;
    risk_factors: Record<string, [number, string]>;
    source: string;
    consistency_status: string;
    consistency_message: string;
    triggered_rules: string[];
    risk_score_rules: number;
    recommended_action: string;
    confidence_level_label: string;
  };
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
  const [generatedProfile, setGeneratedProfile] = useState<any>(null);
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

      // Si le ticket est approuvé, on va chercher l'habilitation correspondante
      if (data.status === 'APPROVED') {
        try {
          const pRes = await fetch(`http://127.0.0.1:8000/profiles?limit=500`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (pRes.ok) {
            const pData = await pRes.json();
            const prof = pData.profiles.find((p: any) => p.ticket_id === data.id);
            if (prof) setGeneratedProfile(prof);
          }
        } catch(e) { console.error('Erreur chargement profil', e); }
      }

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

  useEffect(() => {
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
      <div className="flex items-center gap-4 bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm">
        <button 
          onClick={() => navigate('/tickets')} 
          className="p-3 hover:bg-[#F1F5F9] rounded-xl transition-all active:scale-95 group"
        >
          <ArrowLeft size={24} className="text-[#64748B] group-hover:text-[#003087]" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2 text-sm text-[#64748B] mb-1">
            <span className="hover:underline cursor-pointer" onClick={() => navigate('/tickets')}>Tickets</span>
            <span>/</span>
            <span className="font-medium text-[#003087]">{ticket.ref}</span>
          </div>
          <h1 className="text-2xl font-bold text-[#1E2937] flex items-center gap-3">
            Détails de la demande
            <Badge className={`${getStatutBadgeColor(ticket.status)} border px-3 py-1 text-xs uppercase tracking-wider font-bold`}>
              {getStatutFrancais(ticket.status)}
            </Badge>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {ticket.ai_level && (
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${getNiveauBadgeColor(getNiveauAcces())} animate-pulse-subtle`}>
              <Brain size={18} />
              <div className="flex flex-col">
                <span className="text-[10px] uppercase font-bold opacity-70 leading-none">Analyse IA</span>
                <span className="text-sm font-black leading-none mt-1">{getNiveauAcces()}</span>
              </div>
            </div>
          )}
          <button 
            onClick={fetchTicket} 
            className="p-3 hover:bg-[#F1F5F9] rounded-xl transition-all text-[#64748B] hover:text-[#003087] border border-[#E2E8F0]" 
            title="Actualiser"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {ticket.status === 'REJECTED' && ticket.rejected_reason && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl p-5 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-red-100 p-2 rounded-lg">
              <XCircle size={24} className="text-red-600" />
            </div>
            <div className="flex-1">
              <p className="font-bold text-red-900 text-lg">Demande Rejetée</p>
              <p className="text-red-700 mt-1 italic">"{ticket.rejected_reason}"</p>
              <div className="flex items-center gap-4 mt-3 text-sm text-red-600 font-medium">
                <span className="flex items-center gap-1"><User size={14} /> {ticket.rejected_by}</span>
                <span className="flex items-center gap-1"><Clock size={14} /> {new Date(ticket.rejected_at!).toLocaleString('fr-FR')}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Informations demandeur */}
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#1E2937] flex items-center gap-3">
                <div className="p-2 bg-[#F8FAFC] rounded-lg text-[#003087] border border-[#E2E8F0]">
                  <User size={24} />
                </div>
                Profil du Demandeur
              </h2>
              <Badge className="bg-[#F1F5F9] text-[#64748B] border-[#E2E8F0] border px-2 py-0.5 font-mono text-[10px]">
                ID: {ticket.employee_id}
              </Badge>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-6 gap-x-8">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400 group-hover:text-[#003087] transition-colors"><User size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Nom complet</div>
                  <div className="text-[#1E2937] font-bold">{ticket.employee_name}</div>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Mail size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Email Professionnel</div>
                  <div className="text-[#1E2937] font-bold">{ticket.employee_email}</div>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Users size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Équipe / Département</div>
                  <div className="text-[#1E2937] font-bold">{ticket.team_name}</div>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Briefcase size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Rôle / Fonction</div>
                  <div className="text-[#1E2937] font-bold">{ticket.role || 'Non spécifié'}</div>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Calendar size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Date de demande</div>
                  <div className="text-[#1E2937] font-bold">{new Date(ticket.created_at).toLocaleString('fr-FR')}</div>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Server size={18} /></div>
                <div>
                  <div className="text-[10px] text-[#64748B] font-bold uppercase tracking-widest mb-0.5">Environnements cibles</div>
                  <div className="flex gap-1.5 flex-wrap mt-1">
                    {ticket.requested_environments?.map((env) => (
                      <Badge key={env} className="bg-blue-50 text-blue-700 border-blue-200 border text-[10px] py-0 px-2 font-bold">
                        {env}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
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

              {/* ── COHÉRENCE DE LA DÉCISION (Requirement) ── */}
              {ticket.classification?.consistency_status && (
                <div className={`rounded-xl p-5 border-2 ${
                  ticket.classification.consistency_status === 'OK' 
                    ? 'bg-emerald-50 border-emerald-100/50 text-emerald-900 shadow-sm' 
                    : 'bg-amber-50 border-amber-100/50 text-amber-900 shadow-sm'
                } transition-all duration-300`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        ticket.classification.consistency_status === 'OK' ? 'bg-emerald-200/50' : 'bg-amber-200/50'
                      }`}>
                        {ticket.classification.consistency_status === 'OK' 
                          ? <CheckCircle size={20} className="text-emerald-700" />
                          : <AlertTriangle size={20} className="text-amber-700" />
                        }
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Verdict Cohérence</span>
                        <span className="text-base font-bold">Indice : {ticket.classification.consistency_status === 'OK' ? 'Décision Cohérente' : 'Ambiguïté Détectée'}</span>
                      </div>
                    </div>
                    {ticket.classification.decision_source && (
                      <Badge className="bg-white/50 border-white text-xs font-bold">
                        {ticket.classification.decision_source}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed font-medium bg-white/30 p-3 rounded-lg border border-white/40">
                    {ticket.classification.consistency_message}
                  </p>
                </div>
              )}

              {/* ── RAISON DE CLASSEMENT ── */}
              <div className="bg-white rounded-xl p-5 border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm text-[#64748B] font-black uppercase tracking-tighter flex items-center gap-2">
                    <Sparkles size={16} className="text-purple-500" />
                    Justification du Diagnostic
                  </div>
                  {ticket.classification?.risk_score_rules !== undefined && (
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-[#64748B]">SCORE MÉTIER :</span>
                      <span className={`text-sm font-black ${ticket.classification.risk_score_rules > 80 ? 'text-red-600' : 'text-emerald-600'}`}>
                        {ticket.classification.risk_score_rules} pts
                      </span>
                    </div>
                  )}
                </div>
                
                {ticket.ai_explanation ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-[#F8FAFC] rounded-xl border border-blue-50 text-[#1E2937] text-sm leading-relaxed font-medium italic relative">
                      <div className="absolute top-0 right-0 p-2 opacity-5">
                        <Brain size={48} />
                      </div>
                      "{ticket.ai_explanation}"
                    </div>

                    {/* Règles expertes triggered_rules */}
                    {ticket.classification?.triggered_rules && ticket.classification.triggered_rules.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest">Règles expertes appliquées :</div>
                        <div className="flex flex-wrap gap-1.5">
                          {ticket.classification.triggered_rules.map((rule, ri) => (
                            <div key={ri} className="flex items-center gap-2 py-1 px-2.5 bg-slate-50 border border-slate-100 rounded-lg text-[11px] font-medium text-slate-600">
                              <Shield size={10} className="text-blue-400" />
                              {rule}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Facteurs de risque (breakdown) */}
                    {ticket.ai_risk_factors && Object.keys(ticket.ai_risk_factors).length > 0 && (
                      <div className="space-y-3 pt-2">
                        <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest">Analyse granulaire des points de risque :</div>
                        <div className="grid grid-cols-1 gap-2">
                          {Object.entries(ticket.ai_risk_factors)
                            .sort(([, a], [, b]) => Math.abs(b[0]) - Math.abs(a[0]))
                            .map(([key, [pts, desc]]) => (
                              <div key={key} className="flex items-center gap-4 bg-[#F8FAFC]/50 p-2 rounded-lg border border-transparent hover:border-slate-200 transition-all">
                                <div className={`w-12 text-right shrink-0 font-black text-sm ${pts > 0 ? 'text-red-500' : 'text-emerald-600'}`}>
                                  {pts > 0 ? `+${pts}` : pts}
                                </div>
                                <div className="flex-1">
                                  <div className="text-[11px] font-bold text-[#1E2937]">{desc}</div>
                                  <div className="h-1 mt-1 rounded-full bg-slate-100 overflow-hidden">
                                    <div
                                      className={`h-full rounded-full transition-all duration-1000 ${pts > 40 ? 'bg-red-500' : pts > 20 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                      style={{ width: `${Math.min(Math.abs(pts), 60) * 1.6}%` }}
                                    />
                                  </div>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-xl text-center italic text-[#64748B] text-sm">
                    En attente d'analyse structurée...
                  </div>
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

          {/* ── PROFIL GÉNÉRÉ (Si approuvé) ──────────────────────────────────────────────── */}
          {generatedProfile && (
            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-6 border border-emerald-200 shadow-sm mb-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Key size={100} className="text-emerald-500" />
              </div>
              <div className="flex items-center justify-between mb-5 relative z-10">
                 <h2 className="text-xl font-bold text-emerald-900 flex items-center gap-3">
                    <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700">
                      <Key size={24} />
                    </div>
                    Habilitation Créée Automatiquement
                 </h2>
                 <Badge className="bg-emerald-600 text-white font-bold tracking-wider py-1 px-3">
                   COMPTE ACTIF
                 </Badge>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-5 bg-white/60 backdrop-blur-sm rounded-xl border border-emerald-100/50 shadow-inner relative z-10">
                 <div>
                    <div className="text-[10px] font-black text-emerald-800/60 uppercase tracking-widest mb-1">Compte Généré</div>
                    <div className="font-mono text-base font-bold text-emerald-900 flex items-center gap-2">
                      {generatedProfile.account_name}
                    </div>
                 </div>
                 <div>
                    <div className="text-[10px] font-black text-emerald-800/60 uppercase tracking-widest mb-1">Système Cible</div>
                    <div className="text-sm font-bold text-[#1E2937]">{generatedProfile.system_name}</div>
                 </div>
                 <div>
                    <div className="text-[10px] font-black text-emerald-800/60 uppercase tracking-widest mb-1">Application</div>
                    <div className="text-sm font-bold text-[#1E2937]">{generatedProfile.application}</div>
                 </div>
                 <div>
                    <div className="text-[10px] font-black text-emerald-800/60 uppercase tracking-widest mb-1">Notification Email</div>
                    <div className="text-sm font-bold text-emerald-600 flex items-center gap-1.5">
                      <CheckCircle size={16}/> {generatedProfile.notification_sent ? 'Envoyée à l\'employé' : 'En attente'}
                    </div>
                 </div>
              </div>
            </div>
          )}

          {/* Accès demandés */}
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm hover:shadow-md transition-shadow uppercase-headers">
            <h2 className="text-xl font-bold text-[#1E2937] mb-6 flex items-center gap-3">
              <div className="p-2 bg-[#F8FAFC] rounded-lg text-[#003087] border border-[#E2E8F0]">
                <ShieldCheck size={24} />
              </div>
              Détails techniques de l'accès
            </h2>
            <div className="space-y-6">
              <div className="p-5 bg-[#F8FAFC] rounded-2xl border border-[#E2E8F0] relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                  <Database size={64} />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-3">Privilèges requis :</div>
                    <div className="flex gap-2 flex-wrap">
                      {ticket.requested_access_details?.access_types?.map((type, idx) => (
                        <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-white border border-blue-100 text-blue-800 rounded-xl text-xs font-black shadow-sm">
                          <Key size={12} className="text-blue-400" />
                          {type}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-3">Application cible :</div>
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#003087] text-white rounded-xl text-sm font-bold shadow-md">
                      <Cpu size={16} />
                      {ticket.requested_access_details?.application || 'Standard'}
                    </div>
                  </div>
                </div>

                <div className="mt-8">
                  <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-3">Contexte & Justification métier :</div>
                  <div className="p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-slate-100 text-sm text-[#1E2937] leading-relaxed italic">
                    {ticket.requested_access_details?.justification || "Aucune justification détaillée fournie par l'utilisateur."}
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between pt-6 border-t border-slate-200">
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black text-[#64748B] uppercase tracking-widest">Criticité Déclarée</span>
                      <span className="font-bold text-sm text-[#1E2937]">{ticket.requested_access_details?.criticite || 'BASE'}</span>
                    </div>
                    <div className="w-px h-8 bg-slate-200"></div>
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black text-[#64748B] uppercase tracking-widest">Séniorité</span>
                      <span className="font-bold text-sm text-[#1E2937] capitalize">{ticket.requested_access_details?.user_seniority || 'non précisée'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-5 bg-slate-50 rounded-2xl border border-dashed border-slate-300">
                <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-2 flex items-center gap-2">
                  <FileCode size={14} /> Description textuelle brute (iTop) :
                </div>
                <p className="text-xs text-slate-500 font-medium leading-relaxed">
                  {ticket.description}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Colonne latérale - Actions */}
        <div className="lg:sticky lg:top-24 space-y-6 self-start lg:h-fit">
          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="text-lg font-bold text-[#1E2937] mb-4 flex items-center gap-2">
              <Shield size={18} className="text-[#003087]" />
              Actions de Décision
            </h3>
            <div className="space-y-4">
              {(ticket.status === 'NEW' || ticket.status === 'ASSIGNED') && userCanAct && (
                <>
                  <button 
                    onClick={handleApprove} 
                    disabled={actionLoading} 
                    className="w-full py-4 bg-[#003087] text-white rounded-xl font-black hover:bg-[#002066] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg shadow-blue-100 uppercase tracking-wider text-sm"
                  >
                    <CheckCircle size={20} /> {actionLoading ? 'Traitement...' : 'Approuver Demande'}
                  </button>
                  <button 
                    onClick={() => setShowRejectModal(true)} 
                    disabled={actionLoading} 
                    className="w-full py-3 bg-white text-[#EF4444] border-2 border-[#EF4444] rounded-xl font-bold hover:bg-[#EF4444] hover:text-white transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 uppercase tracking-wider text-xs"
                  >
                    <XCircle size={18} /> Rejeter la demande
                  </button>
                  
                  {/* Recommandation IA */}
                  {(ticket.ai_recommended_action || ticket.classification?.recommended_action) && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-2xl border border-blue-100 relative overflow-hidden group">
                      <div className="absolute -right-2 -top-2 opacity-5 group-hover:opacity-10 transition-opacity">
                        <Brain size={64} />
                      </div>
                      <div className="flex items-start gap-3 relative z-10">
                        <div className="p-2 bg-white rounded-lg shadow-sm text-blue-600">
                          <Brain size={18} />
                        </div>
                        <div>
                          <div className="text-[10px] font-black text-blue-800 uppercase tracking-widest leading-tight">Recommandation IA</div>
                          <div className="text-sm font-black text-blue-900 mt-1">
                            {(() => {
                              const action = ticket.ai_recommended_action || ticket.classification?.recommended_action;
                              switch(action) {
                                case 'AUTO_APPROVE': return 'Approbation de routine';
                                case 'BLOCK': return 'Blocage de sécurité requis';
                                case 'MANUAL_REVIEW': return 'Revue manuelle approfondie';
                                default: return action;
                              }
                            })()}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              {(ticket.status === 'NEW' || ticket.status === 'ASSIGNED') && !userCanAct && (
                <div className="p-6 bg-slate-50 rounded-2xl text-center border border-slate-200 border-dashed">
                  <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
                    <Shield size={24} />
                  </div>
                  <p className="text-[#1E2937] font-bold text-sm">Action Restreinte</p>
                  <p className="text-slate-500 text-xs mt-1">Ce ticket est assigné au rôle :</p>
                  <Badge className="mt-2 bg-[#003087] text-white border-0 font-black px-3 py-1">
                    {ticket.assigned_to === 'SUPER_ADMIN' ? 'SUPER ADMIN' : ticket.assigned_to?.includes('ADMIN') ? 'ADMINISTRATEUR' : 'EN ATTENTE'}
                  </Badge>
                </div>
              )}
              {ticket.status === 'APPROVED' && (
                <div className="p-6 bg-emerald-50 rounded-2xl text-center border border-emerald-100">
                  <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600 shadow-inner">
                    <CheckCircle size={32} />
                  </div>
                  <p className="text-emerald-900 font-black uppercase tracking-widest text-sm">Demande Approuvée</p>
                  <p className="text-emerald-700/70 text-xs mt-2 font-medium">Les accès ont été synchronisés et provisionnés.</p>
                </div>
              )}
              {ticket.status === 'REJECTED' && (
                <div className="p-6 bg-red-50 rounded-2xl text-center border border-red-100">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 text-red-600 shadow-inner">
                    <XCircle size={32} />
                  </div>
                  <p className="text-red-900 font-black uppercase tracking-widest text-sm">Demande Rejetée</p>
                  <p className="text-red-700/70 text-xs mt-2 font-medium">Le demandeur a été notifié du motif de refus.</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm relative overflow-hidden">
            <h3 className="text-lg font-bold text-[#1E2937] mb-6 flex items-center gap-2">
              <Clock size={20} className="text-[#64748B]" />
              Fil d'audit du ticket
            </h3>
            <div className="space-y-0 relative">
              <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-gradient-to-b from-[#003087] via-[#E2E8F0] to-transparent"></div>
              {historique.map((event, idx) => (
                <div key={event.id} className="relative pl-10 pb-8 last:pb-0 group">
                  <div className={`absolute left-0 top-1 w-6 h-6 rounded-full border-4 border-white shadow-md flex items-center justify-center z-10 transition-transform group-hover:scale-110 ${
                    idx === 0 ? 'bg-[#003087] animate-pulse-subtle' : 'bg-[#E2E8F0]'
                  }`}>
                    {idx === 0 && <CheckCircle size={10} className="text-white" />}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-[#94A3B8] uppercase tracking-widest">{new Date(event.date).toLocaleString('fr-FR')}</span>
                    <span className="font-black text-[#1E2937] text-sm mt-1 group-hover:text-[#003087] transition-colors">{event.action}</span>
                    <div className="text-xs text-[#64748B] mt-2 bg-[#F8FAFC] p-3 rounded-xl border border-[#F1F5F9] group-hover:border-[#E2E8F0] transition-colors">
                      <div className="flex items-center gap-1.5 mb-1">
                        <User size={10} />
                        <span className="font-black text-[#003087] uppercase text-[9px] tracking-widest">{event.acteur}</span>
                      </div>
                      {event.details}
                    </div>
                  </div>
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