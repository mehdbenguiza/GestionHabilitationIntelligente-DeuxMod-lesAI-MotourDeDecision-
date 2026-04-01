import { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import * as LucideIcons from 'lucide-react';
import { statsData, evolutionTickets, repartitionNiveaux, mockTickets } from '../utils/mockData';
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
  ChevronLeft
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
    {/* Contrôles du widget */}
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

// Interface pour les props du WidgetControls
interface WidgetControlsProps {
  widgets: Array<Widget & { onToggle: () => void }>;
  onToggleAll: (visible: boolean) => void;
  onResetLayout: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

// Panneau de contrôle des widgets - MODIFIÉ avec flèche
const WidgetControls = ({ widgets, onToggleAll, onResetLayout, isOpen, onToggle }: WidgetControlsProps) => (
  <div className={`relative bg-white rounded-xl border border-[#E2E8F0] shadow-sm mb-6 transition-all duration-300 ${
    isOpen ? 'p-4' : 'p-2'
  }`}>
    {/* Bouton fléché pour masquer/afficher */}
    <button
      onClick={onToggle}
      className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-white border border-[#E2E8F0] rounded-full shadow-sm flex items-center justify-center hover:bg-[#F8FAFC] transition-colors z-20"
      title={isOpen ? "Masquer le panneau" : "Afficher le panneau"}
    >
      {isOpen ? <ChevronLeft size={14} className="text-[#003087]" /> : <ChevronRight size={14} className="text-[#003087]" />}
    </button>

    {isOpen ? (
      // Contenu complet du panneau
      <>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings size={20} className="text-[#003087]" />
            <span className="font-semibold text-[#1E2937]">Personnalisation du tableau de bord</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onToggleAll(true)}
              className="px-3 py-1 text-sm bg-[#003087] text-white rounded-md hover:bg-[#002366] transition-colors"
            >
              Tout afficher
            </button>
            <button
              onClick={() => onToggleAll(false)}
              className="px-3 py-1 text-sm border border-[#E2E8F0] text-[#64748B] rounded-md hover:bg-[#F8FAFC] transition-colors"
            >
              Tout masquer
            </button>
            <button
              onClick={onResetLayout}
              className="px-3 py-1 text-sm border border-[#E2E8F0] text-[#64748B] rounded-md hover:bg-[#F8FAFC] transition-colors"
            >
              Réinitialiser
            </button>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          {widgets.map((widget) => (
            <div key={widget.id} className="flex items-center justify-between p-2 border border-[#E2E8F0] rounded-md">
              <div className="flex items-center gap-2">
                <widget.icon size={16} className="text-[#003087]" />
                <span className="text-sm text-[#1E2937]">{widget.title}</span>
              </div>
              <button
                onClick={widget.onToggle}
                className={`p-1 rounded-md transition-colors ${
                  widget.visible 
                    ? 'text-[#10B981] hover:text-[#0E9E6E]' 
                    : 'text-[#EF4444] hover:text-[#DC2626]'
                }`}
              >
                {widget.visible ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
          ))}
        </div>
      </>
    ) : (
      // Version réduite (juste l'icône)
      <div className="flex items-center justify-center">
        <Settings size={20} className="text-[#003087]" />
      </div>
    )}
  </div>
);

// Composant pour les contrôles de déplacement des widgets
const WidgetMoveControls = ({ widget, onMove, canMoveUp, canMoveDown }: any) => (
  <div className="absolute top-2 left-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
    <button
      onClick={() => onMove(widget.id, 'up')}
      disabled={!canMoveUp}
      className={`p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] transition-colors ${
        canMoveUp 
          ? 'hover:bg-[#F8FAFC] text-[#64748B]' 
          : 'opacity-50 cursor-not-allowed'
      }`}
      title="Déplacer vers le haut"
    >
      <GripVertical size={14} />
    </button>
  </div>
);

export function DashboardPage() {
  const [widgets, setWidgets] = useState<Widget[]>([
    { id: 'stats', title: 'Statistiques', visible: true, size: 'medium', position: 0, icon: TrendingUp },
    { id: 'evolution', title: 'Évolution des tickets', visible: true, size: 'medium', position: 1, icon: Activity },
    { id: 'repartition', title: 'Répartition par niveau', visible: true, size: 'medium', position: 2, icon: Shield },
    { id: 'recent', title: 'Tickets récents', visible: true, size: 'large', position: 3, icon: Users },
    { id: 'alertes', title: 'Alertes IA', visible: true, size: 'medium', position: 4, icon: AlertCircle }
  ]);

  // État pour le panneau de personnalisation
  const [isCustomizationOpen, setIsCustomizationOpen] = useState(true);

  const recentTickets = mockTickets.slice(0, 5);

  const getNiveauBadgeColor = (niveau: string) => {
    switch (niveau) {
      case 'Base': return 'bg-green-100 text-green-800 border-green-300';
      case 'Sensible': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Critique': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatutBadgeColor = (statut: string) => {
    switch (statut) {
      case 'En attente': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Approuvé': return 'bg-green-100 text-green-800 border-green-300';
      case 'Rejeté': return 'bg-red-100 text-red-800 border-red-300';
      case 'Escaladé': return 'bg-orange-100 text-orange-800 border-orange-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // Fonctions de manipulation des widgets
  const toggleWidget = (widgetId: string) => {
    setWidgets(prev => prev.map(w => 
      w.id === widgetId ? { ...w, visible: !w.visible } : w
    ));
  };

  const toggleAllWidgets = (visible: boolean) => {
    setWidgets(prev => prev.map(w => ({ ...w, visible })));
  };

  const resizeWidget = (widgetId: string) => {
    setWidgets(prev => prev.map(w => {
      if (w.id === widgetId) {
        const sizes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large'];
        const currentIndex = sizes.indexOf(w.size);
        const nextSize = sizes[(currentIndex + 1) % sizes.length];
        return { ...w, size: nextSize };
      }
      return w;
    }));
  };

  const moveWidget = (widgetId: string, direction: 'up' | 'down') => {
    setWidgets(prev => {
      const visibleWidgets = prev.filter(w => w.visible);
      const hiddenWidgets = prev.filter(w => !w.visible);
      
      const index = visibleWidgets.findIndex(w => w.id === widgetId);
      if (index === -1) return prev;
      
      if ((direction === 'up' && index === 0) || (direction === 'down' && index === visibleWidgets.length - 1)) {
        return prev;
      }

      const newVisibleWidgets = [...visibleWidgets];
      const swapIndex = direction === 'up' ? index - 1 : index + 1;
      [newVisibleWidgets[index], newVisibleWidgets[swapIndex]] = [newVisibleWidgets[swapIndex], newVisibleWidgets[index]];
      
      // Réassigner les positions
      const reorderedWidgets = [
        ...newVisibleWidgets.map((w, idx) => ({ ...w, position: idx })),
        ...hiddenWidgets.map((w, idx) => ({ ...w, position: newVisibleWidgets.length + idx }))
      ];
      
      return reorderedWidgets;
    });
  };

  const resetLayout = () => {
    setWidgets([
      { id: 'stats', title: 'Statistiques', visible: true, size: 'medium', position: 0, icon: TrendingUp },
      { id: 'evolution', title: 'Évolution des tickets', visible: true, size: 'medium', position: 1, icon: Activity },
      { id: 'repartition', title: 'Répartition par niveau', visible: true, size: 'medium', position: 2, icon: Shield },
      { id: 'recent', title: 'Tickets récents', visible: true, size: 'large', position: 3, icon: Users },
      { id: 'alertes', title: 'Alertes IA', visible: true, size: 'medium', position: 4, icon: AlertCircle }
    ]);
  };

  // Sauvegarder la configuration dans localStorage
  useEffect(() => {
    localStorage.setItem('dashboardWidgets', JSON.stringify(widgets));
  }, [widgets]);

  // Sauvegarder l'état du panneau
  useEffect(() => {
    localStorage.setItem('customizationPanelOpen', JSON.stringify(isCustomizationOpen));
  }, [isCustomizationOpen]);

  // Charger la configuration depuis localStorage
  useEffect(() => {
    const saved = localStorage.getItem('dashboardWidgets');
    if (saved) {
      try {
        const parsedWidgets = JSON.parse(saved);
        // Restaurer les fonctions icon (perdues lors de la sérialisation JSON)
        const restoredWidgets = parsedWidgets.map((w: any) => {
          let icon = TrendingUp; // Default icon
          switch(w.id) {
            case 'stats': icon = TrendingUp; break;
            case 'evolution': icon = Activity; break;
            case 'repartition': icon = Shield; break;
            case 'recent': icon = Users; break;
            case 'alertes': icon = AlertCircle; break;
          }
          return { ...w, icon };
        });
        setWidgets(restoredWidgets);
      } catch (e) {
        console.error('Erreur lors du chargement de la configuration', e);
      }
    }

    // Charger l'état du panneau
    const panelState = localStorage.getItem('customizationPanelOpen');
    if (panelState) {
      try {
        setIsCustomizationOpen(JSON.parse(panelState));
      } catch (e) {
        console.error('Erreur lors du chargement de l\'état du panneau', e);
      }
    }
  }, []);

  // Trier les widgets par position et filtrer les visibles
  const visibleWidgets = widgets.filter(w => w.visible).sort((a, b) => a.position - b.position);
  const totalVisible = visibleWidgets.length;

  // Fonction pour obtenir la classe CSS en fonction de la taille
  const getSizeClass = (size: string) => {
    switch(size) {
      case 'small': return 'col-span-1';
      case 'large': return 'col-span-2';
      default: return 'col-span-1';
    }
  };

  return (
    <div className="space-y-8">
      {/* En-tête */}
      <div>
        <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Tableau de Bord</h1>
        <p className="text-[#64748B]">Vue d'ensemble de la gestion des autorisations</p>
      </div>

      {/* Panneau de contrôle - MODIFIÉ avec flèche */}
      <WidgetControls 
        widgets={widgets.map(w => ({ ...w, onToggle: () => toggleWidget(w.id) }))}
        onToggleAll={toggleAllWidgets}
        onResetLayout={resetLayout}
        isOpen={isCustomizationOpen}
        onToggle={() => setIsCustomizationOpen(!isCustomizationOpen)}
      />

      {/* Grille de widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {visibleWidgets.map((widget, index) => {
          const canMoveUp = index > 0;
          const canMoveDown = index < totalVisible - 1;

          switch(widget.id) {
            case 'stats':
              return (
                <div key={widget.id} className={`${getSizeClass(widget.size)} relative group`}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <StatCard
                      icon={Clock}
                      label="Tickets en attente"
                      value={statsData.ticketsEnAttente}
                      color="text-[#00AEEF]"
                      bgColor="bg-blue-50"
                      onMove={(dir) => moveWidget(widget.id, dir)}
                      onResize={() => resizeWidget(widget.id)}
                      onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible}
                      canMoveUp={canMoveUp}
                      canMoveDown={canMoveDown}
                    />
                    <StatCard
                      icon={CheckCircle}
                      label="Traités aujourd'hui"
                      value={statsData.ticketsTraitesAujourdhui}
                      color="text-[#10B981]"
                      bgColor="bg-green-50"
                      onMove={(dir) => moveWidget(widget.id, dir)}
                      onResize={() => resizeWidget(widget.id)}
                      onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible}
                      canMoveUp={canMoveUp}
                      canMoveDown={canMoveDown}
                    />
                    <StatCard
                      icon={Zap}
                      label="Décisions automatiques IA"
                      value={statsData.decisionsAutomatiquesIA}
                      color="text-[#F59E0B]"
                      bgColor="bg-amber-50"
                      onMove={(dir) => moveWidget(widget.id, dir)}
                      onResize={() => resizeWidget(widget.id)}
                      onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible}
                      canMoveUp={canMoveUp}
                      canMoveDown={canMoveDown}
                    />
                    <StatCard
                      icon={AlertCircle}
                      label="Anomalies détectées"
                      value={statsData.anomaliesDetectees}
                      color="text-[#EF4444]"
                      bgColor="bg-red-50"
                      onMove={(dir) => moveWidget(widget.id, dir)}
                      onResize={() => resizeWidget(widget.id)}
                      onToggleVisibility={() => toggleWidget(widget.id)}
                      isVisible={widget.visible}
                      canMoveUp={canMoveUp}
                      canMoveDown={canMoveDown}
                    />
                  </div>
                </div>
              );

            case 'evolution':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button
                      onClick={() => moveWidget(widget.id, 'up')}
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
                      onClick={() => moveWidget(widget.id, 'down')}
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
                      onClick={() => resizeWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Changer la taille"
                    >
                      <Maximize2 size={14} className="text-[#64748B]" />
                    </button>
                    <button
                      onClick={() => toggleWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Masquer/Afficher"
                    >
                      {widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mb-6">
                    <Activity className="text-[#003087]" size={24} />
                    <h2 className="text-xl font-bold text-[#1E2937]">Évolution des tickets (7 jours)</h2>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={evolutionTickets}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="jour" stroke="#64748B" style={{ fontSize: '12px' }} />
                      <YAxis stroke="#64748B" style={{ fontSize: '12px' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #E2E8F0',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                        }}
                      />
                      <Line type="monotone" dataKey="total" stroke="#003087" strokeWidth={3} dot={{ fill: '#003087', r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              );

            case 'repartition':
              return (
                <div key={widget.id} className={`bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm ${getSizeClass(widget.size)} relative group`}>
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button
                      onClick={() => moveWidget(widget.id, 'up')}
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
                      onClick={() => moveWidget(widget.id, 'down')}
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
                      onClick={() => resizeWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Changer la taille"
                    >
                      <Maximize2 size={14} className="text-[#64748B]" />
                    </button>
                    <button
                      onClick={() => toggleWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Masquer/Afficher"
                    >
                      {widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mb-6">
                    <Shield className="text-[#003087]" size={24} />
                    <h2 className="text-xl font-bold text-[#1E2937]">Répartition par niveau d'accès</h2>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={repartitionNiveaux}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {repartitionNiveaux.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
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
                    <button
                      onClick={() => moveWidget(widget.id, 'up')}
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
                      onClick={() => moveWidget(widget.id, 'down')}
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
                      onClick={() => resizeWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Changer la taille"
                    >
                      <Maximize2 size={14} className="text-[#64748B]" />
                    </button>
                    <button
                      onClick={() => toggleWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Masquer/Afficher"
                    >
                      {widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mb-6">
                    <Users className="text-[#003087]" size={24} />
                    <h2 className="text-xl font-bold text-[#1E2937]">Tickets récents</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-[#E2E8F0]">
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Réf. Ticket</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Demandeur</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Équipe</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Niveau d'accès</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Statut</th>
                          <th className="text-left py-3 px-4 text-sm font-semibold text-[#64748B]">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentTickets.map((ticket) => (
                          <tr key={ticket.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                            <td className="py-3 px-4 font-medium text-[#003087]">{ticket.ref}</td>
                            <td className="py-3 px-4 text-[#1E2937]">{ticket.demandeur}</td>
                            <td className="py-3 px-4 text-[#64748B]">{ticket.equipe}</td>
                            <td className="py-3 px-4">
                              <Badge className={`${getNiveauBadgeColor(ticket.niveauAcces)} border`}>
                                {ticket.niveauAcces}
                              </Badge>
                            </td>
                            <td className="py-3 px-4">
                              <Badge className={`${getStatutBadgeColor(ticket.statut)} border`}>
                                {ticket.statut}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-[#64748B]">{ticket.date}</td>
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
                    <button
                      onClick={() => moveWidget(widget.id, 'up')}
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
                      onClick={() => moveWidget(widget.id, 'down')}
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
                      onClick={() => resizeWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Changer la taille"
                    >
                      <Maximize2 size={14} className="text-[#64748B]" />
                    </button>
                    <button
                      onClick={() => toggleWidget(widget.id)}
                      className="p-1 bg-white rounded-md shadow-sm border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
                      title="Masquer/Afficher"
                    >
                      {widget.visible ? <Eye size={14} className="text-[#64748B]" /> : <EyeOff size={14} className="text-[#64748B]" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mb-6">
                    <AlertCircle className="text-[#EF4444]" size={24} />
                    <h2 className="text-xl font-bold text-[#1E2937]">Alertes IA - Anomalies détectées</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="text-[#EF4444] flex-shrink-0 mt-1" size={20} />
                        <div>
                          <div className="font-semibold text-[#1E2937] mb-1">Demande suspecte détectée</div>
                          <div className="text-sm text-[#64748B] mb-2">
                            Agent Support demande accès Critique à la base Core Banking
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-red-100 text-red-800 border-red-300 border text-xs">TKT-2026-004</Badge>
                            <span className="text-xs text-[#64748B]">Score confiance: 12%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="text-[#F59E0B] flex-shrink-0 mt-1" size={20} />
                        <div>
                          <div className="font-semibold text-[#1E2937] mb-1">Accès inhabituel</div>
                          <div className="text-sm text-[#64748B] mb-2">
                            Demande multi-environnements avec niveau Critique en attente de validation
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-amber-100 text-amber-800 border-amber-300 border text-xs">TKT-2026-002</Badge>
                            <span className="text-xs text-[#64748B]">Escaladé au Super Admin</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );

            default:
              return null;
          }
        })}
      </div>
    </div>
  );
}