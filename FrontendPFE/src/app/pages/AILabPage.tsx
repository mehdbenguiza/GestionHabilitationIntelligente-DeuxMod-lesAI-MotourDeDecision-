import { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical, Zap, BarChart3, RefreshCw, ThumbsUp, ThumbsDown,
  Brain, Users, TrendingUp, AlertTriangle, CheckCircle2, Layers,
  Play, Cpu, BookOpen, Trash2, ChevronDown, ChevronUp, Shield
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Badge } from '../components/ui/badge';

const API = 'http://127.0.0.1:8000';

interface GeneratedTicket {
  id: number;
  ref: string;
  employee_name: string;
  team: string;
  role: string;
  application: string;
  environments: string[];
  ai_classification: {
    level: string;
    confidence: number;
    probabilities: { BASE: number; SENSITIVE: number; CRITICAL: number };
    assigned_to: string;
  };
}

interface FeedbackStats {
  total_votes: number;
  likes: number;
  dislikes: number;
  satisfaction_rate: number;
  corrections_count: number;
  corrections_applied: number;
}

interface Correction {
  id: number;
  application: string;
  environment: string;
  access_type: string;
  team: string;
  resource: string;
  corrected_level: string;
  corrected_reason: string;
  reviewer: string;
  usage_count: number;
  created_at: string;
  last_used_at: string | null;
}

interface RetrainHistory {
  date: string;
  total_tickets: number;
  human_tickets: number;
  accuracy: number;
  cv_mean: number;
  cv_std: number;
}

const levelColor = (l: string) =>
  l === 'CRITICAL' ? '#EF4444' : l === 'SENSITIVE' ? '#F59E0B' : '#10B981';

const levelBg = (l: string) =>
  l === 'CRITICAL'
    ? 'bg-red-100 text-red-800 border-red-300'
    : l === 'SENSITIVE'
    ? 'bg-amber-100 text-amber-800 border-amber-300'
    : 'bg-green-100 text-green-800 border-green-300';

const levelFr = (l: string) =>
  l === 'CRITICAL' ? 'Critique' : l === 'SENSITIVE' ? 'Sensible' : 'Base';

export function AILabPage() {
  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // ── State ────────────────────────────────────────────────────────────────
  const [userRole, setUserRole]           = useState('');
  const [generated, setGenerated]         = useState<GeneratedTicket[]>([]);
  const [batchCount, setBatchCount]       = useState(5);
  const [generating, setGenerating]       = useState(false);
  const [retraining, setRetraining]       = useState(false);
  const [retrainOutput, setRetrainOutput] = useState('');
  const [retrainHistory, setRetrainHistory] = useState<RetrainHistory[]>([]);
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);
  const [corrections, setCorrections]     = useState<Correction[]>([]);
  const [showCorrections, setShowCorrections] = useState(false);
  const [employeeStats, setEmployeeStats] = useState<any>(null);
  const [activeTab, setActiveTab]         = useState<'generate' | 'corrections' | 'retrain'>('generate');
  const [loading, setLoading]             = useState(true);

  // ── Init ────────────────────────────────────────────────────────────────
  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [meRes, statsRes, histRes, corrRes, empRes] = await Promise.all([
        fetch(`${API}/users/me`, { headers }),
        fetch(`${API}/feedback/stats/summary`, { headers }),
        fetch(`${API}/ai/retrain/history`, { headers }),
        fetch(`${API}/feedback/corrections/list`, { headers }),
        fetch(`${API}/employees/stats`, { headers }),
      ]);

      if (meRes.ok) { const d = await meRes.json(); setUserRole(d.role); }
      if (statsRes.ok) setFeedbackStats(await statsRes.json());
      if (histRes.ok) setRetrainHistory(await histRes.json());
      if (corrRes.ok) setCorrections(await corrRes.json());
      if (empRes.ok) setEmployeeStats(await empRes.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  // ── Génération de tickets ───────────────────────────────────────────────
  const generateOne = async () => {
    setGenerating(true);
    console.log('🚀 Simulation: Génération d\'un ticket...');
    try {
      const r = await fetch(`${API}/tickets/simulate/create?v=2`, { method: 'POST', headers });
      if (r.ok) {
        const d = await r.json();
        console.log('✅ Ticket reçu:', d.ticket);
        if (d.ticket) {
          setGenerated(prev => [d.ticket, ...prev].slice(0, 50));
        } else {
          console.error('❌ Format de réponse invalide (ticket manquant):', d);
        }
      } else {
        const err = await r.json();
        console.error('❌ Erreur simulation:', err);
        alert('Erreur lors de la génération : ' + (err.detail || 'Erreur serveur'));
      }
    } catch (e) {
      console.error('❌ Erreur réseau simulation:', e);
      alert('Impossible de contacter le serveur pour la simulation.');
    } finally { setGenerating(false); }
  };

  const generateBatch = async () => {
    setGenerating(true);
    console.log(`🚀 Simulation: Génération de ${batchCount} tickets...`);
    try {
      const r = await fetch(`${API}/tickets/simulate/batch/${batchCount}?v=2`, { method: 'POST', headers });
      if (r.ok) {
        const d = await r.json();
        console.log('✅ Tickets reçus:', d.tickets?.length);
        if (d.tickets) {
          setGenerated(prev => [...d.tickets, ...prev].slice(0, 50));
        }
      } else {
        const err = await r.json();
        console.error('❌ Erreur batch:', err);
        alert('Erreur batch : ' + (err.detail || 'Erreur serveur'));
      }
    } catch (e) {
      console.error('❌ Erreur réseau batch:', e);
    } finally {
      setGenerating(false);
      loadAll();
    }
  };

  // ── Rétro-entraînement ───────────────────────────────────────────────────
  const triggerRetrain = async () => {
    setRetraining(true);
    setRetrainOutput('⏳ Rétro-entraînement en cours...\n');
    try {
      const r = await fetch(`${API}/ai/retrain`, { method: 'POST', headers });
      const d = await r.json();
      if (r.ok) {
        setRetrainOutput('✅ ' + d.message + '\n\n' + (d.output || ''));
        await loadAll();
      } else {
        setRetrainOutput('❌ Erreur : ' + (d.detail || JSON.stringify(d)));
      }
    } catch (e) {
      setRetrainOutput('❌ Erreur réseau : ' + e);
    } finally { setRetraining(false); }
  };

  const deleteCorrection = async (id: number) => {
    await fetch(`${API}/feedback/corrections/${id}`, { method: 'DELETE', headers });
    setCorrections(prev => prev.filter(c => c.id !== id));
  };

  // ── Statistiques générées ────────────────────────────────────────────────
  const levelStats = generated.reduce(
    (acc, t) => {
      const l = t.ai_classification?.level || 'UNKNOWN';
      acc[l] = (acc[l] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  const pieData = Object.entries(levelStats).map(([name, value]) => ({
    name: levelFr(name), value, color: levelColor(name),
  }));

  const historyChartData = retrainHistory.map(h => ({
    date: new Date(h.date).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }),
    accuracy: Math.round(h.accuracy * 100),
    cv: Math.round(h.cv_mean * 100),
    tickets: h.total_tickets,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4" />
          <p className="text-gray-600">Chargement du Lab IA...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E2937] mb-1 flex items-center gap-3">
            <FlaskConical className="text-[#003087]" size={32} />
            Lab IA
          </h1>
          <p className="text-[#64748B]">
            Génération de tickets · Feedback · Rétro-entraînement du modèle
          </p>
        </div>
        <button onClick={loadAll} className="p-2 hover:bg-white rounded-lg transition-colors" title="Actualiser">
          <RefreshCw size={20} className="text-[#64748B]" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Layers, label: 'Tickets générés', value: generated.length, color: 'text-[#003087]', bg: 'bg-blue-50' },
          { icon: ThumbsUp, label: 'Taux de satisfaction', value: feedbackStats ? `${feedbackStats.satisfaction_rate}%` : '—', color: 'text-green-600', bg: 'bg-green-50' },
          { icon: BookOpen, label: 'Corrections actives', value: corrections.length, color: 'text-amber-600', bg: 'bg-amber-50' },
          { icon: Cpu, label: 'Corrections appliquées', value: feedbackStats?.corrections_applied || 0, color: 'text-purple-600', bg: 'bg-purple-50' },
        ].map(({ icon: Icon, label, value, color, bg }) => (
          <div key={label} className="bg-white rounded-xl p-5 border border-[#E2E8F0] shadow-sm">
            <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mb-3`}>
              <Icon size={20} className={color} />
            </div>
            <div className="text-2xl font-bold text-[#1E2937]">{value}</div>
            <div className="text-sm text-[#64748B] mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[#E2E8F0]">
        {([
          { id: 'generate', label: 'Génération', icon: Zap },
          { id: 'corrections', label: `Corrections (${corrections.length})`, icon: BookOpen },
          { id: 'retrain', label: 'Rétro-entraînement', icon: Brain },
        ] as const).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium text-sm border-b-2 transition-colors -mb-px ${
              activeTab === id
                ? 'border-[#003087] text-[#003087]'
                : 'border-transparent text-[#64748B] hover:text-[#1E2937]'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB: GÉNÉRATION ─────────────────────────────────────────────── */}
      {activeTab === 'generate' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Panneau gauche */}
          <div className="space-y-4">
            {/* Employés */}
            {employeeStats && (
              <div className="bg-white rounded-xl p-5 border border-[#E2E8F0] shadow-sm">
                <h3 className="font-bold text-[#1E2937] mb-3 flex items-center gap-2">
                  <Users size={18} className="text-[#003087]" /> Employés dans la DB
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-[#003087]">{employeeStats.total}</div>
                    <div className="text-xs text-[#64748B]">Total</div>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-amber-600">{employeeStats.juniors}</div>
                    <div className="text-xs text-[#64748B]">Juniors</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">{employeeStats.seniors}</div>
                    <div className="text-xs text-[#64748B]">Seniors</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Object.keys(employeeStats.by_team || {}).length}
                    </div>
                    <div className="text-xs text-[#64748B]">Équipes</div>
                  </div>
                </div>
                <p className="text-xs text-[#64748B] mt-3 leading-relaxed">
                  🔵 <strong>Junior</strong> → génère des accès plus risqués (PRD, DELETE) <br/>
                  🟢 <strong>Senior</strong> → génère des accès modérés (DEV, READ)
                </p>
              </div>
            )}

            {/* Contrôles */}
            <div className="bg-white rounded-xl p-5 border border-[#E2E8F0] shadow-sm space-y-3">
              <h3 className="font-bold text-[#1E2937] mb-1 flex items-center gap-2">
                <Play size={18} className="text-[#003087]" /> Générer des tickets
              </h3>
              <button
                onClick={generateOne}
                disabled={generating}
                className="w-full py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {generating ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
                Générer 1 ticket
              </button>

              <div className="flex gap-2 items-center">
                <input
                  type="range" min={1} max={50} value={batchCount}
                  onChange={e => setBatchCount(Number(e.target.value))}
                  className="flex-1 accent-[#003087]"
                />
                <span className="text-sm font-bold text-[#003087] w-8 text-right">{batchCount}</span>
              </div>
              <button
                onClick={generateBatch}
                disabled={generating}
                className="w-full py-2.5 bg-gradient-to-r from-[#003087] to-[#00AEEF] text-white rounded-lg font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {generating ? <RefreshCw size={16} className="animate-spin" /> : <BarChart3 size={16} />}
                Générer {batchCount} tickets en batch
              </button>

              {generated.length > 0 && (
                <button
                  onClick={() => setGenerated([])}
                  className="w-full py-2 text-sm text-[#64748B] border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
                >
                  Effacer la liste
                </button>
              )}
            </div>

            {/* Pie chart */}
            {generated.length > 0 && (
              <div className="bg-white rounded-xl p-5 border border-[#E2E8F0] shadow-sm">
                <h3 className="font-bold text-[#1E2937] mb-3">Répartition générée</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={70} dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Tableau des tickets générés */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
            <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
              <h3 className="font-bold text-[#1E2937] flex items-center gap-2">
                <Layers size={18} className="text-[#003087]" />
                Tickets générés ({generated.length})
              </h3>
              {generating && <RefreshCw size={16} className="animate-spin text-[#003087]" />}
            </div>
            {generated.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-[#64748B]">
                <FlaskConical size={48} className="mb-4 opacity-30" />
                <p className="font-medium">Aucun ticket généré</p>
                <p className="text-sm">Cliquez sur "Générer" pour commencer</p>
              </div>
            ) : (
              <div className="overflow-auto max-h-[600px]">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-[#F8FAFC] border-b border-[#E2E8F0]">
                    <tr>
                      {['Réf.', 'Employé', 'Équipe', 'Appli', 'Niveau IA', 'Confiance', 'Assigné à'].map(h => (
                        <th key={h} className="text-left py-3 px-4 font-semibold text-[#64748B]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {generated.map(t => (
                      <tr key={t.ref} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors cursor-pointer"
                        onClick={() => window.open(`/ticket/${t.id}`, '_blank')}>
                        <td className="py-3 px-4 font-medium text-[#003087] whitespace-nowrap">{t.ref}</td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-[#1E2937]">{t.employee_name}</div>
                          <div className="text-xs text-[#64748B]">{t.role}</div>
                        </td>
                        <td className="py-3 px-4 text-[#64748B]">{t.team}</td>
                        <td className="py-3 px-4">
                          <Badge className="bg-blue-50 text-blue-700 border-blue-200 border text-xs">
                            {t.application}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={`${levelBg(t.ai_classification?.level)} border text-xs`}>
                            {levelFr(t.ai_classification?.level)}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`font-bold ${
                            (t.ai_classification?.confidence || 0) > 85 ? 'text-green-600' :
                            (t.ai_classification?.confidence || 0) > 65 ? 'text-amber-600' : 'text-red-600'
                          }`}>
                            {t.ai_classification?.confidence}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-[#64748B]">
                          {t.ai_classification?.assigned_to === 'SUPER_ADMIN' ? '🔴 Super Admin' :
                           t.ai_classification?.assigned_to?.includes('ADMIN') ? '🟠 Admin' : '🟢 Auto'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: CORRECTIONS ────────────────────────────────────────────── */}
      {activeTab === 'corrections' && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <BookOpen size={20} className="text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-amber-800">Bibliothèque de corrections humaines</p>
                <p className="text-sm text-amber-700 mt-1">
                  Ces corrections sont automatiquement appliquées à chaque ticket dont le profil
                  (application + environnement + type d'accès + équipe) correspond.
                  Elles sont aussi intégrées dans le prochain rétro-entraînement (×5 poids).
                </p>
              </div>
            </div>
          </div>

          {corrections.length === 0 ? (
            <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col items-center justify-center py-20 text-[#64748B]">
              <ThumbsDown size={48} className="mb-4 opacity-20" />
              <p className="font-medium">Aucune correction dans la bibliothèque</p>
              <p className="text-sm">Les corrections apparaissent quand un Super Admin dislike une classification</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
                  <tr>
                    {['Profil (Application/Env/Accès)', 'Équipe', 'Niveau corrigé', 'Raison du Super Admin', 'Utilisée', 'Actions'].map(h => (
                      <th key={h} className="text-left py-3 px-4 font-semibold text-[#64748B]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {corrections.map(c => (
                    <tr key={c.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC]">
                      <td className="py-3 px-4">
                        <div className="flex gap-1 flex-wrap">
                          <Badge className="bg-blue-50 text-blue-700 border-blue-200 border text-xs">{c.application}</Badge>
                          <Badge className="bg-gray-100 text-gray-700 border-gray-200 border text-xs">{c.environment}</Badge>
                          <Badge className="bg-orange-50 text-orange-700 border-orange-200 border text-xs">{c.access_type}</Badge>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-[#64748B]">{c.team}</td>
                      <td className="py-3 px-4">
                        <Badge className={`${levelBg(c.corrected_level)} border text-xs`}>
                          {levelFr(c.corrected_level)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-[#1E2937] max-w-xs">
                        <p className="text-xs leading-relaxed line-clamp-3">{c.corrected_reason}</p>
                        <p className="text-xs text-[#64748B] mt-1">— {c.reviewer}</p>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`font-bold ${c.usage_count > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                          {c.usage_count}×
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {userRole === 'SUPER_ADMIN' && (
                          <button onClick={() => deleteCorrection(c.id)}
                            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Supprimer la correction">
                            <Trash2 size={16} />
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
      )}

      {/* ── TAB: RÉTRO-ENTRAÎNEMENT ──────────────────────────────────────── */}
      {activeTab === 'retrain' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            {/* Déclencheur */}
            <div className="bg-gradient-to-br from-[#003087] to-[#00AEEF] rounded-xl p-6 text-white">
              <Brain size={32} className="mb-3 opacity-80" />
              <h3 className="text-lg font-bold mb-2">Rétro-entraîner le modèle</h3>
              <p className="text-sm opacity-80 mb-4">
                Le modèle sera ré-entraîné avec :
                <br />• Dataset historique (CSV)
                <br />• Tickets traités manuellement
                <br />• Corrections humaines (×5 poids)
              </p>
              {userRole === 'SUPER_ADMIN' ? (
                <button
                  onClick={triggerRetrain}
                  disabled={retraining}
                  className="w-full py-3 bg-white text-[#003087] rounded-lg font-bold hover:bg-opacity-90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {retraining ? <RefreshCw size={18} className="animate-spin" /> : <Cpu size={18} />}
                  {retraining ? 'Entraînement...' : 'Lancer le rétro-entraînement'}
                </button>
              ) : (
                <div className="bg-white bg-opacity-20 rounded-lg p-3 text-sm">
                  <Shield size={16} className="inline mr-2" />
                  Réservé aux Super Admins
                </div>
              )}
            </div>

            {/* Output console */}
            {retrainOutput && (
              <div className="bg-gray-900 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-gray-400 text-xs ml-2">Console</span>
                </div>
                <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap overflow-y-auto max-h-64">
                  {retrainOutput}
                </pre>
              </div>
            )}
          </div>

          {/* Graphe d'évolution */}
          <div className="lg:col-span-2 bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
            <h3 className="font-bold text-[#1E2937] mb-4 flex items-center gap-2">
              <TrendingUp size={18} className="text-[#003087]" />
              Évolution de la précision du modèle
            </h3>
            {historyChartData.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-[#64748B]">
                <TrendingUp size={48} className="mb-4 opacity-20" />
                <p>Aucun cycle d'entraînement enregistré</p>
                <p className="text-sm">Lancez un rétro-entraînement pour commencer</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={historyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="date" stroke="#64748B" style={{ fontSize: '12px' }} />
                  <YAxis domain={[0, 100]} stroke="#64748B" style={{ fontSize: '12px' }}
                    tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Legend />
                  <Line type="monotone" dataKey="accuracy" name="Accuracy" stroke="#003087"
                    strokeWidth={2} dot={{ r: 5 }} />
                  <Line type="monotone" dataKey="cv" name="Validation croisée" stroke="#10B981"
                    strokeWidth={2} dot={{ r: 4 }} strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            )}

            {retrainHistory.length > 0 && (
              <div className="mt-4 grid grid-cols-3 gap-4">
                {[
                  { label: 'Dernier accuracy', value: `${Math.round(retrainHistory.at(-1)!.accuracy * 100)}%`, color: 'text-[#003087]' },
                  { label: 'Tickets humains', value: retrainHistory.at(-1)!.human_tickets, color: 'text-green-600' },
                  { label: 'Total entraînement', value: retrainHistory.at(-1)!.total_tickets, color: 'text-[#64748B]' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-[#F8FAFC] rounded-lg p-3 text-center">
                    <div className={`text-xl font-bold ${color}`}>{value}</div>
                    <div className="text-xs text-[#64748B] mt-1">{label}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
