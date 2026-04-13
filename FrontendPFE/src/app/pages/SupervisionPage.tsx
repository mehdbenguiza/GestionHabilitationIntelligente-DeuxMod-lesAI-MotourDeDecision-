import { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, AlertCircle, Target, BarChart3, 
  Activity, Settings, Edit, Trash2, CheckCircle, XCircle,
  Plus, Save, X, Download, RefreshCw, 
  ChevronDown, ChevronUp, Filter, Clock, Info
} from 'lucide-react';
import { mockDecisionsIA } from '../utils/mockData';
import { Badge } from '../components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

interface AutomationRule {
  id: string;
  equipe: string;
  roles: string[];
  environnements: string[];
  accesParDefaut: { nom: string; niveau: 'Base' | 'Sensible' | 'Critique' }[];
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  timestamp: Date;
}

const mockAutomationRules: AutomationRule[] = [
  {
    id: '1',
    equipe: 'Middleware',
    roles: ['Développeur', 'Tech Lead'],
    environnements: ['DEV', 'QA'],
    accesParDefaut: [
      { nom: 'API Gateway', niveau: 'Base' },
      { nom: 'Message Queue', niveau: 'Sensible' }
    ]
  },
  {
    id: '2',
    equipe: 'Développement',
    roles: ['Développeur Frontend', 'Développeur Backend'],
    environnements: ['DEV', 'QA'],
    accesParDefaut: [
      { nom: 'Code Repository', niveau: 'Base' },
      { nom: 'CI/CD Pipeline', niveau: 'Base' }
    ]
  },
  {
    id: '3',
    equipe: 'Ops',
    roles: ['DevOps Engineer', 'SRE'],
    environnements: ['PROD', 'PREPROD', 'QA'],
    accesParDefaut: [
      { nom: 'Monitoring Tools', niveau: 'Sensible' },
      { nom: 'Infrastructure', niveau: 'Critique' }
    ]
  },
  {
    id: '4',
    equipe: 'Sécurité',
    roles: ['Security Engineer', 'Security Analyst'],
    environnements: ['PROD', 'PREPROD', 'QA', 'DEV'],
    accesParDefaut: [
      { nom: 'SIEM', niveau: 'Critique' },
      { nom: 'Vulnerability Scanner', niveau: 'Sensible' }
    ]
  }
];

export function SupervisionPage() {
  // États
  const [filterAnomalie, setFilterAnomalie] = useState('all');
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [showAddRuleModal, setShowAddRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
  const [aiThresholds, setAiThresholds] = useState({
    autoApprove: 95,
    anomalyAlert: 30
  });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [expandedAnomalies, setExpandedAnomalies] = useState<string[]>([]);
  const [showStats, setShowStats] = useState(true);
  const [showCharts, setShowCharts] = useState(true);
  const [rules, setRules] = useState(mockAutomationRules);
  const [selectedTimeRange, setSelectedTimeRange] = useState('month');

  // Nouveaux états de données réelles
  const [realMetrics, setRealMetrics] = useState<any>(null);
  const [realDecisions, setRealDecisions] = useState<any[]>([]);
  const [loadingSupervision, setLoadingSupervision] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const fetchData = async () => {
      try {
        const metricsRes = await fetch('http://127.0.0.1:8000/ai/metrics?v=2', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const decisionsRes = await fetch('http://127.0.0.1:8000/ai/decisions?v=2', {
             headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (metricsRes.ok && decisionsRes.ok) {
           const metrics = await metricsRes.json();
           const decisions = await decisionsRes.json();
           setRealMetrics(metrics);
           setRealDecisions(decisions);
        }
      } catch (err) {
        console.error("Supervision endpoints error:", err);
      } finally {
        setLoadingSupervision(false);
      }
    };
    fetchData();
  }, []);

  // Fonction pour ajouter une notification
  const addNotification = (type: Notification['type'], message: string) => {
    const newNotification: Notification = {
      id: Date.now().toString(),
      type,
      message,
      timestamp: new Date()
    };
    setNotifications(prev => [newNotification, ...prev].slice(0, 5));
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
    }, 5000);
  };

  // Fonctions CRUD pour les règles
  const handleAddRule = (rule: AutomationRule) => {
    setRules(prev => [...prev, { ...rule, id: Date.now().toString() }]);
    setShowAddRuleModal(false);
    addNotification('success', 'Règle ajoutée avec succès');
  };

  const handleEditRule = (rule: AutomationRule) => {
    setEditingRule(rule);
    setShowAddRuleModal(true);
  };

  const handleUpdateRule = (updatedRule: AutomationRule) => {
    setRules(prev => prev.map(r => r.id === updatedRule.id ? updatedRule : r));
    setEditingRule(null);
    setShowAddRuleModal(false);
    addNotification('success', 'Règle modifiée avec succès');
  };

  const handleDeleteRule = (ruleId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette règle ?')) {
      setRules(prev => prev.filter(r => r.id !== ruleId));
      addNotification('error', 'Règle supprimée');
    }
  };

  const handleValidateAnomaly = (anomalyId: string) => {
    addNotification('success', `Anomalie ${anomalyId} validée et traitée`);
  };

  const handleIgnoreAnomaly = (anomalyId: string) => {
    addNotification('info', `Anomalie ${anomalyId} ignorée`);
  };

  const toggleAnomalyExpansion = (anomalyId: string) => {
    setExpandedAnomalies(prev => 
      prev.includes(anomalyId) 
        ? prev.filter(id => id !== anomalyId)
        : [...prev, anomalyId]
    );
  };

  const filteredDecisions = realDecisions.filter(decision => {
    if (filterAnomalie === 'all') return true;
    if (filterAnomalie === 'anomalie') return decision.anomalie;
    if (filterAnomalie === 'normal') return !decision.anomalie;
    return true;
  });

  const getNiveauBadgeColor = (niveau: string) => {
    switch (niveau) {
      case 'Base': return 'bg-green-100 text-green-800 border-green-300';
      case 'Sensible': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Critique': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getNotificationStyles = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-50 border-green-200 text-green-800';
      case 'error': return 'bg-red-50 border-red-200 text-red-800';
      case 'warning': return 'bg-amber-50 border-amber-200 text-amber-800';
      default: return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  // Maps values correctly if realMetrics existing
  const autoApprovals = realMetrics?.auto_approve_rate || 0;
  const precision = realMetrics?.avg_confidence || 80;
  
  const performanceData = [
    { metrique: 'Précision', valeur: precision },
    { metrique: 'Auto-Approvals', valeur: autoApprovals },
    { metrique: 'Tickets traités', valeur: realMetrics?.total || 0 > 100 ? 100 : realMetrics?.total || 0 }, // fallback representation
  ];

  const evolutionPerformance = [
    { semaine: 'S1', precision: 89, rappel: 87 },
    { semaine: 'S2', precision: 91, rappel: 88 },
    { semaine: 'S3', precision: 93, rappel: 90 },
    { semaine: 'S4', precision: 94, rappel: 91 }
  ];

  const featureImportance = [
    { feature: 'Rôle utilisateur', importance: 0.35 },
    { feature: 'Équipe', importance: 0.28 },
    { feature: 'Environnement', importance: 0.22 },
    { feature: 'Historique', importance: 0.15 }
  ];

  const anomaliesRecentes = mockDecisionsIA.filter(d => d.anomalie);

  const detailedAnomalies = [
    {
      id: '1',
      ticket: 'TKT-2026-004',
      demandeur: 'Nesrine Bouazizi',
      equipe: 'Support Client',
      demande: 'Accès base Core Banking en PROD',
      reasoning: [
        'Rôle "Agent Support" incompatible avec accès niveau Critique',
        'Équipe Support ne nécessite pas d\'accès direct aux bases de données',
        'Pas d\'historique de demandes similaires pour cette équipe',
        'Score de risque: 88/100 (Très élevé)'
      ],
      timestamp: new Date('2026-02-24T16:30:00'),
      severity: 'high'
    },
    {
      id: '2',
      ticket: 'TKT-2026-007',
      demandeur: 'Ali Hammouda',
      equipe: 'Marketing',
      demande: 'Accès serveurs PROD',
      reasoning: [
        'Équipe Marketing n\'a jamais eu d\'accès aux serveurs de production',
        'Aucune justification métier fournie',
        'Demande en dehors des heures de travail (23h45)',
        'Score de risque: 92/100 (Critique)'
      ],
      timestamp: new Date('2026-02-26T23:45:00'),
      severity: 'critical'
    }
  ];

  const pieData = realMetrics ? [
    { name: 'Base', value: realMetrics.levels['BASE'] || 0, color: '#10B981' },
    { name: 'Sensible', value: realMetrics.levels['SENSITIVE'] || 0, color: '#F59E0B' },
    { name: 'Critique', value: realMetrics.levels['CRITICAL'] || 0, color: '#EF4444' }
  ] : [];

  return (
    <div className="space-y-6 p-6 bg-[#F8FAFC] min-h-screen relative">
      {/* Notifications */}
      <div className="fixed top-4 right-4 z-[60] space-y-2 w-96">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`p-4 rounded-lg border shadow-lg animate-slideIn ${getNotificationStyles(notification.type)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                {notification.type === 'success' && <CheckCircle size={18} />}
                {notification.type === 'error' && <XCircle size={18} />}
                {notification.type === 'warning' && <AlertCircle size={18} />}
                {notification.type === 'info' && <Info size={18} />}
                <p className="text-sm font-medium">{notification.message}</p>
              </div>
              <button
                onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={16} />
              </button>
            </div>
            <p className="text-xs mt-1 opacity-75">
              {notification.timestamp.toLocaleTimeString()}
            </p>
          </div>
        ))}
      </div>

      {/* En-tête avec actions */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Supervision IA & Sécurité</h1>
          <p className="text-[#64748B]">Monitoring des décisions et performances du modèle d'IA</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-4 py-2 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] text-sm"
          >
            <option value="week">7 derniers jours</option>
            <option value="month">30 derniers jours</option>
            <option value="quarter">Ce trimestre</option>
            <option value="year">Cette année</option>
          </select>
          <button
            onClick={() => addNotification('info', 'Données actualisées')}
            className="p-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
            title="Actualiser"
          >
            <RefreshCw size={20} className="text-[#64748B]" />
          </button>
          <button
            onClick={() => {/* Logique d'export */}}
            className="p-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
            title="Exporter"
          >
            <Download size={20} className="text-[#64748B]" />
          </button>
          <button
            onClick={() => setShowRulesModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors"
          >
            <Settings size={20} />
            Configuration IA
          </button>
        </div>
      </div>

      {/* Statistiques clés avec toggle */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <button
          onClick={() => setShowStats(!showStats)}
          className="w-full px-6 py-4 flex items-center justify-between bg-[#F8FAFC] border-b border-[#E2E8F0]"
        >
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-[#003087]" />
            <h2 className="font-semibold text-[#1E2937]">Indicateurs clés</h2>
          </div>
          {showStats ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        
        {showStats && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-purple-50 to-white rounded-xl p-6 border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Brain size={24} className="text-purple-600" />
                  </div>
                  <TrendingUp size={20} className="text-[#10B981]" />
                </div>
                <div className="text-3xl font-bold text-[#1E2937] mb-1">{realMetrics ? realMetrics.avg_confidence : 0}%</div>
                <div className="text-sm text-[#64748B]">Confiance globale moyenne</div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-white rounded-xl p-6 border border-green-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <Target size={24} className="text-[#10B981]" />
                  </div>
                  <TrendingUp size={20} className="text-[#10B981]" />
                </div>
                <div className="text-3xl font-bold text-[#1E2937] mb-1">{realMetrics ? realMetrics.auto_approve_rate : 0}%</div>
                <div className="text-sm text-[#64748B]">Taux d'auto-approbation</div>
              </div>

              <div className="bg-gradient-to-br from-amber-50 to-white rounded-xl p-6 border border-amber-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                    <Activity size={24} className="text-[#F59E0B]" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[#1E2937] mb-1">{realMetrics ? realMetrics.total : 0}</div>
                <div className="text-sm text-[#64748B]">Décisions IA globales</div>
              </div>

              <div className="bg-gradient-to-br from-red-50 to-white rounded-xl p-6 border border-red-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                    <AlertCircle size={24} className="text-[#EF4444]" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[#1E2937] mb-1">{filteredDecisions.filter(d => d.anomalie).length}</div>
                <div className="text-sm text-[#64748B]">Anomalies détectées</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Graphiques avec toggle */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <button
          onClick={() => setShowCharts(!showCharts)}
          className="w-full px-6 py-4 flex items-center justify-between bg-[#F8FAFC] border-b border-[#E2E8F0]"
        >
          <div className="flex items-center gap-2">
            <BarChart3 size={20} className="text-[#003087]" />
            <h2 className="font-semibold text-[#1E2937]">Analyses et performances</h2>
          </div>
          {showCharts ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showCharts && (
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Métriques de performance */}
              <div className="bg-white rounded-xl p-4 border border-[#E2E8F0]">
                <h3 className="text-lg font-semibold text-[#1E2937] mb-4">Métriques de Performance</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="metrique" stroke="#64748B" style={{ fontSize: '12px' }} />
                    <YAxis stroke="#64748B" style={{ fontSize: '12px' }} domain={[0, 100]} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #E2E8F0', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Bar dataKey="valeur" fill="#003087" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Évolution de la performance */}
              <div className="bg-white rounded-xl p-4 border border-[#E2E8F0]">
                <h3 className="text-lg font-semibold text-[#1E2937] mb-4">Évolution Temporelle (Tickets analysés par jour)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={realMetrics?.daily_stats || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="date" stroke="#64748B" style={{ fontSize: '10px' }} />
                    <YAxis stroke="#64748B" style={{ fontSize: '12px' }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #E2E8F0', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#003087" strokeWidth={3} dot={{ fill: '#003087', r: 3 }} name="Décisions" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Feature Importance */}
              <div className="bg-white rounded-xl p-4 border border-[#E2E8F0]">
                <h3 className="text-lg font-semibold text-[#1E2937] mb-4">Importance des Features</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={featureImportance} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis type="number" domain={[0, 0.4]} stroke="#64748B" style={{ fontSize: '12px' }} />
                    <YAxis type="category" dataKey="feature" stroke="#64748B" style={{ fontSize: '12px' }} width={120} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #E2E8F0', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Bar dataKey="importance" fill="#00AEEF" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Distribution des niveaux */}
              <div className="bg-white rounded-xl p-4 border border-[#E2E8F0]">
                <h3 className="text-lg font-semibold text-[#1E2937] mb-4">Distribution des Niveaux d'Accès</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Règles d'Automatisation par Équipe */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-[#F8FAFC] border-b border-[#E2E8F0] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="text-[#003087]" size={20} />
            <h2 className="font-semibold text-[#1E2937]">Règles d'Automatisation par Équipe</h2>
          </div>
          <button
            onClick={() => {
              setEditingRule(null);
              setShowAddRuleModal(true);
            }}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors text-sm"
          >
            <Plus size={16} />
            Ajouter une règle
          </button>
        </div>

        <div className="p-6 overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F8FAFC]">
              <tr className="border-b border-[#E2E8F0]">
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Équipe</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Rôles</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Environnements</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Accès par Défaut</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                  <td className="py-4 px-6 font-semibold text-[#1E2937]">{rule.equipe}</td>
                  <td className="py-4 px-6">
                    <div className="flex gap-1 flex-wrap">
                      {rule.roles.map((role, idx) => (
                        <Badge key={idx} className="bg-blue-50 text-blue-700 border-blue-200 border text-xs">
                          {role}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex gap-1 flex-wrap">
                      {rule.environnements.map((env, idx) => (
                        <Badge key={idx} className="bg-purple-50 text-purple-700 border-purple-200 border text-xs">
                          {env}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex gap-1 flex-wrap">
                      {rule.accesParDefaut.map((acces, idx) => (
                        <Badge key={idx} className={`${getNiveauBadgeColor(acces.niveau)} border text-xs`}>
                          {acces.nom}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleEditRule(rule)}
                        className="p-2 text-[#003087] hover:bg-blue-50 rounded-lg transition-colors"
                        title="Modifier"
                      >
                        <Edit size={16} />
                      </button>
                      <button 
                        onClick={() => handleDeleteRule(rule.id)}
                        className="p-2 text-[#EF4444] hover:bg-red-50 rounded-lg transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Anomalies détaillées */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-[#F8FAFC] border-b border-[#E2E8F0]">
          <div className="flex items-center gap-2">
            <AlertCircle className="text-[#EF4444]" size={20} />
            <h2 className="font-semibold text-[#1E2937]">Anomalies Détectées - Demandes Inhabituelles</h2>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {detailedAnomalies.map((anomaly) => (
            <div 
              key={anomaly.id} 
              className={`p-6 rounded-xl border-2 transition-all ${
                anomaly.severity === 'critical' 
                  ? 'bg-red-50 border-red-300 hover:border-red-400' 
                  : 'bg-orange-50 border-orange-300 hover:border-orange-400'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <Badge className={`${
                      anomaly.severity === 'critical' 
                        ? 'bg-red-200 text-red-800 border-red-400' 
                        : 'bg-orange-200 text-orange-800 border-orange-400'
                    } border font-bold px-3 py-1`}>
                      {anomaly.ticket}
                    </Badge>
                    <span className="font-semibold text-[#1E2937]">{anomaly.demandeur}</span>
                    <span className="text-sm text-[#64748B]">• {anomaly.equipe}</span>
                    <Badge className={anomaly.severity === 'critical' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'}>
                      {anomaly.severity === 'critical' ? 'Critique' : 'Élevée'}
                    </Badge>
                  </div>
                  
                  <div className="text-[#1E2937] font-medium mb-3">
                    Demande: <span className="text-[#EF4444] font-semibold">{anomaly.demande}</span>
                  </div>

                  <button
                    onClick={() => toggleAnomalyExpansion(anomaly.id)}
                    className="flex items-center gap-1 text-sm text-[#003087] hover:text-[#002066] mb-3"
                  >
                    {expandedAnomalies.includes(anomaly.id) ? (
                      <>Masquer les détails <ChevronUp size={16} /></>
                    ) : (
                      <>Voir le raisonnement IA <ChevronDown size={16} /></>
                    )}
                  </button>

                  {expandedAnomalies.includes(anomaly.id) && (
                    <div className="bg-white rounded-lg p-4 border border-red-200 mb-4">
                      <div className="text-sm font-semibold text-[#1E2937] mb-3 flex items-center gap-2">
                        <Brain size={16} className="text-[#003087]" />
                        Raisonnement IA détaillé:
                      </div>
                      <ul className="space-y-2">
                        {anomaly.reasoning.map((reason, idx) => (
                          <li key={idx} className="text-sm text-[#64748B] flex items-start gap-2">
                            <span className="text-[#EF4444] mt-1">•</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-red-200">
                <div className="flex items-center gap-2 text-xs text-[#64748B]">
                  <Clock size={14} />
                  Détecté le {anomaly.timestamp.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleIgnoreAnomaly(anomaly.id)}
                    className="px-4 py-2 bg-white border border-[#E2E8F0] text-[#64748B] rounded-lg hover:bg-[#F8FAFC] transition-colors text-sm font-semibold flex items-center gap-2"
                  >
                    <XCircle size={16} />
                    Ignorer
                  </button>
                  <button
                    onClick={() => handleValidateAnomaly(anomaly.id)}
                    className="px-4 py-2 bg-[#EF4444] text-white rounded-lg hover:bg-[#DC2626] transition-colors text-sm font-semibold flex items-center gap-2"
                  >
                    <CheckCircle size={16} />
                    Valider Alerte
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tableau des décisions IA */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-[#F8FAFC] border-b border-[#E2E8F0] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="text-[#003087]" size={20} />
            <h2 className="font-semibold text-[#1E2937]">Décisions IA</h2>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={filterAnomalie}
              onChange={(e) => setFilterAnomalie(e.target.value)}
              className="px-4 py-2 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] text-sm"
            >
              <option value="all">Toutes les décisions</option>
              <option value="anomalie">Anomalies uniquement</option>
              <option value="normal">Sans anomalie</option>
            </select>
            <Filter size={20} className="text-[#64748B]" />
          </div>
        </div>

        <div className="p-6 overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F8FAFC]">
              <tr className="border-b border-[#E2E8F0]">
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Ticket</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Niveau Prédit</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Niveau Réel</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Score Confiance</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Anomalie</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredDecisions.map((decision, idx) => (
                <tr key={decision.id || idx} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                  <td className="py-4 px-6 font-semibold text-[#003087]">{decision.ticketRef}</td>
                  <td className="py-4 px-6">
                    <Badge className={`${getNiveauBadgeColor(decision.niveauPredit == 'BASE' ? 'Base' : decision.niveauPredit == 'SENSITIVE' ? 'Sensible' : 'Critique')} border`}>
                      {decision.niveauPredit}
                    </Badge>
                  </td>
                  <td className="py-4 px-6">
                    <Badge className={`${getNiveauBadgeColor(decision.niveauReel == 'BASE' ? 'Base' : decision.niveauReel == 'SENSITIVE' ? 'Sensible' : 'Critique')} border`}>
                      {decision.niveauReel}
                    </Badge>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                       {/* Make sure we can handle real number */}
                      <div className={`font-bold ${
                        decision.scoreConfiance > 80 ? 'text-[#10B981]' : 
                        decision.scoreConfiance > 50 ? 'text-[#F59E0B]' : 
                        'text-[#EF4444]'
                      }`}>
                        {decision.scoreConfiance}%
                      </div>
                      {decision.scoreConfiance < aiThresholds.anomalyAlert && (
                        <AlertCircle size={14} className="text-[#EF4444]" />
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    {decision.anomalie ? (
                      <Badge className="bg-red-100 text-red-800 border-red-300 border">
                        Oui
                      </Badge>
                    ) : (
                      <Badge className="bg-green-100 text-green-800 border-green-300 border">
                        Non
                      </Badge>
                    )}
                  </td>
                  <td className="py-4 px-6 text-[#64748B] text-sm">
                    {decision.date ? new Date(decision.date).toLocaleDateString('fr-FR') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Configuration IA - Transparent */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
          {/* Overlay transparent - ne bloque pas la vue */}
          <div className="absolute inset-0 bg-transparent" />
          
          {/* Modal content - avec pointer-events: auto pour pouvoir interagir */}
          <div className="relative bg-white/95 backdrop-blur-sm rounded-xl max-w-md w-full shadow-2xl border-2 border-[#E2E8F0] pointer-events-auto">
            <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Settings className="text-[#003087]" size={24} />
                <h3 className="text-xl font-bold text-[#1E2937]">Configuration IA</h3>
              </div>
              <button
                onClick={() => setShowRulesModal(false)}
                className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors"
              >
                <X size={20} className="text-[#64748B]" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="bg-blue-50/90 p-4 rounded-lg border border-blue-200">
                <div className="flex items-start gap-3">
                  <Info size={20} className="text-[#003087] mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-[#1E2937] mb-1">Configuration des seuils</h4>
                    <p className="text-sm text-[#64748B]">
                      Ajustez les seuils pour contrôler le comportement de l'IA
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-3">
                  Seuil d'approbation automatique
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="70"
                    max="100"
                    value={aiThresholds.autoApprove}
                    onChange={(e) => setAiThresholds({ ...aiThresholds, autoApprove: parseInt(e.target.value) })}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-2xl font-bold text-[#003087] w-16 text-right bg-blue-50/90 px-3 py-1 rounded-lg">
                    {aiThresholds.autoApprove}%
                  </span>
                </div>
                <p className="text-xs text-[#64748B] mt-2">
                  Les tickets avec un score supérieur à {aiThresholds.autoApprove}% seront approuvés automatiquement
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-3">
                  Seuil d'alerte anomalie
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={aiThresholds.anomalyAlert}
                    onChange={(e) => setAiThresholds({ ...aiThresholds, anomalyAlert: parseInt(e.target.value) })}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-2xl font-bold text-[#EF4444] w-16 text-right bg-red-50/90 px-3 py-1 rounded-lg">
                    {aiThresholds.anomalyAlert}%
                  </span>
                </div>
                <p className="text-xs text-[#64748B] mt-2">
                  Une alerte sera déclenchée pour les scores inférieurs à {aiThresholds.anomalyAlert}%
                </p>
              </div>

              <div className="pt-4 border-t border-[#E2E8F0]">
                <button
                  onClick={() => {
                    setShowRulesModal(false);
                    addNotification('success', 'Configuration IA mise à jour');
                  }}
                  className="w-full py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors flex items-center justify-center gap-2"
                >
                  <Save size={18} />
                  Sauvegarder la Configuration
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Ajout/Édition Règle - Transparent */}
      {showAddRuleModal && (
        <AddEditRuleModal
          rule={editingRule}
          onClose={() => {
            setShowAddRuleModal(false);
            setEditingRule(null);
          }}
          onSave={editingRule ? handleUpdateRule : handleAddRule}
        />
      )}
    </div>
  );
}

// Modal pour ajouter/modifier une règle - Version transparente
function AddEditRuleModal({ rule, onClose, onSave }: { 
  rule?: AutomationRule | null; 
  onClose: () => void; 
  onSave: (rule: AutomationRule) => void;
}) {
  const [formData, setFormData] = useState<Partial<AutomationRule>>(
    rule || {
      equipe: '',
      roles: [],
      environnements: [],
      accesParDefaut: []
    }
  );

  const [newRole, setNewRole] = useState('');
  const [newEnv, setNewEnv] = useState('');
  const [newAcces, setNewAcces] = useState({ nom: '', niveau: 'Base' as const });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.equipe && formData.roles?.length && formData.environnements?.length) {
      onSave({
        id: rule?.id || Date.now().toString(),
        equipe: formData.equipe,
        roles: formData.roles,
        environnements: formData.environnements,
        accesParDefaut: formData.accesParDefaut || []
      });
    }
  };

  const addRole = () => {
    if (newRole && !formData.roles?.includes(newRole)) {
      setFormData({
        ...formData,
        roles: [...(formData.roles || []), newRole]
      });
      setNewRole('');
    }
  };

  const addEnv = () => {
    if (newEnv && !formData.environnements?.includes(newEnv)) {
      setFormData({
        ...formData,
        environnements: [...(formData.environnements || []), newEnv]
      });
      setNewEnv('');
    }
  };

  const addAcces = () => {
    if (newAcces.nom) {
      setFormData({
        ...formData,
        accesParDefaut: [...(formData.accesParDefaut || []), { ...newAcces }]
      });
      setNewAcces({ nom: '', niveau: 'Base' });
    }
  };

  const removeRole = (roleToRemove: string) => {
    setFormData({
      ...formData,
      roles: formData.roles?.filter(r => r !== roleToRemove)
    });
  };

  const removeEnv = (envToRemove: string) => {
    setFormData({
      ...formData,
      environnements: formData.environnements?.filter(e => e !== envToRemove)
    });
  };

  const removeAcces = (accesToRemove: string) => {
    setFormData({
      ...formData,
      accesParDefaut: formData.accesParDefaut?.filter(a => a.nom !== accesToRemove)
    });
  };

  const getNiveauBadgeColor = (niveau: string) => {
    switch (niveau) {
      case 'Base': return 'bg-green-100 text-green-800 border-green-300';
      case 'Sensible': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Critique': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
      {/* Overlay transparent */}
      <div className="absolute inset-0 bg-transparent" />
      
      {/* Modal content */}
      <div className="relative bg-white/95 backdrop-blur-sm rounded-xl max-w-2xl w-full shadow-2xl border-2 border-[#E2E8F0] pointer-events-auto">
        <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between">
          <h3 className="text-xl font-bold text-[#1E2937]">
            {rule ? 'Modifier la règle' : 'Ajouter une nouvelle règle'}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors"
          >
            <X size={20} className="text-[#64748B]" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-[#1E2937] mb-2">
              Équipe <span className="text-[#EF4444]">*</span>
            </label>
            <input
              type="text"
              value={formData.equipe}
              onChange={(e) => setFormData({ ...formData, equipe: e.target.value })}
              className="w-full px-4 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] bg-white/80"
              placeholder="ex: Développement"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#1E2937] mb-2">
              Rôles <span className="text-[#EF4444]">*</span>
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                className="flex-1 px-4 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] bg-white/80"
                placeholder="Ajouter un rôle"
              />
              <button
                type="button"
                onClick={addRole}
                className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]"
              >
                Ajouter
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.roles?.map((role, idx) => (
                <Badge key={idx} className="bg-blue-50 text-blue-700 border-blue-200 border px-3 py-1 flex items-center gap-1">
                  {role}
                  <button type="button" onClick={() => removeRole(role)} className="ml-1 hover:text-blue-900">
                    <X size={14} />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#1E2937] mb-2">
              Environnements <span className="text-[#EF4444]">*</span>
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newEnv}
                onChange={(e) => setNewEnv(e.target.value)}
                className="flex-1 px-4 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] bg-white/80"
                placeholder="Ajouter un environnement"
              />
              <button
                type="button"
                onClick={addEnv}
                className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]"
              >
                Ajouter
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.environnements?.map((env, idx) => (
                <Badge key={idx} className="bg-purple-50 text-purple-700 border-purple-200 border px-3 py-1 flex items-center gap-1">
                  {env}
                  <button type="button" onClick={() => removeEnv(env)} className="ml-1 hover:text-purple-900">
                    <X size={14} />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#1E2937] mb-2">
              Accès par défaut
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newAcces.nom}
                onChange={(e) => setNewAcces({ ...newAcces, nom: e.target.value })}
                className="flex-1 px-4 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] bg-white/80"
                placeholder="Nom de l'accès"
              />
              <select
                value={newAcces.niveau}
                onChange={(e) => setNewAcces({ ...newAcces, niveau: e.target.value as any })}
                className="px-4 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] bg-white/80"
              >
                <option value="Base">Base</option>
                <option value="Sensible">Sensible</option>
                <option value="Critique">Critique</option>
              </select>
              <button
                type="button"
                onClick={addAcces}
                className="px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066]"
              >
                Ajouter
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.accesParDefaut?.map((acces, idx) => (
                <Badge key={idx} className={`${getNiveauBadgeColor(acces.niveau)} border px-3 py-1 flex items-center gap-1`}>
                  {acces.nom}
                  <button type="button" onClick={() => removeAcces(acces.nom)} className="ml-1">
                    <X size={14} />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-[#E2E8F0] flex gap-3">
            <button
              type="submit"
              className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors flex items-center justify-center gap-2"
            >
              <Save size={18} />
              {rule ? 'Mettre à jour' : 'Créer la règle'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 bg-[#F8FAFC] text-[#64748B] rounded-lg font-semibold hover:bg-[#E2E8F0] transition-colors flex items-center justify-center gap-2"
            >
              <X size={18} />
              Annuler
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}