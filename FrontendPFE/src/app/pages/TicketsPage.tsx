import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Download, Eye, RefreshCw, XCircle, Brain, ThumbsUp, ChevronLeft, ChevronRight } from 'lucide-react';
import { Badge } from '../components/ui/badge';

interface Ticket {
  id: number;
  ref: string;
  status: string;
  employee_name: string;
  employee_email: string;
  team_name: string;
  role: string;
  description: string;
  requested_environments: string[];
  requested_access_details: any;
  created_at: string;
  rejected_reason?: string;
  rejected_by?: string;
  rejected_at?: string;
  assigned_to?: string;
  // ✅ NOUVEAUX CHAMPS IA
  ai_level?: string;
  ai_confidence?: number;
}

interface UserInfo {
  role: string;
  username: string;
}

export function TicketsPage() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatut, setFilterStatut] = useState('all');
  const [filterNiveau, setFilterNiveau] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [likedTickets, setLikedTickets] = useState<number[]>([]);
  const itemsPerPage = 10;

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

  const fetchTickets = async () => {
    if (!token) {
      setError('Non authentifié');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/tickets?v=2', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des tickets');
      }

      const data = await response.json();
      setTickets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserInfo();
    fetchTickets();
  }, []);

  const filterTicketsByRole = (tickets: Ticket[]): Ticket[] => {
    if (!userInfo) return tickets;
    if (userInfo.role === 'SUPER_ADMIN') return tickets;
    return tickets.filter(ticket => 
      ticket.assigned_to === 'ADMIN' || 
      (ticket.status === 'NEW' && !ticket.assigned_to)
    );
  };

  const getNiveauAcces = (ticket: Ticket): string => {
    // Priorité au niveau IA s'il existe
    if (ticket.ai_level) {
      return ticket.ai_level === 'BASE' ? 'Base' : 
             ticket.ai_level === 'SENSITIVE' ? 'Sensible' : 'Critique';
    }
    const details = ticket.requested_access_details;
    if (details && details.criticite) {
      return details.criticite === 'CRITIQUE' ? 'Critique' : 
             details.criticite === 'SENSIBLE' ? 'Sensible' : 'Base';
    }
    return 'Base';
  };

  const getStatutFrancais = (status: string): string => {
    switch (status) {
      case 'NEW': return 'En attente';
      case 'ASSIGNED': return 'Assigné';
      case 'APPROVED': return 'Approuvé';
      case 'REJECTED': return 'Rejeté';
      case 'CLOSED': return 'Clos';
      default: return status;
    }
  };

  const filteredTickets = filterTicketsByRole(tickets).filter(ticket => {
    const matchesSearch = ticket.ref.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.team_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatut = filterStatut === 'all' || getStatutFrancais(ticket.status) === filterStatut;
    const matchesNiveau = filterNiveau === 'all' || getNiveauAcces(ticket) === filterNiveau;
    return matchesSearch && matchesStatut && matchesNiveau;
  });

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterStatut, filterNiveau]);

  const totalPages = Math.ceil(filteredTickets.length / itemsPerPage) || 1;
  const currentTickets = filteredTickets.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const handleLike = async (ticketId: number) => {
    if (likedTickets.includes(ticketId)) return; // Already liked
    try {
      const response = await fetch(`http://127.0.0.1:8000/feedback/${ticketId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          classification_vote: 'like',
          reason_vote: 'like'
        })
      });
      if (!response.ok) throw new Error('Erreur lors du vote');
      setLikedTickets([...likedTickets, ticketId]);
    } catch (err) {
      console.error('Erreur lors du vote', err);
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

  const getStatutBadgeColor = (statut: string) => {
    switch (statut) {
      case 'En attente': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Approuvé': return 'bg-green-100 text-green-800 border-green-300';
      case 'Rejeté': return 'bg-red-100 text-red-800 border-red-300';
      case 'Assigné': return 'bg-orange-100 text-orange-800 border-orange-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // ✅ CORRECTION : Gérer le cas où level est undefined
  const getAIBadgeColor = (level: string | undefined) => {
    if (!level) return 'bg-gray-100 text-gray-800 border-gray-300';
    switch (level) {
      case 'BASE': return 'bg-green-100 text-green-800 border-green-300';
      case 'SENSITIVE': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // ✅ CORRECTION : Gérer le cas où level est undefined
  const getAIFr = (level: string | undefined) => {
    if (!level) return '-';
    switch (level) {
      case 'BASE': return 'Base';
      case 'SENSITIVE': return 'Sensible';
      case 'CRITICAL': return 'Critique';
      default: return level;
    }
  };

  const syncTickets = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/tickets/sync?v=2', {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Erreur lors de la synchronisation');
      await fetchTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de synchronisation');
    } finally {
      setLoading(false);
    }
  };

  const createTestTicket = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/tickets/simulate/create?v=2', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Erreur lors de la création');
      await fetchTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de création');
    }
  };

  const exportToCSV = () => {
    if (filteredTickets.length === 0) return;

    const headers = ["ID", "Référence", "Demandeur", "Équipe", "Niveau IA", "Confiance", "Statut", "Date"];
    
    const rows = filteredTickets.map(ticket => [
      ticket.id,
      ticket.ref,
      ticket.employee_name,
      ticket.team_name,
      getAIFr(ticket.ai_level),
      ticket.ai_confidence ? `${ticket.ai_confidence}%` : '-',
      getStatutFrancais(ticket.status),
      new Date(ticket.created_at).toLocaleDateString('fr-FR')
    ]);

    const csvContent = [
      headers.join(';'),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(';'))
    ].join('\n');

    // Pour l'encodage correct (Excel UTF-8)
    const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `Export_Tickets_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading && tickets.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003087] mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des tickets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E2937] mb-2">Liste des Tickets</h1>
        <p className="text-[#64748B]">
          Gestion des demandes d'autorisations
          {userInfo && (
            <span className="ml-2 text-sm font-medium">
              ({userInfo.role === 'SUPER_ADMIN' ? 'Super Admin - Vue complète' : 'Admin - Tickets assignés'})
            </span>
          )}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl p-6 border border-[#E2E8F0] shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={20} />
              <input
                type="text"
                placeholder="Rechercher par réf., demandeur, équipe..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <select
              value={filterStatut}
              onChange={(e) => setFilterStatut(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
            >
              <option value="all">Tous les statuts</option>
              <option value="En attente">En attente</option>
              <option value="Approuvé">Approuvé</option>
              <option value="Rejeté">Rejeté</option>
              <option value="Assigné">Assigné</option>
            </select>
          </div>

          <div>
            <select
              value={filterNiveau}
              onChange={(e) => setFilterNiveau(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
            >
              <option value="all">Tous les niveaux</option>
              <option value="Base">Base</option>
              <option value="Sensible">Sensible</option>
              <option value="Critique">Critique</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex justify-between items-center">
          <div className="flex gap-2">
            <button onClick={syncTickets} className="flex items-center gap-2 px-4 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg hover:bg-[#E2E8F0] transition-colors">
              <RefreshCw size={18} /> Synchroniser iTop
            </button>
            <button onClick={createTestTicket} className="flex items-center gap-2 px-4 py-2 bg-[#F59E0B] text-white rounded-lg hover:bg-[#D97706] transition-colors">
              <Brain size={18} /> + Ticket Test
            </button>
          </div>
          <button 
            onClick={exportToCSV}
            disabled={filteredTickets.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-[#003087] text-white rounded-lg hover:bg-[#002066] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={18} /> Exporter CSV
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F8FAFC]">
              <tr className="border-b border-[#E2E8F0]">
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Réf.</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Demandeur</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Équipe</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Niveau IA</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Confiance</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Statut</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Date</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#64748B]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentTickets.map((ticket) => (
                <tr key={ticket.id} className="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors">
                  <td className="py-4 px-6 font-semibold text-[#003087]">{ticket.ref}</td>
                  <td className="py-4 px-6 text-[#1E2937]">{ticket.employee_name}</td>
                  <td className="py-4 px-6 text-[#64748B]">{ticket.team_name}</td>
                  <td className="py-4 px-6">
                    <Badge className={`${getAIBadgeColor(ticket.ai_level)} border`}>
                      <Brain size={12} className="mr-1 inline" />
                      {getAIFr(ticket.ai_level)}
                    </Badge>
                  </td>
                  <td className="py-4 px-6 text-[#64748B]">{ticket.ai_confidence ? `${ticket.ai_confidence}%` : '-'}</td>
                  <td className="py-4 px-6">
                    <Badge className={`${getStatutBadgeColor(getStatutFrancais(ticket.status))} border`}>
                      {getStatutFrancais(ticket.status)}
                    </Badge>
                  </td>
                  <td className="py-4 px-6 text-[#64748B] text-sm">
                    {new Date(ticket.created_at).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="py-4 px-6 flex gap-2">
                    <button
                      onClick={() => navigate(`/ticket/${ticket.id}`)}
                      className="p-2 hover:bg-[#003087] hover:text-white rounded-lg transition-colors text-[#64748B]"
                      title="Voir détails"
                    >
                      <Eye size={18} />
                    </button>
                    {ticket.ai_level && (
                      <button
                        onClick={() => handleLike(ticket.id)}
                        className={`p-2 rounded-lg transition-all duration-300 ${
                          likedTickets.includes(ticket.id)
                            ? 'bg-green-100 text-green-700 pointer-events-none shadow-[0_0_10px_rgba(34,197,94,0.4)] border border-green-200'
                            : 'hover:bg-green-50 hover:text-green-600 text-[#64748B] hover:shadow-sm'
                        }`}
                        title="La classification est parfaite (Like)"
                      >
                        <ThumbsUp size={18} className={likedTickets.includes(ticket.id) ? 'fill-current' : ''} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredTickets.length === 0 && !loading && (
          <div className="text-center py-12 text-[#64748B]">Aucun ticket trouvé</div>
        )}

        <div className="p-4 bg-[#F8FAFC] border-t border-[#E2E8F0] flex items-center justify-between">
          <div className="text-sm text-[#64748B]">
            Affichage de <span className="font-semibold text-[#1E2937]">{currentTickets.length}</span> sur <span className="font-semibold text-[#1E2937]">{filteredTickets.length}</span> tickets
          </div>
          
          {totalPages > 1 && (
            <div className="flex gap-2 items-center">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded hover:bg-[#E2E8F0] disabled:opacity-50 transition"
              >
                <ChevronLeft size={18} />
              </button>
              
              <div className="flex gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum = currentPage;
                  if (currentPage <= 3) pageNum = i + 1;
                  else if (currentPage >= totalPages - 2) pageNum = totalPages - 4 + i;
                  else pageNum = currentPage - 2 + i;
                  
                  if (pageNum < 1 || pageNum > totalPages) return null;
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1 rounded transition-colors ${
                        currentPage === pageNum
                          ? 'bg-[#003087] text-white font-semibold shadow'
                          : 'bg-white hover:bg-[#E2E8F0] text-[#64748B] border border-[#E2E8F0]'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                {totalPages > 5 && currentPage < totalPages - 2 && (
                  <span className="px-2 py-1 text-[#64748B]">...</span>
                )}
              </div>

              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded hover:bg-[#E2E8F0] disabled:opacity-50 transition"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}