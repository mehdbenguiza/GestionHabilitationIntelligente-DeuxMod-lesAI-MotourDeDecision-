import { useState, useRef, useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import { Search, Bell, User, LogOut, ChevronDown, AlertCircle } from 'lucide-react';
import { BiatLogo } from './BiatLogo';
import { useSidebar } from '../contexts/SidebarContext';

interface Notification {
  id: string;
  title: string;
  timestamp: string;
  read: boolean;
  type: 'info' | 'warning' | 'danger';
}

const mockNotifications: Notification[] = [
  { id: '1', title: 'Nouveau ticket critique escaladé', timestamp: 'Il y a 5 min', read: false, type: 'danger' },
  { id: '2', title: 'Anomalie IA détectée sur ticket TKT-2026-004', timestamp: 'Il y a 15 min', read: false, type: 'warning' },
  { id: '3', title: 'Ticket TKT-2026-003 approuvé automatiquement', timestamp: 'Il y a 1h', read: true, type: 'info' },
  { id: '4', title: 'Nouvel admin ajouté au système', timestamp: 'Il y a 2h', read: true, type: 'info' },
  { id: '5', title: 'Mise à jour du modèle IA terminée', timestamp: 'Il y a 3h', read: true, type: 'info' }
];

export function Topbar() {
  const navigate = useNavigate();
  const { isCollapsed } = useSidebar();

  // ==================== DONNÉES RÉELLES DE L'UTILISATEUR ====================
  const [userName, setUserName] = useState('Chargement...');
  const [userRole, setUserRole] = useState('');
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // États existants
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  // ==================== FETCH DU USER CONNECTÉ & NOTIFICATIONS ====================
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setUserName('Non connecté');
      setLoadingUser(false);
      return;
    }

    // Fetch user info
    fetch('http://127.0.0.1:8000/users/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
      .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(data => {
        setUserName(data.fullName);
        setUserRole(data.role === 'SUPER_ADMIN' ? 'Super Admin' : 'Admin');
        setProfileImage(data.profile_image || null);
        setLoadingUser(false);
      })
      .catch(() => {
        setUserName('Erreur de chargement');
        setLoadingUser(false);
      });

    // Fetch notifications
    const fetchNotifications = () => {
      fetch('http://127.0.0.1:8000/notifications/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      .then(res => res.json())
      .then(data => {
         if (Array.isArray(data)) setNotifications(data);
      })
      .catch(console.error);
    };

    fetchNotifications();
    const intervalId = setInterval(fetchNotifications, 15000); // Polling toutes les 15s

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAsRead = (notif: Notification) => {
    if (notif.read) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch(`http://127.0.0.1:8000/notifications/${notif.id}/read`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }).then(res => {
      if(res.ok) {
        setNotifications(notifications.map(n => n.id === notif.id ? { ...n, read: true } : n));
      }
    }).catch(console.error);
  };

  const markAllAsRead = () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch('http://127.0.0.1:8000/notifications/read-all', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }).then(() => {
      setNotifications(notifications.map(n => ({ ...n, read: true })));
    }).catch(console.error);
  };

  return (
    <header
      className="fixed top-0 right-0 h-16 bg-white border-b border-[#E2E8F0] z-50 flex items-center px-6 transition-all duration-300"
      style={{ left: isCollapsed ? '60px' : '280px', right: 0 }}
    >
      {/* Logo petit */}
      <div className="flex-shrink-0">
        <BiatLogo size="small" showText={false} />
      </div>

      {/* Contenu du topbar */}
      <div className="flex-1 flex items-center justify-between gap-6">
        {/* Barre de recherche */}
        <div className="flex-1 max-w-md ml-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={20} />
            <input
              type="text"
              placeholder="Rechercher un ticket, utilisateur..."
              className="w-full pl-11 pr-4 py-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent text-sm"
            />
          </div>
        </div>

        {/* Actions droite */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors"
            >
              <Bell size={20} className="text-[#64748B]" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-[#EF4444] text-white text-xs rounded-full flex items-center justify-center font-semibold">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Dropdown Notifications */}
            {showNotifications && (
              <div className="absolute right-0 top-12 w-[350px] bg-white rounded-xl shadow-2xl border border-[#E2E8F0] overflow-hidden z-50">
                <div className="p-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8FAFC]">
                  <h3 className="font-semibold text-[#1E2937]">Notifications</h3>
                  {unreadCount > 0 && (
                    <button 
                      onClick={markAllAsRead}
                      className="text-xs text-[#003087] font-medium hover:underline px-2 py-1 hover:bg-blue-50 rounded transition-colors"
                    >
                      Tout marquer comme lu
                    </button>
                  )}
                </div>
                <div className="max-h-[400px] overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-8 text-center text-[#64748B]">
                      <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Bell size={20} className="text-gray-400" />
                      </div>
                      <p className="text-sm">Aucune notification</p>
                    </div>
                  ) : (
                    notifications.map((notif: any) => (
                      <div 
                        key={notif.id} 
                        onClick={() => markAsRead(notif)}
                        className={`p-4 border-b border-[#E2E8F0] last:border-0 hover:bg-[#F8FAFC] transition-colors cursor-pointer ${
                          !notif.read ? 'bg-blue-50/30' : ''
                        }`}
                      >
                        <div className="flex gap-3">
                          <div className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                            notif.type === 'danger' ? 'bg-red-100 text-red-600' :
                            notif.type === 'warning' ? 'bg-amber-100 text-amber-600' :
                            notif.type === 'success' ? 'bg-green-100 text-green-600' :
                            'bg-blue-100 text-blue-600'
                          }`}>
                            <AlertCircle size={16} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm text-[#1E2937] ${!notif.read ? 'font-semibold' : ''}`}>
                              {notif.title}
                            </p>
                            <p className="text-xs text-[#64748B] mt-1 line-clamp-2">
                              {notif.message}
                            </p>
                            <p className="text-[10px] text-[#94A3B8] mt-2">
                              {notif.timestamp ? new Date(notif.timestamp).toLocaleString('fr-FR') : 'À l\'instant'}
                            </p>
                          </div>
                          {!notif.read && (
                            <div className="w-2 h-2 bg-[#003087] rounded-full mt-2"></div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Profil utilisateur */}
          <div className="relative pl-4 border-l border-[#E2E8F0]" ref={profileRef}>
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-3 hover:bg-[#F8FAFC] px-3 py-2 rounded-lg transition-colors"
            >
              <div className="text-right">
                <div className="text-sm font-semibold text-[#1E2937]">
                  {loadingUser ? 'Chargement...' : userName}
                </div>
                <div className="text-xs text-[#64748B]">{userRole}</div>
              </div>
              {profileImage ? (
                <img 
                  src={`http://127.0.0.1:8000${profileImage}`} 
                  alt="Profile" 
                  className="w-10 h-10 rounded-full object-cover border border-gray-200"
                />
              ) : (
                <div className="w-10 h-10 bg-[#003087] rounded-full flex items-center justify-center">
                  <User size={20} className="text-white" />
                </div>
              )}
              <ChevronDown size={16} className="text-[#64748B]" />
            </button>

            {/* Dropdown Menu */}
            {showProfileMenu && (
              <div className="absolute right-0 top-14 w-48 bg-white rounded-lg shadow-xl border border-[#E2E8F0] overflow-hidden z-50">
                <button
                  onClick={() => {
                    navigate('/profile');
                    setShowProfileMenu(false);
                  }}
                  className="w-full px-4 py-3 text-left hover:bg-[#F8FAFC] transition-colors flex items-center gap-3 text-[#1E2937]"
                >
                  <User size={18} />
                  <span className="font-medium">Voir Profil</span>
                </button>
                <div className="border-t border-[#E2E8F0]"></div>
                <button
                  onClick={async () => {
                    const token = localStorage.getItem('token');
                    if (token) {
                      try {
                        await fetch('http://127.0.0.1:8000/auth/logout', {
                          method: 'POST',
                          headers: { 'Authorization': `Bearer ${token}` }
                        });
                      } catch (e) {
                        console.error('Logout error', e);
                      }
                    }
                    localStorage.removeItem('token');
                    navigate('/');
                    setShowProfileMenu(false);
                  }}
                  className="w-full px-4 py-3 text-left hover:bg-red-50 transition-colors flex items-center gap-3 text-[#EF4444]"
                >
                  <LogOut size={18} />
                  <span className="font-medium">Déconnexion</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}