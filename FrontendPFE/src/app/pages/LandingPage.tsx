import { useNavigate } from 'react-router-dom';
import { Shield, User, ChevronRight, Lock, Sparkles, Zap, Globe, ArrowRight } from 'lucide-react';
import { BiatLogo } from '../components/BiatLogo';

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 relative overflow-hidden">

      {/* Subtle background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top-right accent */}
        <div
          className="absolute -top-24 -right-24 w-[480px] h-[480px] rounded-full opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, #003087, transparent)' }}
        />
        {/* Bottom-left accent */}
        <div
          className="absolute -bottom-24 -left-24 w-[400px] h-[400px] rounded-full opacity-[0.06]"
          style={{ background: 'radial-gradient(circle, #00AEEF, transparent)' }}
        />
        {/* Center faint circle */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full opacity-[0.03]"
          style={{ background: 'radial-gradient(circle, #003087, transparent)' }}
        />
        {/* Subtle grid */}
        <div
          className="absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage: `linear-gradient(#003087 1px, transparent 1px), linear-gradient(90deg, #003087 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        />
        {/* Top decorative bar */}
        <div className="absolute top-0 left-0 right-0 h-1"
          style={{ background: 'linear-gradient(90deg, #003087, #00AEEF, #003087)' }}
        />
      </div>

      <div className="relative w-full max-w-2xl">

        {/* Header section */}
        <div className="text-center mb-14">

          {/* Logo */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div
                className="absolute inset-0 rounded-2xl blur-xl opacity-20"
                style={{ background: 'linear-gradient(135deg, #003087, #00AEEF)' }}
              />
              <div
                className="relative px-6 py-4 rounded-2xl"
                style={{
                  background: 'white',
                  border: '1px solid #E8EDF5',
                  boxShadow: '0 4px 24px rgba(0,48,135,0.10)'
                }}
              >
                <BiatLogo size="large" showText={true} />
              </div>
            </div>
          </div>

          {/* Title */}
          <h1 className="text-[42px] font-black text-[#0D1B3E] mb-3 tracking-tight leading-tight">
            Gestion des <span style={{ color: '#003087' }}>Habilitations</span>
          </h1>

          {/* BIAT tagline */}
          <p className="text-[#5A6478] text-base font-medium mb-8 max-w-md mx-auto leading-relaxed">
            Révolutionner le monde bancaire —{' '}
            <span className="font-bold" style={{ color: '#003087' }}>simple, humain & accessible</span>{' '}
            pour chaque client.
          </p>

          {/* Feature pills */}
          <div className="flex items-center justify-center gap-3 flex-wrap">
            {[
              { icon: <Sparkles size={11} />, label: 'Innovation' },
              { icon: <Zap size={11} />, label: 'Excellence' },
              { icon: <Globe size={11} />, label: 'Accessibilité' },
            ].map((pill, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-wider uppercase"
                style={{
                  background: i === 1 ? '#003087' : '#F0F4FB',
                  color: i === 1 ? '#ffffff' : '#003087',
                  border: i === 1 ? '1px solid #003087' : '1px solid #D0DAEE',
                }}
              >
                {pill.icon}
                {pill.label}
              </span>
            ))}
          </div>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

          {/* Employé card */}
          <button
            id="btn-employee-space"
            onClick={() => navigate('/employee')}
            className="group relative text-left rounded-[24px] p-8 cursor-pointer overflow-hidden transition-all duration-300 hover:-translate-y-1"
            style={{
              background: 'linear-gradient(145deg, #003087 0%, #00529b 100%)',
              boxShadow: '0 8px 30px rgba(0,48,135,0.25)',
              border: '1px solid rgba(0,48,135,0.3)'
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.boxShadow = '0 16px 48px rgba(0,48,135,0.40)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 30px rgba(0,48,135,0.25)';
            }}
          >
            {/* Card inner glow */}
            <div
              className="absolute top-0 right-0 w-48 h-48 -mr-20 -mt-20 rounded-full opacity-20 group-hover:opacity-30 transition-opacity duration-500"
              style={{ background: 'radial-gradient(circle, #00AEEF, transparent)' }}
            />
            <div
              className="absolute bottom-0 left-0 w-32 h-32 -ml-12 -mb-12 rounded-full opacity-10"
              style={{ background: 'radial-gradient(circle, #ffffff, transparent)' }}
            />

            <div className="relative">
              <div className="flex items-start justify-between mb-7">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110"
                  style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.2)' }}
                >
                  <User size={26} className="text-white" />
                </div>
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center opacity-60 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300"
                  style={{ background: 'rgba(255,255,255,0.1)' }}
                >
                  <ChevronRight size={16} className="text-white" />
                </div>
              </div>

              <h2 className="text-[22px] font-extrabold text-white mb-2">Espace Employé</h2>
              <p className="text-white/65 text-sm leading-relaxed mb-7">
                Soumettez vos demandes d'accès et suivez leur traitement en temps réel.
              </p>

              <div className="flex items-center justify-between">
                <span
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold"
                  style={{ background: 'rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.9)', border: '1px solid rgba(255,255,255,0.15)' }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  ACCÈS LIBRE
                </span>
                <span className="text-white/40 text-xs group-hover:text-white/70 transition-colors duration-300 flex items-center gap-1">
                  Continuer <ArrowRight size={12} />
                </span>
              </div>
            </div>
          </button>

          {/* Admin card */}
          <button
            id="btn-admin-login"
            onClick={() => navigate('/login')}
            className="group relative text-left rounded-[24px] p-8 cursor-pointer overflow-hidden transition-all duration-300 hover:-translate-y-1"
            style={{
              background: '#ffffff',
              border: '1.5px solid #E0E8F5',
              boxShadow: '0 4px 20px rgba(0,48,135,0.07)',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.border = '1.5px solid #003087';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 16px 48px rgba(0,48,135,0.14)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.border = '1.5px solid #E0E8F5';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 20px rgba(0,48,135,0.07)';
            }}
          >
            <div
              className="absolute top-0 right-0 w-48 h-48 -mr-20 -mt-20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"
              style={{ background: 'radial-gradient(circle, rgba(0,48,135,0.05), transparent)' }}
            />

            <div className="relative">
              <div className="flex items-start justify-between mb-7">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 group-hover:scale-110"
                  style={{
                    background: 'linear-gradient(135deg, #EEF2FB, #D8E3F5)',
                    border: '1px solid #C5D4EC'
                  }}
                >
                  <Shield size={26} style={{ color: '#003087' }} />
                </div>
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center opacity-40 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300"
                  style={{ background: '#F0F4FB' }}
                >
                  <ChevronRight size={16} style={{ color: '#003087' }} />
                </div>
              </div>

              <h2 className="text-[22px] font-extrabold text-[#0D1B3E] mb-2">Espace Admin</h2>
              <p className="text-[#6B7A99] text-sm leading-relaxed mb-7">
                Tableau de bord, validation des tickets et supervision complète de la plateforme.
              </p>

              <div className="flex items-center justify-between">
                <span
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold"
                  style={{ background: '#F0F4FB', color: '#5A6478', border: '1px solid #D0DAEE' }}
                >
                  <Lock size={9} style={{ color: '#003087' }} />
                  AUTH REQUISE
                </span>
                <span className="text-[#B0BBC8] text-xs group-hover:text-[#003087] transition-colors duration-300 flex items-center gap-1">
                  Continuer <ArrowRight size={12} />
                </span>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-center gap-4 mt-12">
          <div className="h-px flex-1 bg-[#E8EDF5]" />
          <p className="text-[#A8B4C8] text-xs font-medium whitespace-nowrap">
            © BIAT Innovation & Technology 2026
          </p>
          <div className="h-px flex-1 bg-[#E8EDF5]" />
        </div>

      </div>
    </div>
  );
}
