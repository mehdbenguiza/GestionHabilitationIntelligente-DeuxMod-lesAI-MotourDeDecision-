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
  is_anomalous?: boolean;
  anomaly_severity?: string;
  anomaly_score?: number;
  anomaly_flags?: string[];
  source?: string;
  employee_submitted_at?: string;
  classification?: {
    predicted_level: string;
    confidence: number;
    probabilities: Record<string, number>;
    explanation: string;
    risk_factors: Record<string, [number, string]>;
    source: string;
    decision_source: string;
    consistency_status: string;
    consistency_message: string;
    triggered_rules: string[];
    risk_score_rules: number;
    recommended_action: string;
    confidence_level_label: string;
    shap_values?: Record<string, number>;
    nlp_score?: number;
    nlp_label?: string;
    trust_modifier?: number;
    trust_label?: string;
    trust_score?: number;
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

  // V3.0 MFA Modal
  const [showMfaModal, setShowMfaModal] = useState(false);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaLoading, setMfaLoading] = useState(false);
  const [mfaErrorMsg, setMfaErrorMsg] = useState('');
  const [mfaHint, setMfaHint] = useState('');
  const [mfaCooldown, setMfaCooldown] = useState(0);

  // Timer pour le renvoi MFA
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (mfaCooldown > 0) {
      timer = setTimeout(() => setMfaCooldown(mfaCooldown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [mfaCooldown]);

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
      
      // V3.0 : Si le backend réclame le MFA (428 Precondition Required)
      if (response.status === 428) {
        // Demander automatiquement la génération du code
        const reqMfa = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/request-mfa`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (reqMfa.ok) {
           const mfaData = await reqMfa.json();
           setMfaHint(mfaData.hint || 'Code envoyé.');
           setMfaCooldown(60); // 60 secondes de cooldown
           setShowMfaModal(true);
           return;
        } else {
           throw new Error('Impossible de générer le code MFA.');
        }
      }

      if (!response.ok) {
        const d = await response.json().catch(()=>({}));
        throw new Error(d?.detail?.message || 'Erreur lors de l\'approbation');
      }
      await fetchTicket();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResendMfa = async () => {
    if (!ticket || mfaCooldown > 0) return;
    setMfaErrorMsg('');
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/request-mfa`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const mfaData = await response.json();
        setMfaHint(mfaData.hint || 'Code envoyé.');
        setMfaCooldown(60);
      } else {
        throw new Error('Erreur lors du renvoi du code.');
      }
    } catch (err) {
      setMfaErrorMsg(err instanceof Error ? err.message : 'Erreur réseau.');
    }
  };

  const submitMfaApprove = async () => {
    if (!ticket || !mfaCode) return;
    setMfaLoading(true);
    setMfaErrorMsg('');
    try {
      const response = await fetch(`http://127.0.0.1:8000/tickets/${ticket.id}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution: 'Demande approuvée après validation MFA', mfa_code: mfaCode })
      });
      
      if (!response.ok) {
        const d = await response.json();
        throw new Error(d?.detail?.message || 'Code invalide');
      }
      setShowMfaModal(false);
      setMfaCode('');
      await fetchTicket();
    } catch (err) {
      setMfaErrorMsg(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setMfaLoading(false);
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

              {/* ── Modèle 2 : Anomalies Comportementales ── */}
              {ticket.is_anomalous && (
                <div className="bg-amber-50 rounded-xl p-4 border border-amber-200 shadow-sm mt-4">
                  <div className="text-[10px] font-black text-amber-800 uppercase tracking-widest mb-2 flex items-center gap-1">
                    <AlertTriangle size={12}/> Anomalie Comportementale Détectée
                  </div>
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-amber-900 font-medium">Sévérité :</span>
                      <Badge className="bg-amber-200 text-amber-900 border-amber-300 font-bold uppercase">{ticket.anomaly_severity}</Badge>
                    </div>
                    {ticket.anomaly_flags && ticket.anomaly_flags.length > 0 && (
                      <div className="mt-1">
                        <span className="text-xs text-amber-800 font-semibold">Signaux détectés :</span>
                        <ul className="list-disc list-inside text-xs text-amber-700 mt-1 space-y-0.5">
                          {ticket.anomaly_flags.map((flag, idx) => {
                            const parts = flag.split(':');
                            const name = parts[0].replace('ANOMALY_', '').replace(/_/g, ' ');
                            const detail = parts[1] ? ` (${parts[1]})` : '';
                            return <li key={idx}><span className="font-semibold">{name}</span>{detail}</li>;
                          })}
                        </ul>
                      </div>
                    )}
                    {ticket.anomaly_score !== undefined && ticket.anomaly_score !== null && (
                      <div className="flex justify-between items-center mt-1 border-t border-amber-200/50 pt-2">
                        <span className="text-xs text-amber-800 font-semibold">Score Isolation Forest :</span>
                        <span className="text-xs font-mono font-bold text-amber-900">{ticket.anomaly_score.toFixed(3)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ── V3.0 : Analyse Sémantique NLP & Trust Score ── */}
              {(ticket.classification?.nlp_score !== undefined || ticket.classification?.trust_score !== undefined) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  {ticket.classification?.nlp_score !== undefined && (
                    <div className="bg-white rounded-xl p-4 border border-indigo-100 shadow-sm">
                      <div className="text-[10px] font-black text-indigo-800 uppercase tracking-widest mb-1 flex items-center gap-1"><Sparkles size={12}/> Sémantique NLP</div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-sm">{ticket.classification.nlp_label}</span>
                        <span className="font-bold text-indigo-600">{ticket.classification.nlp_score}/100</span>
                      </div>
                      <Progress value={ticket.classification.nlp_score} className="h-1.5" />
                    </div>
                  )}
                  {ticket.classification?.trust_score !== undefined && (
                    <div className="bg-white rounded-xl p-4 border border-teal-100 shadow-sm">
                      <div className="text-[10px] font-black text-teal-800 uppercase tracking-widest mb-1 flex items-center gap-1"><ShieldCheck size={12}/> Trust Score Employé</div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-sm">{ticket.classification.trust_label}</span>
                        <span className="font-bold text-teal-600">{ticket.classification.trust_score}/100</span>
                      </div>
                      <Progress value={ticket.classification.trust_score} className="h-1.5" />
                    </div>
                  )}
                </div>
              )}

              {/* ── V3.0 : SHAP Values explainability ── */}
              {ticket.classification?.shap_values && (
                <div className="mt-4 p-4 bg-white/60 border border-purple-100 rounded-xl space-y-3">
                  <div className="text-[10px] font-black text-purple-800 uppercase tracking-widest flex items-center gap-1">
                     <Brain size={12}/> Contribution des Signaux (Top 5)
                  </div>
                  <div className="space-y-2">
                    {Object.entries(ticket.classification.shap_values).map(([feature, val]) => (
                      <div key={feature} className="flex items-center gap-3">
                         <div className="w-[120px] text-xs font-mono truncate" title={feature}>{feature}</div>
                         <div className="flex-1 flex items-center">
                            {val < 0 ? (
                               <div className="flex flex-1 justify-end">
                                  <div style={{width: `${Math.min(Math.abs(val)*20, 100)}%`}} className="h-2 bg-emerald-400 rounded-l-sm" />
                               </div>
                            ) : (
                               <div className="flex-1" />
                            )}
                            <div className="w-px h-3 bg-slate-300 mx-1" />
                            {val > 0 ? (
                               <div className="flex flex-1 justify-start">
                                  <div style={{width: `${Math.min(val*20, 100)}%`}} className="h-2 bg-rose-400 rounded-r-sm" />
                               </div>
                            ) : (
                               <div className="flex-1" />
                            )}
                         </div>
                         <div className={`w-12 text-right text-xs font-bold ${val > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                           {val > 0 ? '+' : ''}{val.toFixed(2)}
                         </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── COHÉRENCE DE LA DÉCISION ── */}
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
                
                {ticket.classification?.risk_score_rules !== undefined ? (
                  <div className="space-y-6">
                    
                    {/* ── PILLIER 1 : MODÈLE ML (XGBoost/RF) ── */}
                    <div className="bg-[#F8FAFC] border border-slate-200 rounded-xl overflow-hidden">
                      <div className="bg-blue-50 border-b border-slate-200 p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><Cpu size={20} /></div>
                          <div>
                            <div className="text-[11px] font-black text-blue-500 uppercase tracking-widest">Pillier 1</div>
                            <div className="text-sm font-bold text-slate-800">Modèle de Classification Machine Learning</div>
                          </div>
                        </div>
                        <Badge className={`${getNiveauBadgeColor(ticket.classification.predicted_level)} font-bold text-xs px-3 py-1`}>
                          {ticket.classification.predicted_level}
                        </Badge>
                      </div>
                      <div className="p-4 bg-white">
                        <p className="text-sm text-slate-600 mb-4">
                          Le modèle prédictif a analysé l'historique des requêtes similaires et a défini ce niveau de base avec une 
                          certitude de <span className="font-bold text-slate-800">{ticket.ai_confidence}%</span>.
                        </p>
                        
                        {ticket.classification.probabilities && Object.keys(ticket.classification.probabilities).length > 0 && (
                          <div className="space-y-2 mt-4 border-t border-slate-100 pt-4">
                            <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-3">Probabilités par classe :</div>
                            <div className="flex flex-col gap-2">
                              {Object.entries(ticket.classification.probabilities).map(([cls, prob]) => {
                                const pVal = typeof prob === 'number' ? prob : 0;
                                return (
                                  <div key={cls} className="flex items-center gap-3">
                                    <div className="w-20 text-xs font-bold text-slate-600">{cls}</div>
                                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                                      <div 
                                        className={`h-full rounded-full ${cls === 'CRITICAL' ? 'bg-red-400' : cls === 'SENSITIVE' ? 'bg-amber-400' : 'bg-emerald-400'}`} 
                                        style={{ width: `${pVal * 100}%` }}
                                      />
                                    </div>
                                    <div className="w-12 text-right text-[10px] font-bold text-slate-500">{(pVal * 100).toFixed(1)}%</div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* ── PILLIER 2 : RÈGLES MÉTIER & EXPERTISE ── */}
                    <div className="bg-[#F8FAFC] border border-slate-200 rounded-xl overflow-hidden">
                      <div className="bg-emerald-50 border-b border-slate-200 p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><Shield size={20} /></div>
                          <div>
                            <div className="text-[11px] font-black text-emerald-500 uppercase tracking-widest">Pillier 2</div>
                            <div className="text-sm font-bold text-slate-800">Moteur de Règles Métier & Analyse Sémantique</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-500">Score calculé :</span>
                          <span className={`text-lg font-black ${ticket.classification.risk_score_rules > 80 ? 'text-red-600' : 'text-emerald-600'}`}>
                            {ticket.classification.risk_score_rules} pts
                          </span>
                        </div>
                      </div>
                      <div className="p-4 bg-white space-y-5">
                        
                        {ticket.classification.triggered_rules && ticket.classification.triggered_rules.length > 0 && (
                          <div>
                            <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-2">Règles métier déclenchées :</div>
                            <div className="flex flex-wrap gap-2">
                              {ticket.classification.triggered_rules.map((rule, ri) => (
                                <div key={ri} className="flex items-center gap-2 py-1 px-2.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-medium text-slate-600">
                                  <Shield size={10} className="text-emerald-400" />
                                  {rule}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {ticket.ai_risk_factors && Object.keys(ticket.ai_risk_factors).length > 0 && (
                          <div className="border-t border-slate-100 pt-4">
                            <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest mb-3">Détail des points additionnés :</div>
                            <div className="grid grid-cols-1 gap-1.5">
                              {Object.entries(ticket.ai_risk_factors)
                                .filter(([key]) => key !== 'ANOMALY_BOOST') // On masque l'anomalie ici pour la mettre dans le pilier 3
                                .sort(([, a], [, b]) => Math.abs(b[0]) - Math.abs(a[0]))
                                .map(([key, [pts, desc]]) => (
                                  <div key={key} className="flex items-center gap-3 p-1.5 hover:bg-slate-50 rounded transition-colors">
                                    <div className={`w-10 text-right font-black text-xs ${pts > 0 ? 'text-red-500' : 'text-emerald-600'}`}>
                                      {pts > 0 ? `+${pts}` : pts}
                                    </div>
                                    <div className="text-xs font-medium text-slate-700">{desc}</div>
                                  </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* ── PILLIER 3 : ANOMALIES COMPORTEMENTALES ── */}
                    <div className="bg-[#F8FAFC] border border-slate-200 rounded-xl overflow-hidden">
                      <div className="bg-amber-50 border-b border-slate-200 p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-amber-100 text-amber-600 rounded-lg"><AlertTriangle size={20} /></div>
                          <div>
                            <div className="text-[11px] font-black text-amber-500 uppercase tracking-widest">Pillier 3</div>
                            <div className="text-sm font-bold text-slate-800">Modèle d'Anomalie Comportementale (Isolation Forest)</div>
                          </div>
                        </div>
                        <Badge className={`${ticket.is_anomalous ? 'bg-amber-200 text-amber-900 border-amber-300' : 'bg-slate-200 text-slate-600 border-slate-300'} font-bold text-xs px-3 py-1`}>
                          {ticket.anomaly_severity || 'AUCUNE'}
                        </Badge>
                      </div>
                      <div className="p-4 bg-white">
                        
                        {ticket.is_anomalous ? (
                          <div className="space-y-4">
                            <p className="text-sm text-slate-600">
                              Le modèle d'anomalie a détecté un comportement suspect basé sur l'heure, le jour de soumission, ou un volume inhabituel.
                              {ticket.anomaly_score !== null && ticket.anomaly_score !== undefined && (
                                <span className="ml-1 font-semibold text-slate-800">Score d'anomalie (IF) : {ticket.anomaly_score.toFixed(3)}</span>
                              )}
                            </p>
                            
                            {ticket.anomaly_flags && ticket.anomaly_flags.length > 0 && (
                              <div className="space-y-2">
                                <div className="text-[10px] font-black text-[#64748B] uppercase tracking-widest">Signaux détectés :</div>
                                <div className="flex flex-col gap-2">
                                  {ticket.anomaly_flags.map((flag, idx) => (
                                    <div key={idx} className="flex items-center gap-2 text-xs font-medium text-amber-800 bg-amber-50/50 p-2 rounded border border-amber-100">
                                      <AlertTriangle size={12} className="text-amber-500" />
                                      {flag.replace('ANOMALY_', '').replace(/_/g, ' ')}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {ticket.ai_risk_factors && ticket.ai_risk_factors['ANOMALY_BOOST'] && (
                              <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-600">Impact sur le score final :</span>
                                <span className="text-sm font-black text-red-500">+{ticket.ai_risk_factors['ANOMALY_BOOST'][0]} pts</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500 italic text-center py-2">
                            Aucune anomalie comportementale ou temporelle n'a été détectée lors de la soumission de cette demande.
                          </p>
                        )}
                        
                      </div>
                    </div>
                    
                    {/* SCORE FINAL */}
                    <div className="flex flex-col gap-3 bg-white shadow-md p-5 rounded-xl border border-slate-200 mt-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <div className={`text-center font-black text-3xl leading-none ${ticket.classification!.risk_score_rules > 80 ? 'text-red-600' : 'text-emerald-600'}`}>
                            {ticket.classification!.risk_score_rules}
                          </div>
                          <div className="text-[9px] font-bold text-slate-400 mt-1.5 uppercase tracking-widest text-center">Points</div>
                        </div>
                        <div className="flex-1">
                          <div className="text-lg font-black text-[#1E2937] uppercase tracking-tight flex items-center gap-2">
                            Score Final Calculé
                          </div>
                          <div className="text-xs font-medium text-slate-500 mt-1">
                            Calcul mathématique détaillé de la décision IA (Formule de fusion) :
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-sm overflow-x-auto whitespace-nowrap flex items-center gap-2 mt-2">
                        <span className="font-bold text-slate-400">0</span>
                        <span className="text-slate-400 font-bold px-1">+</span>
                        {Object.entries(ticket.ai_risk_factors || {})
                          .sort(([, a], [, b]) => Math.abs(b[0]) - Math.abs(a[0]))
                          .map(([key, [pts, desc]], idx, arr) => (
                            <span key={key} className="flex items-center">
                              <span className={`font-bold px-1.5 py-0.5 rounded ${pts > 0 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                {pts > 0 ? `+${pts}` : pts}
                              </span>
                              <span className="text-[10px] text-slate-500 ml-1.5 mr-1 font-sans font-semibold uppercase tracking-wider">
                                ({key === 'ANOMALY_BOOST' ? 'Anomalie' : key === 'nlp_ana' ? 'NLP' : key === 'trust_ana' ? 'Trust' : 'Règle'})
                              </span>
                              {idx < arr.length - 1 && <span className="text-slate-400 font-bold mx-2">+</span>}
                            </span>
                        ))}
                        
                        {(() => {
                          const rawSum = Object.values(ticket.ai_risk_factors || {}).reduce((acc, curr) => acc + curr[0], 0);
                          const finalScore = ticket.classification!.risk_score_rules;
                          
                          if (rawSum !== finalScore) {
                            return (
                              <>
                                <span className="text-slate-400 font-bold px-3">=</span>
                                <span className="font-bold text-slate-400 line-through mr-2">{rawSum}</span>
                                <span className="text-slate-400 font-bold italic text-xs mr-2">
                                  (Plafonné à {finalScore === 200 ? '200 max' : '0 min'}) ➜
                                </span>
                                <span className={`font-black text-lg px-3 py-1 rounded shadow-sm ${finalScore > 80 ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'}`}>
                                  {finalScore} pts
                                </span>
                              </>
                            );
                          } else {
                            return (
                              <>
                                <span className="text-slate-400 font-bold px-3">=</span>
                                <span className={`font-black text-lg px-3 py-1 rounded shadow-sm ${finalScore > 80 ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'}`}>
                                  {finalScore} pts
                                </span>
                              </>
                            );
                          }
                        })()}
                      </div>
                    </div>

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

      {/* ── Modal d'Approbation Sécurisée (MFA) — V3.0 ── */}
      {showMfaModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 border border-slate-100 animate-fade-in text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600">
              <Key size={32} />
            </div>
            
            <h2 className="text-xl font-bold text-[#1E2937] mb-2">Vérification de Sécurité Requise</h2>
            <p className="text-sm text-slate-500 mb-6">Ce ticket a été classifié comme <strong>CRITIQUE</strong>. Une étape de vérification supplémentaire (MFA) est requise.</p>
            
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6 text-left">
              <p className="text-xs text-slate-500 font-medium mb-3 flex items-center gap-2"><AlertCircle size={14}/> {mfaHint}</p>
              <input
                type="text"
                placeholder="Ex. 482915"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value.replace(/[^0-9]/g, '').substring(0, 6))}
                className="w-full h-12 text-center text-2xl tracking-[0.5em] font-black border border-slate-200 bg-white rounded-xl text-[#003087] focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
              {mfaErrorMsg && <p className="text-red-500 text-xs font-bold mt-2 text-center">{mfaErrorMsg}</p>}
            </div>

            {/* Bouton Renvoyer le code */}
            <div className="mb-6 text-center">
              <button 
                onClick={handleResendMfa}
                disabled={mfaCooldown > 0}
                className={`text-sm text-center font-bold ${mfaCooldown > 0 ? 'text-slate-400 cursor-not-allowed' : 'text-[#003087] hover:underline'}`}
              >
                {mfaCooldown > 0 ? `Renvoyer le code (${mfaCooldown}s)` : 'Je n\'ai pas reçu le code'}
              </button>
            </div>

            <div className="flex gap-3">
              <button onClick={() => {setShowMfaModal(false); setMfaCode('');}} disabled={mfaLoading} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-50 rounded-xl transition-colors bg-white border border-slate-200">
                Annuler
              </button>
              <button onClick={submitMfaApprove} disabled={mfaLoading || mfaCode.length < 6} className="flex-1 py-3 bg-[#003087] text-white font-bold rounded-xl shadow-md hover:bg-[#002066] disabled:opacity-50">
                {mfaLoading ? 'Validation...' : 'Valider'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}