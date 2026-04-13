import { useState, useEffect } from 'react';
import { 
  ScrollText, Download, Search, Filter, FileJson, CheckCircle, XCircle,
  Clock, User, Shield, Database, AlertTriangle, Info, ChevronLeft, ChevronRight,
  RefreshCw, Printer, Brain, X
} from 'lucide-react';
import { Badge } from '../components/ui/badge';

// Interface alignée avec le cahier des charges
interface AuditLog {
  id: string;
  timestamp: Date;
  acteur: string;
  role: 'IA' | 'Admin' | 'Super Admin';
  action: string;
  categorie: 'Ticket' | 'Compte' | 'Accès' | 'Configuration' | 'Sécurité';
  ticketRef?: string;
  environnement: string;
  resultat: 'Succès' | 'Échec' | 'Alerte';
  niveauAcces?: 'Base' | 'Sensible' | 'Critique';
  equipe?: string;
  motif?: string;
  risque?: number;
  details: {
    demande?: any;
    decision?: string;
    ip?: string;
  };
}

// Constantes et utilitaires ont été supprimés pour charger depuis l'API

export function AuditLogsPage() {
  // États pour les filtres
  const [searchTerm, setSearchTerm] = useState('');
  const [filterResultat, setFilterResultat] = useState('all');
  const [filterRole, setFilterRole] = useState('all');
  const [filterCategorie, setFilterCategorie] = useState('all');
  const [filterNiveau, setFilterNiveau] = useState('all');
  const [filterEnvironnement, setFilterEnvironnement] = useState('all');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // États pour la pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  
  // État pour le modal
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  
  // État pour l'export
  const [showExportMessage, setShowExportMessage] = useState(false);

  // État des données
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  // Charger depuis le Backend
  const fetchLogs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://127.0.0.1:8000/audit/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        // Convert dates
        const mapped = data.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp),
          // Mapping back to uppercase Frontend badges
          niveauAcces: item.niveauAcces === 'BASE' ? 'Base' : 
                       item.niveauAcces === 'SENSITIVE' ? 'Sensible' : 
                       item.niveauAcces === 'CRITICAL' ? 'Critique' : item.niveauAcces
        }));
        setLogs(mapped);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des logs', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  // Statistiques pour l'affichage
  const stats = {
    total: logs.length,
    succes: logs.filter(l => l.resultat === 'Succès').length,
    echec: logs.filter(l => l.resultat === 'Échec').length,
    alerte: logs.filter(l => l.resultat === 'Alerte').length,
    ia: logs.filter(l => l.role === 'IA').length,
    critique: logs.filter(l => l.niveauAcces === 'Critique').length
  };

  // Filtrage des logs
  const filteredLogs = logs.filter(log => {
    // Recherche textuelle
    const matchesSearch = 
      (log.ticketRef?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      log.acteur.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.environnement?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (log.equipe?.toLowerCase() || '').includes(searchTerm.toLowerCase());

    // Filtres
    const matchesResultat = filterResultat === 'all' || log.resultat === filterResultat;
    const matchesRole = filterRole === 'all' || log.role === filterRole;
    const matchesCategorie = filterCategorie === 'all' || log.categorie === filterCategorie;
    const matchesNiveau = filterNiveau === 'all' || log.niveauAcces === filterNiveau;
    const matchesEnvironnement = filterEnvironnement === 'all' || log.environnement === filterEnvironnement;
    
    return matchesSearch && matchesResultat && matchesRole && matchesCategorie && 
           matchesNiveau && matchesEnvironnement;
  });

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentLogs = filteredLogs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);

  // Handlers
  const handleExport = () => {
    setShowExportMessage(true);
    setTimeout(() => setShowExportMessage(false), 3000);
  };

  const resetFilters = () => {
    setSearchTerm('');
    setFilterResultat('all');
    setFilterRole('all');
    setFilterCategorie('all');
    setFilterNiveau('all');
    setFilterEnvironnement('all');
    setCurrentPage(1);
  };

  const getResultatBadge = (resultat: string) => {
    switch (resultat) {
      case 'Succès':
        return { className: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle };
      case 'Échec':
        return { className: 'bg-red-100 text-red-800 border-red-300', icon: XCircle };
      case 'Alerte':
        return { className: 'bg-amber-100 text-amber-800 border-amber-300', icon: AlertTriangle };
      default:
        return { className: 'bg-gray-100 text-gray-800 border-gray-300', icon: Info };
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'IA':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'Super Admin':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Admin':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getNiveauBadge = (niveau?: string) => {
    switch (niveau) {
      case 'Base':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'Sensible':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Critique':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="space-y-6 p-6 bg-[#F8FAFC] min-h-screen">
      {/* Message d'export simulé */}
      {showExportMessage && (
        <div className="fixed top-4 right-4 z-50 bg-green-100 border border-green-400 text-green-700 px-6 py-3 rounded-lg shadow-lg animate-slideIn">
          <div className="flex items-center gap-2">
            <Download size={18} />
            <span>Export simulé - {filteredLogs.length} logs exportés</span>
          </div>
        </div>
      )}

      {/* En-tête avec titre conforme au cahier des charges */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[#1E2937] mb-2">
            Audit Logs / Traçabilité Complète
          </h1>
          <p className="text-[#64748B]">
            Journalisation exhaustive de toutes les actions - Conforme aux exigences de sécurité bancaire
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="p-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
            title="Imprimer"
          >
            <Printer size={20} className="text-[#64748B]" />
          </button>
          <button
            onClick={fetchLogs}
            className="p-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
            title="Rafraîchir"
            disabled={loading}
          >
            <RefreshCw size={20} className={`text-[#64748B] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Statistiques clés */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <ScrollText size={20} className="text-[#003087]" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1E2937]">{stats.total}</div>
              <div className="text-xs text-[#64748B]">Total des entrées</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle size={20} className="text-[#10B981]" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1E2937]">{stats.succes}</div>
              <div className="text-xs text-[#64748B]">Succès</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle size={20} className="text-[#EF4444]" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1E2937]">{stats.echec}</div>
              <div className="text-xs text-[#64748B]">Échecs</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Brain size={20} className="text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-[#1E2937]">{stats.ia}</div>
              <div className="text-xs text-[#64748B]">Décisions IA</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filtres */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[#E2E8F0] bg-[#F8FAFC]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter size={20} className="text-[#003087]" />
              <h2 className="font-semibold text-[#1E2937]">Filtres de recherche</h2>
            </div>
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="text-sm text-[#003087] hover:text-[#002066] font-medium"
            >
              {showAdvancedFilters ? 'Masquer' : 'Afficher'} filtres avancés
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Filtres de base */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="relative md:col-span-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={20} />
              <input
                type="text"
                placeholder="Rechercher par ticket, acteur, action, équipe..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-11 pr-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
            </div>

            <select
              value={filterResultat}
              onChange={(e) => {
                setFilterResultat(e.target.value);
                setCurrentPage(1);
              }}
              className="px-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
            >
              <option value="all">Tous les résultats</option>
              <option value="Succès">Succès uniquement</option>
              <option value="Échec">Échecs uniquement</option>
              <option value="Alerte">Alertes uniquement</option>
            </select>
          </div>

          {/* Filtres avancés */}
          {showAdvancedFilters && (
            <div className="space-y-4 pt-4 border-t border-[#E2E8F0]">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <select
                  value={filterRole}
                  onChange={(e) => {
                    setFilterRole(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
                >
                  <option value="all">Tous les rôles</option>
                  <option value="IA">IA</option>
                  <option value="Admin">Admin</option>
                  <option value="Super Admin">Super Admin</option>
                </select>

                <select
                  value={filterCategorie}
                  onChange={(e) => {
                    setFilterCategorie(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
                >
                  <option value="all">Toutes catégories</option>
                  <option value="Ticket">Tickets</option>
                  <option value="Compte">Comptes</option>
                  <option value="Accès">Accès</option>
                  <option value="Configuration">Configuration</option>
                  <option value="Sécurité">Sécurité</option>
                </select>

                <select
                  value={filterNiveau}
                  onChange={(e) => {
                    setFilterNiveau(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
                >
                  <option value="all">Tous niveaux</option>
                  <option value="Base">Base</option>
                  <option value="Sensible">Sensible</option>
                  <option value="Critique">Critique</option>
                </select>

                <select
                  value={filterEnvironnement}
                  onChange={(e) => {
                    setFilterEnvironnement(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-4 py-2.5 bg-white border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087]"
                >
                  <option value="all">Tous environnements</option>
                  <option value="T24 DVH">T24 DVH</option>
                  <option value="T24 INV">T24 INV</option>
                  <option value="T24 DVR">T24 DVR</option>
                  <option value="T24 CRT">T24 CRT</option>
                  <option value="T24 DEV2">T24 DEV2</option>
                  <option value="T24 QL2">T24 QL2</option>
                  <option value="PRD">PROD</option>
                  <option value="PREPROD">PREPROD</option>
                </select>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={resetFilters}
                  className="px-4 py-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors text-[#64748B] text-sm"
                >
                  Réinitialiser
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Boutons d'action */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors text-[#64748B]"
        >
          <Filter size={18} />
          Filtres avancés
        </button>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors"
        >
          <Download size={18} />
          Exporter les logs
        </button>
      </div>

      {/* Tableau des logs */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F8FAFC]">
              <tr className="border-b border-[#E2E8F0]">
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Date & Heure</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Acteur</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Rôle</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Action</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Catégorie</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Ticket</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Environnement</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Niveau</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Résultat</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Détails</th>
              </tr>
            </thead>
            <tbody>
              {currentLogs.map((log) => {
                const ResultatIcon = getResultatBadge(log.resultat).icon;
                return (
                  <tr key={log.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <Clock size={14} className="text-[#64748B]" />
                        <div>
                          <div className="text-sm font-medium text-[#1E2937]">
                            {new Date(log.timestamp).toLocaleDateString('fr-FR')}
                          </div>
                          <div className="text-xs text-[#64748B]">
                            {new Date(log.timestamp).toLocaleTimeString('fr-FR')}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <User size={14} className="text-[#64748B]" />
                        <span className="text-sm font-medium text-[#1E2937]">{log.acteur}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <Badge className={`${getRoleBadge(log.role)} border text-xs`}>
                        {log.role}
                      </Badge>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm text-[#1E2937]">{log.action}</span>
                    </td>
                    <td className="py-4 px-6">
                      <Badge className="bg-gray-100 text-gray-800 border-gray-300 text-xs">
                        {log.categorie}
                      </Badge>
                    </td>
                    <td className="py-4 px-6">
                      {log.ticketRef ? (
                        <span className="text-sm font-semibold text-[#003087]">{log.ticketRef}</span>
                      ) : (
                        <span className="text-sm text-[#64748B]">-</span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-1">
                        <Database size={14} className="text-[#64748B]" />
                        <span className="text-sm text-[#1E2937]">{log.environnement}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      {log.niveauAcces && (
                        <Badge className={`${getNiveauBadge(log.niveauAcces)} border text-xs`}>
                          {log.niveauAcces}
                        </Badge>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <Badge className={`${getResultatBadge(log.resultat).className} border text-xs flex items-center gap-1 w-fit`}>
                        <ResultatIcon size={12} />
                        {log.resultat}
                      </Badge>
                      {log.risque && log.risque > 70 && (
                        <div className="mt-1 text-xs text-red-600 font-semibold">
                          Risque élevé: {log.risque}%
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="p-2 hover:bg-[#003087] hover:text-white rounded-lg transition-colors text-[#64748B]"
                        title="Voir les détails"
                      >
                        <FileJson size={18} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 bg-[#F8FAFC] border-t border-[#E2E8F0] flex items-center justify-between">
          <div className="text-sm text-[#64748B]">
            Affichage <span className="font-semibold text-[#1E2937]">{indexOfFirstItem + 1}</span> à{' '}
            <span className="font-semibold text-[#1E2937]">
              {Math.min(indexOfLastItem, filteredLogs.length)}
            </span>{' '}
            sur <span className="font-semibold text-[#1E2937]">{filteredLogs.length}</span> entrées
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className={`p-2 border border-[#E2E8F0] rounded-lg transition-colors ${
                currentPage === 1 
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                  : 'bg-white hover:bg-[#F8FAFC] text-[#64748B]'
              }`}
            >
              <ChevronLeft size={18} />
            </button>
            
            {[...Array(totalPages)].map((_, i) => {
              const pageNum = i + 1;
              if (
                pageNum === 1 ||
                pageNum === totalPages ||
                (pageNum >= currentPage - 2 && pageNum <= currentPage + 2)
              ) {
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-4 py-2 border border-[#E2E8F0] rounded-lg transition-colors ${
                      currentPage === pageNum
                        ? 'bg-[#003087] text-white border-[#003087]'
                        : 'bg-white hover:bg-[#F8FAFC] text-[#64748B]'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              } else if (
                pageNum === currentPage - 3 ||
                pageNum === currentPage + 3
              ) {
                return <span key={pageNum} className="px-2 self-center text-[#64748B]">...</span>;
              }
              return null;
            })}

            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className={`p-2 border border-[#E2E8F0] rounded-lg transition-colors ${
                currentPage === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white hover:bg-[#F8FAFC] text-[#64748B]'
              }`}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Modal Détails - Transparent */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
          <div className="absolute inset-0 bg-transparent" />
          <div className="relative bg-white/95 backdrop-blur-sm rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl border-2 border-[#E2E8F0] pointer-events-auto">
            <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileJson className="text-[#003087]" size={24} />
                <h3 className="text-xl font-bold text-[#1E2937]">Détails complets de l'audit</h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors"
              >
                <X size={20} className="text-[#64748B]" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(80vh-180px)]">
              <div className="space-y-4">
                {/* Informations générales */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#F8FAFC] p-3 rounded-lg">
                    <div className="text-xs text-[#64748B] mb-1">ID du Log</div>
                    <div className="text-sm font-mono text-[#1E2937]">{selectedLog.id}</div>
                  </div>
                  <div className="bg-[#F8FAFC] p-3 rounded-lg">
                    <div className="text-xs text-[#64748B] mb-1">Timestamp</div>
                    <div className="text-sm font-mono text-[#1E2937]">{selectedLog.timestamp.toISOString()}</div>
                  </div>
                </div>

                {/* Informations de sécurité */}
                {selectedLog.risque && (
                  <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                    <h4 className="text-sm font-semibold text-[#1E2937] mb-3 flex items-center gap-2">
                      <Shield size={16} className="text-[#F59E0B]" />
                      Informations de sécurité
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-[#64748B]">Score de risque</div>
                        <div className="text-sm font-semibold">
                          <Badge className={selectedLog.risque > 70 ? 'bg-red-100 text-red-800' : 
                                         selectedLog.risque > 40 ? 'bg-amber-100 text-amber-800' : 
                                         'bg-green-100 text-green-800'}>
                            {selectedLog.risque}%
                          </Badge>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-[#64748B]">Motif (si échec)</div>
                        <div className="text-sm text-[#1E2937]">{selectedLog.motif || 'Aucun'}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* JSON Complet */}
                <div>
                  <h4 className="text-sm font-semibold text-[#1E2937] mb-3">Payload JSON complet</h4>
                  <pre className="bg-[#1E2937] text-[#10B981] p-4 rounded-lg overflow-x-auto text-xs font-mono">
{JSON.stringify(
  {
    id: selectedLog.id,
    timestamp: selectedLog.timestamp.toISOString(),
    acteur: selectedLog.acteur,
    role: selectedLog.role,
    categorie: selectedLog.categorie,
    action: selectedLog.action,
    ticketRef: selectedLog.ticketRef,
    environnement: selectedLog.environnement,
    niveauAcces: selectedLog.niveauAcces,
    resultat: selectedLog.resultat,
    risque: selectedLog.risque,
    motif: selectedLog.motif,
    equipe: selectedLog.equipe,
    details: selectedLog.details
  },
  null,
  2
)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-[#E2E8F0] bg-[#F8FAFC]">
              <button
                onClick={() => setSelectedLog(null)}
                className="w-full py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}