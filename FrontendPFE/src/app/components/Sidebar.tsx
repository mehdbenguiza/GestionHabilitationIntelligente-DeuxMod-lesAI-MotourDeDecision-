// src/app/components/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import { Home, FileText, Shield, ScrollText, Users, User, Menu, FlaskConical, Key } from 'lucide-react';
import { BiatLogo } from './BiatLogo';
import { useSidebar } from '../contexts/SidebarContext';

const navItems = [
  { path: '/dashboard', label: 'Accueil', icon: Home },
  { path: '/tickets', label: 'Tickets', icon: FileText },
  { path: '/habilitations', label: 'Habilitations', icon: Key },
  { path: '/supervision', label: 'Supervision IA', icon: Shield },
  { path: '/ai-lab', label: 'Lab IA', icon: FlaskConical },
  { path: '/audit-logs', label: 'Audit Logs', icon: ScrollText },
  { path: '/admins', label: 'Gestion Admins', icon: Users },
  { path: '/profile', label: 'Mon Profil', icon: User },
];

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar();

  return (
    <aside
      className={`${
        isCollapsed ? 'w-[60px]' : 'w-[280px]'
      } h-screen bg-white border-r border-[#E2E8F0] fixed left-0 top-0 flex flex-col transition-all duration-300`}
    >
      {/* Logo et toggle alignés horizontalement */}
      <div className="p-4 border-b border-[#E2E8F0] flex items-center justify-center gap-2">
        {/* Logo Biat grand */}
        <BiatLogo size="large" showText={!isCollapsed} />

        {/* Bouton toggle à côté */}
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-[#F8FAFC] rounded-lg transition-colors"
          title={isCollapsed ? 'Développer' : 'Réduire'}
        >
          <Menu size={20} className="text-[#64748B]" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-6 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center ${isCollapsed ? 'justify-center px-2' : 'gap-3 px-4'} py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-[#003087] text-white shadow-md'
                  : 'text-[#64748B] hover:bg-[#F8FAFC] hover:text-[#003087]'
              }`
            }
            title={isCollapsed ? item.label : ''}
          >
            <item.icon size={20} />
            {!isCollapsed && <span className="font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}