import { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import * as LucideIcons from 'lucide-react';
import { Badge } from '../components/ui/badge';

// Extraire les icônes nécessaires
const {
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  TrendingUp,
  Users,
  Shield,
  Activity,
  Settings,
  Move,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  GripVertical,
  ChevronRight,
  ChevronLeft,
  PlusCircle,
  RefreshCw
} = LucideIcons;

// Types pour les widgets
interface Widget {
  id: string;
  title: string;
  visible: boolean;
  size: 'small' | 'medium' | 'large';
  position: number;
  icon: any;
}

// Interface pour les props du StatCard
interface StatCardProps {
  icon: any;
  label: string;
  value: number;
  color: string;
  bgColor: string;
  onMove: (direction: 'up' | 'down') => void;
  onResize: () => void;
  onToggleVisibility: () => void;
  isVisible: boolean;
  canMoveUp: boolean;
  canMoveDown: boolean;
}

const StatCard = ({ 
  icon: Icon, 
  label, 
  value, 
  color, 
  bgColor, 
  onMove, 
  onResize, 
  onToggleVisibility, 
  isVisible,
  canMoveUp,
  canMoveDown 
}: StatCardProps) => (
  <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm hover:shadow-md transition-shadow relative group">
    <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
      <button
        onClick={() => onMove('up')}
        disabled={!canMoveUp}
        className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] transition-colors ${
          canMoveUp 
            ? 'hover:bg-[#F8FAFC] text-[#64748B]' 
            : 'opacity-50 cursor-not-allowed'
        }`}
        title="Déplacer vers le haut"
      >
        <Move size={14} className="rotate-[-90deg]" />
      </button>
      <button
        onClick={() => onMove('down')}
        disabled={!canMoveDown}
        className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] transition-colors ${
          canMoveDown 
            ? 'hover:bg-[#F8FAFC] text-[#64748B]' 
            : 'opacity-50 cursor-not-allowed'
        }`}
        title="Déplacer vers le bas"
      >
        <Move size={14} className="rotate-90" />
      </button>
      <button
        onClick={() => onResize()}
        className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
        title="Changer la taille"
      >
        <Maximize2 size={14} className="text-[#64748B]" />
      </button>
      <button
        onClick={() => onToggleVisibility()}
        className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
        title="Masquer/Afficher"
      >
        {isVisible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}
      </button>
    </div>
    <div className="flex items-center justify-between mb-4">
      <div className={`w-12 h-12 rounded-lg ${bgColor} flex items-center justify-center`}>
        <Icon size={24} className={color} />
      </div>
      <TrendingUp size={20} className="text-[#10B981]" />
    </div>
    <div className="text-3xl font-bold text-[#1E2937] mb-1">{value}</div>
    <div className="text-sm text-[#64748B]">{label}</div>
  </div>
);

// Panneau de contrôle des widgets
const WidgetControls = ({ widgets, onToggleAll, onResetLayout, isOpen, onToggle }: any) => (
  <div className={`relative bg-white rounded-xl border border-[#E2E8F0] shadow-sm mb-6 transition-all duration-300 ${
    isOpen ? 'p-4' : 'p-2'
  }`}>
    <button
      onClick={onToggle}
      className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-white border border-[#E2E8F0] rounded-full shadow-sm flex items-center justify-center hover:bg-[#F8FAFC] transition-colors z-20"
      title={isOpen ? "Masquer le panneau" : "Afficher le panneau"}
    >
      {isOpen ? <ChevronLeft size={14} className="text-[#003087]" /> : <ChevronRight size={14} className="text-[#003087]" />}
    </button>

    {isOpen ? (
      <>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings size={20} className="text-[#003087]" />
            <span className="font-semibold text-[#1E2937]">Personnalisation du tableau de bord</span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => onToggleAll(true)} className="px-3 py-1 text-sm bg-[#003087] text-white rounded-md hover:bg-[#002366] transition-colors">Tout afficher</button>
            <button onClick={() => onToggleAll(false)} className="px-3 py-1 text-sm border border-[#E2E8F0] text-[#64748B] rounded-md hover:bg-[#F8FAFC] transition-colors">Tout masquer</button>
            <button onClick={onResetLayout} className="px-3 py-1 text-sm border border-[#E2E8F0] text-[#64748B] rounded-md hover:bg-[#F8FAFC] transition-colors">Réinitialiser</button>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          {widgets.map((widget: any) => (
            <div key={widget.id} className="flex items-center justify-between p-2 border border-[#E2E8F0] rounded-md">
              <div className="flex items-center gap-2">
                <widget.icon size={16} className="text-[#003087]" />
                <span className="text-sm text-[#1E2937]">{widget.title}</span>
              </div>
              <button onClick={widget.onToggle} className={`p-1 rounded-md transition-colors ${widget.visible ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                {widget.visible ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
          ))}
        </div>
      </>
    ) : (
      <div className="flex items-center justify-center">
        <Settings size={20} className="text-[#003087]" />
      </div>
    )}
  </div>
);

export function DashboardPage() {
  const token = localStorage.getItem('token');
  const [stats, setStats] = useState({
    ticketsEnAttente: 0,
    ticketsTraitesAujourdhui: 0,
    decisionsAutomatiquesIA: 0,
    anomaliesDetectees: 0
  });
  const [evolutionData, setEvolutionData] = useState<any[]>([]);
  const [repartitionData, setRepartitionData] = useState<any[]>([]);
  const [recentTickets, setRecentTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const [widgets, setWidgets] = useState<Widget[]>([
    { id: 'stats', title: 'Statistiques', visible: true, size: 'medium', position: 0, icon: TrendingUp },
    { id: 'evolution', title: 'Évolution des tickets', visible: true, size: 'medium', position: 1, icon: Activity },
    { id: 'repartition', title: 'Répartition par niveau IA', visible: true, size: 'medium', position: 2, icon: Shield },
    { id: 'recent', title: 'Tickets récents', visible: true, size: 'large', position: 3, icon: Users },
    { id: 'alertes', title: 'Alertes IA', visible: true, size: 'medium', position: 4, icon: AlertCircle }
  ]);

  const [isCustomizationOpen, setIsCustomizationOpen] = useState(true);

  const fetchStats = async () => {
    if (!token) return;
    try {
      const response = await fetch('http://127.0.0.1:8000/tickets/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const tickets = await response.json();

        const enAttente = tickets.filter((t: any) => t.status === 'NEW').length;
        const traitesAujourdhui = tickets.filter((t: any) => {
          const today = new Date().toDateString();
          return new Date(t.created_at).toDateString() === today && ['APPROVED', 'REJECTED'].includes(t.status);
        }).length;

        // ✅ CORRECTION : ai_level est maintenant un champ plat renvoyé par l'API
        const autoApprouves = tickets.filter((t: any) => t.ai_level === 'BASE' && t.status === 'APPROVED').length;
        const anomalies = tickets.filter((t: any) => t.ai_level === 'CRITICAL' && t.status === 'NEW').length;

        setStats({
          ticketsEnAttente: enAttente,
          ticketsTraitesAujourdhui: traitesAujourdhui,
          decisionsAutomatiquesIA: autoApprouves,
          anomaliesDetectees: anomalies
        });

        // Évolution des 7 derniers jours
        const last7Days = [];
        for (let i = 6; i >= 0; i--) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          const dayStr = date.toLocaleDateString('fr-FR', { weekday: 'short' });
          const count = tickets.filter((t: any) => new Date(t.created_at).toDateString() === date.toDateString()).length;
          last7Days.push({ jour: dayStr, total: count });
        }
        setEvolutionData(last7Days);

        // ✅ Répartition par niveau IA (maintenant que le champ existe)
        const baseCount = tickets.filter((t: any) => t.ai_level === 'BASE').length;
        const sensitiveCount = tickets.filter((t: any) => t.ai_level === 'SENSITIVE').length;
        const criticalCount = tickets.filter((t: any) => t.ai_level === 'CRITICAL').length;
        const unknownCount = tickets.filter((t: any) => !t.ai_level).length;

        const repartition = [];
        if (baseCount > 0) repartition.push({ name: 'Base', value: baseCount, color: '#10B981' });
        if (sensitiveCount > 0) repartition.push({ name: 'Sensible', value: sensitiveCount, color: '#F59E0B' });
        if (criticalCount > 0) repartition.push({ name: 'Critique', value: criticalCount, color: '#EF4444' });
        if (unknownCount > 0) repartition.push({ name: 'Non classifié', value: unknownCount, color: '#94A3B8' });

        setRepartitionData(repartition);

        // Tickets récents (5 derniers)
        setRecentTickets(tickets.slice(0, 5));
      }
    } catch (err) {
      console.error('Erreur chargement stats:', err);
    } finally {
      setLoading(false);
    }
  };

  // Générer un ticket de test
  const generateTestTicket = async () => {
    setGenerating(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/tickets/simulate/create', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        await fetchStats();
        alert('✅ Ticket généré avec succès !');
      } else {
        alert('❌ Erreur lors de la génération');
      }
    } catch (err) {
      alert('❌ Erreur: ' + err);
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const getNiveauBadgeColor = (niveau: string) => {
    switch (niveau) {
      case 'BASE': return 'bg-green-100 text-green-800 border-green-300';
      case 'SENSITIVE': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getNiveauFr = (niveau: string) => {
    switch (niveau) {
      case 'BASE': return 'Base';
      case 'SENSITIVE': return 'Sensible';
      case 'CRITICAL': return 'Critique';
      default: return niveau;
    }
  };

  const getStatutBadgeColor = (statut: string) => {
    switch (statut) {
      case 'NEW': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'APPROVED': return 'bg-green-100 text-green-800 border-green-300';
      case 'REJECTED': return 'bg-red-100 text-red-800 border-red-300';
      case 'ASSIGNED': return 'bg-orange-100 text-orange-800 border-orange-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatutFr = (status: string) => {
    switch (status) {
      case 'NEW': return 'En attente';
      case 'APPROVED': return 'Approuvé';
      case 'REJECTED': return 'Rejeté';
      case 'ASSIGNED': return 'Assigné';
      default: return status;
    }
  };

  const toggleWidget = (widgetId: string) => {
    setWidgets(prev => prev.map(w => w.id === widgetId ? { ...w, visible: !w.visible } : w));
  };

  const toggleAllWidgets = (visible: boolean) => {
    setWidgets(prev => prev.map(w => ({ ...w, visible })));
  };

  const resizeWidget = (widgetId: string) => {
    setWidgets(prev => prev.map(w => {
      if (w.id === widgetId) {
        const sizes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large'];
        const currentIndex = sizes.indexOf(w.size);
        return { ...w, size: sizes[(currentIndex + 1) % sizes.length] };
      }
      return w;
    }));
  };

  const moveWidget = (widgetId: string, direction: 'up' | 'down') => {
    setWidgets(prev => {
      const visibleWidgets = prev.filter(w => w.visible);
      const hiddenWidgets = prev.filter(w => !w.visible);
      const index = visibleWidgets.findIndex(w => w.id === widgetId);
      if (index === -1 || (direction === 'up' && index === 0) || (direction === 'down' && index === visibleWidgets.length - 1)) return prev;
      
      const newVisibleWidgets = [...visibleWidgets];
      const swapIndex = direction === 'up' ? index - 1 : index + 1;
      [newVisibleWidgets[index], newVisibleWidgets[swapIndex]] = [newVisibleWidgets[swapIndex], newVisibleWidgets[index]];
      
      return [...newVisibleWidgets.map((w, idx) => ({ ...w, position: idx })), ...hiddenWidgets.map((w, idx) => ({ ...w, position: newVisibleWidgets.length + idx }))];
    });
  };

  const resetLayout = () => {
    setWidgets([
      { id: 'stats', title: 'Statistiques', visible: true, size: 'medium', position: 0, icon: TrendingUp },
      { id: 'evolution', title: 'Évolution des tickets', visible: true, size: 'medium', position: 1, icon: Activity },
      { id: 'repartition', title: 'Répartition par niveau IA', visible: true, size: 'medium', position: 2, icon: Shield },
      { id: 'recent', title: 'Tickets récents', visible: true, size: 'large', position: 3, icon: Users },
      { id: 'alertes', title: 'Alertes IA', visible: true, size: 'medium', position: 4, icon: AlertCircle }
    ]);
  };

  useEffect(() => {
    localStorage.setItem('dashboardWidgets', JSON.stringify(widgets));
  }, [widgets]);

  const visibleWidgets = widgets.filter(w => w.visible).sort((a, b) => a.position - b.position);
  const totalVisible = visibleWidgets.length;

  const getSizeClass = (size: string) => {
    switch(size) {
      case 'small': return 'col-span-1';
      case 'large': return 'col-span-2';
      default: return 'col-span-1';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du tableau de bord...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* En-tête avec bouton génération */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Tableau de Bord</h1>
          <p className="text-[#64748B]">Vue d'ensemble de la gestion des autorisations</p>
        </div>
        <button
          onClick={generateTestTicket}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors disabled:opacity-50"
        >
          {generating ? <RefreshCw size={18} className="animate-spin" /> : <PlusCircle size={18} />}
          {generating ? 'Génération...' : 'Générer un ticket test'}
        </button>
      </div>

      <WidgetControls 
        widgets={widgets.map(w => ({ ...w, onToggle: () => toggleWidget(w.id) }))}
        onToggleAll={toggleAllWidgets}
        onResetLayout={resetLayout}
        isOpen={isCustomizationOpen}
        onToggle={() => setIsCustomizationOpen(!isCustomizationOpen)}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {visibleWidgets.map((widget, index) => {
          const canMoveUp = index > 0;
          const canMoveDown = index < totalVisible - 1;

          switch(widget.id) {
            case 'stats':
              return (
                <div key={widget.id} className={`${getSizeClass(widget.size)} relative group`}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <StatCard icon={Clock} label="Tickets en attente" value={stats.ticketsEnAttente} color="text-[#00AEEF]" bgColor="bg-blue-50"
                      onMove={(dir) => moveWidget(widget.id, dir)} onResize={() => resizeWidget(widget.id)} onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible} canMoveUp={canMoveUp} canMoveDown={canMoveDown} />
                    <StatCard icon={CheckCircle} label="Traités aujourd'hui" value={stats.ticketsTraitesAujourdhui} color="text-[#10B981]" bgColor="bg-green-50"
                      onMove={(dir) => moveWidget(widget.id, dir)} onResize={() => resizeWidget(widget.id)} onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible} canMoveUp={canMoveUp} canMoveDown={canMoveDown} />
                    <StatCard icon={Zap} label="Décisions automatiques IA" value={stats.decisionsAutomatiquesIA} color="text-[#F59E0B]" bgColor="bg-amber-50"
                      onMove={(dir) => moveWidget(widget.id, dir)} onResize={() => resizeWidget(widget.id)} onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible} canMoveUp={canMoveUp} canMoveDown={canMoveDown} />
                    <StatCard icon={AlertCircle} label="Anomalies détectées" value={stats.anomaliesDetectees} color="text-[#EF4444]" bgColor="bg-red-50"
                      onMove={(dir) => moveWidget(widget.id, dir)} onResize={() => resizeWidget(widget.id)} onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible} canMoveUp={canMoveUp} canMoveDown={canMoveDown} />
                  </div>
                </div>
              );

            case 'evolution':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button onClick={() => moveWidget(widget.id, 'up')} disabled={!canMoveUp} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveUp ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-[-90deg]" /></button>
                    <button onClick={() => moveWidget(widget.id, 'down')} disabled={!canMoveDown} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveDown ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-90" /></button>
                    <button onClick={() => resizeWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]"><Maximize2 size={14} className="text-[#64748B]" /></button>
                    <button onClick={() => toggleWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]">{widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}</button>
                  </div>
                  <div className="flex items-center gap-2 mb-6"><Activity className="text-[#003087]" size={24} /><h2 className="text-xl font-bold text-[#1E2937]">Évolution des tickets (7 jours)</h2></div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={evolutionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="jour" stroke="#64748B" style={{ fontSize: '12px' }} />
                      <YAxis stroke="#64748B" style={{ fontSize: '12px' }} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #E2E8F0', borderRadius: '8px' }} />
                      <Line type="monotone" dataKey="total" stroke="#003087" strokeWidth={3} dot={{ fill: '#003087', r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              );

            case 'repartition':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button onClick={() => moveWidget(widget.id, 'up')} disabled={!canMoveUp} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveUp ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-[-90deg]" /></button>
                    <button onClick={() => moveWidget(widget.id, 'down')} disabled={!canMoveDown} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveDown ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-90" /></button>
                    <button onClick={() => resizeWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]"><Maximize2 size={14} className="text-[#64748B]" /></button>
                    <button onClick={() => toggleWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]">{widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}</button>
                  </div>
                  <div className="flex items-center gap-2 mb-6"><Shield className="text-[#003087]" size={24} /><h2 className="text-xl font-bold text-[#1E2937]">Répartition par niveau IA</h2></div>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie data={repartitionData} cx="50%" cy="50%" labelLine={false} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} outerRadius={100} dataKey="value">
                        {repartitionData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              );

            case 'recent':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} col-span-2 relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button onClick={() => moveWidget(widget.id, 'up')} disabled={!canMoveUp} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveUp ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-[-90deg]" /></button>
                    <button onClick={() => moveWidget(widget.id, 'down')} disabled={!canMoveDown} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveDown ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-90" /></button>
                    <button onClick={() => resizeWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]"><Maximize2 size={14} className="text-[#64748B]" /></button>
                    <button onClick={() => toggleWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]">{widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}</button>
                  </div>
                  <div className="flex items-center gap-2 mb-6"><Users className="text-[#003087]" size={24} /><h2 className="text-xl font-bold text-[#1E2937]">Tickets récents</h2></div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-[#E2E8F0]">
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Réf.</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Demandeur</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Équipe</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Niveau IA</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Confiance</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Statut</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Date</th>
                         </tr>
                      </thead>
                      <tbody>
                        {recentTickets.map((ticket) => (
                          <tr key={ticket.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors cursor-pointer" onClick={() => window.location.href = `/ticket/${ticket.id}`}>
                            <td className="py-3 px-4 font-medium text-[#003087]">{ticket.ref}</td>
                            <td className="py-3 px-4 text-[#1E2937]">{ticket.employee_name}</td>
                            <td className="py-3 px-4 text-[#64748B]">{ticket.team_name}</td>
                            <td className="py-3 px-4"><Badge className={`${getNiveauBadgeColor(ticket.ai_level)} border`}>{getNiveauFr(ticket.ai_level)}</Badge></td>
                            <td className="py-3 px-4 text-[#64748B]">{ticket.ai_confidence ? `${ticket.ai_confidence}%` : '-'}</td>
                            <td className="py-3 px-4"><Badge className={`${getStatutBadgeColor(ticket.status)} border`}>{getStatutFr(ticket.status)}</Badge></td>
                            <td className="py-3 px-4 text-[#64748B]">{new Date(ticket.created_at).toLocaleDateString('fr-FR')}</td>
                           </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );

            case 'alertes':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button onClick={() => moveWidget(widget.id, 'up')} disabled={!canMoveUp} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveUp ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-[-90deg]" /></button>
                    <button onClick={() => moveWidget(widget.id, 'down')} disabled={!canMoveDown} className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] ${canMoveDown ? 'hover:bg-[#F8FAFC]' : 'opacity-50 cursor-not-allowed'}`}><Move size={14} className="rotate-90" /></button>
                    <button onClick={() => resizeWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]"><Maximize2 size={14} className="text-[#64748B]" /></button>
                    <button onClick={() => toggleWidget(widget.id)} className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC]">{widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}</button>
                  </div>
                  <div className="flex items-center gap-2 mb-6"><AlertCircle className="text-[#EF4444]" size={24} /><h2 className="text-xl font-bold text-[#1E2937]">Alertes IA - Tickets critiques</h2></div>
                  <div className="space-y-3">
                    {recentTickets.filter((t: any) => t.ai_level === 'CRITICAL' && t.status === 'NEW').slice(0, 3).map((ticket: any) => (
                      <div key={ticket.id} className="p-4 bg-red-50 border border-red-200 rounded-lg cursor-pointer hover:bg-red-100 transition-colors" onClick={() => window.location.href = `/ticket/${ticket.id}`}>
                        <div className="flex items-start gap-3">
                          <AlertCircle className="text-[#EF4444] flex-shrink-0 mt-1" size={20} />
                          <div className="flex-1">
                            <div className="font-semibold text-[#1E2937] mb-1">{ticket.ref} - {ticket.employee_name}</div>
                            <div className="text-sm text-[#64748B] mb-2">{ticket.description?.substring(0, 100)}...</div>
                            <div className="flex items-center gap-2">
                              <Badge className="bg-red-100 text-red-800 border-red-300 border text-xs">{ticket.team_name}</Badge>
                              <span className="text-xs text-[#64748B]">Confiance: {ticket.ai_confidence}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    {recentTickets.filter((t: any) => t.ai_level === 'CRITICAL' && t.status === 'NEW').length === 0 && (
                      <div className="text-center py-8 text-[#64748B]">Aucune alerte critique</div>
                    )}
                  </div>
                </div>
              );

            default: return null;
          }
        })}
      </div>
    </div>
  );
}