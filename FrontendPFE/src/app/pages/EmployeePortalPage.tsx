import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { BiatLogo } from '../components/BiatLogo';

interface Employee {
  id: string;
  name: string;
  team: string;
  role: string;
}

export function EmployeePortalPage() {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  
  const [options, setOptions] = useState<any>({
    systems: [],
    applications: [],
    environments: [],
    access_types: [],
    reasons: [],
    resources: []
  });
  
  const [formData, setFormData] = useState({
    application: '',
    environment: '',
    access_type: '',
    resource: '',
    request_reason: '',
    justification: ''
  });

  useEffect(() => {
    fetchEmployees();
    fetchOptions();
  }, []);

  const fetchOptions = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/portal/options');
      if (response.ok) {
        const data = await response.json();
        setOptions(data);
        
        // Initial setup of defaults if apps exist
        if (data.applications.length > 0) {
          const firstApp = data.applications[0];
          const firstSystem = data.systems.find((s: any) => s.apps.includes(firstApp));
          
          setFormData(prev => ({
            ...prev,
            application: firstApp,
            environment: firstSystem ? firstSystem.envs[0] : data.environments[0],
            access_type: data.access_types[0],
            resource: data.resources[0],
            request_reason: data.reasons[0].id
          }));
        }
      }
    } catch (error) {
      console.error('Erreur chargement options:', error);
    }
  };

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/portal/employees');
      if (response.ok) {
        const data = await response.json();
        setEmployees(data);
      }
    } catch (error) {
      console.error('Erreur chargement employés:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;

    setSubmitting(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/portal/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: selectedEmployee,
          ...formData,
          manager_approval: 'none'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        alert('Erreur lors de la soumission');
      }
    } catch (error) {
      console.error('Erreur soumission:', error);
      alert('Erreur réseau');
    } finally {
      setSubmitting(false);
    }
  };

  const currentEmployee = employees.find(e => e.id === selectedEmployee);

  if (result) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] p-4 flex flex-col items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center">
          <div className="flex justify-center mb-6">
            {result.is_anomalous ? (
              <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="text-amber-500" size={40} />
              </div>
            ) : (
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="text-green-500" size={40} />
              </div>
            )}
          </div>

          <h2 className="text-2xl font-bold text-[#1E2937] mb-2">Demande Soumise</h2>
          <p className="text-[#64748B] mb-6">Référence: {result.ref}</p>

          <div className="bg-slate-50 rounded-xl p-4 text-left space-y-3 mb-8 border border-slate-100">
            <div className="flex justify-between items-center pb-3 border-b border-slate-200">
              <span className="text-[#64748B]">Classification IA</span>
              <span className={`font-bold px-3 py-1 rounded-full text-xs
                ${result.ai_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                  result.ai_level === 'SENSITIVE' ? 'bg-amber-100 text-amber-700' :
                  'bg-green-100 text-green-700'}`}>
                {result.ai_level}
              </span>
            </div>
            {result.is_anomalous && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-[#64748B]">Anomalie Comportementale</span>
                <span className="text-amber-600 font-medium">Détectée ({result.anomaly_severity})</span>
              </div>
            )}
            <div className="flex justify-between items-center text-sm">
              <span className="text-[#64748B]">Soumis le</span>
              <span className="text-[#1E2937] font-medium">{new Date(result.submitted_at).toLocaleString()}</span>
            </div>
          </div>

          <button
            onClick={() => {
              setResult(null);
              setSelectedEmployee('');
            }}
            className="text-[#003087] font-medium hover:underline"
          >
            Nouvelle demande
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center py-10 px-4">
      
      <div className="w-full max-w-3xl mb-8 flex items-center justify-between">
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-[#64748B] hover:text-[#003087] transition-colors font-medium"
        >
          <ArrowLeft size={20} />
          Retour
        </button>
        <BiatLogo />
      </div>

      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-sm border border-[#E2E8F0] overflow-hidden">
        <div className="bg-gradient-to-r from-[#003087] to-[#00AEEF] p-8 text-white">
          <h1 className="text-2xl font-bold mb-2">Portail Collaborateur</h1>
          <p className="text-white/80">Soumettez vos demandes d'habilitation en temps réel</p>
        </div>

        <div className="p-8">
          
          <div className="mb-8">
            <label className="block text-sm font-semibold text-[#1E2937] mb-3">
              1. Identifiez-vous
            </label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl focus:ring-2 focus:ring-[#003087] focus:border-transparent"
              disabled={loading}
            >
              <option value="">-- Sélectionnez votre profil --</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.team} - {emp.role})
                </option>
              ))}
            </select>
          </div>

          {currentEmployee && (
            <form onSubmit={handleSubmit} className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
              <div className="bg-[#F8FAFC] p-6 rounded-2xl border border-[#E2E8F0] flex items-center gap-6 mb-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-full bg-[#003087]/5 -skew-x-12 translate-x-16 group-hover:translate-x-8 transition-transform duration-700" />
                <div className="w-16 h-16 bg-gradient-to-br from-[#003087] to-[#00AEEF] text-white rounded-2xl flex items-center justify-center font-black text-2xl shadow-lg transform -rotate-3 group-hover:rotate-0 transition-transform">
                  {currentEmployee.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-black text-xl text-[#1E2937] leading-tight">{currentEmployee.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-bold bg-[#003087]/10 text-[#003087] px-2 py-0.5 rounded-md uppercase tracking-wider">{currentEmployee.team}</span>
                    <span className="text-xs font-medium text-[#64748B]">•</span>
                    <span className="text-xs font-medium text-[#64748B]">{currentEmployee.role}</span>
                  </div>
                </div>
              </div>

              <label className="block text-sm font-semibold text-[#1E2937] mb-4">
                2. Détails de la demande
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest ml-1">Système / Application</label>
                  <select 
                    className="w-full px-4 py-3 border-2 border-[#E2E8F0] rounded-xl bg-white focus:border-[#003087] focus:ring-0 transition-all font-medium text-[#1E2937]"
                    value={formData.application}
                    onChange={e => {
                      const newApp = e.target.value;
                      const system = options.systems?.find((s: any) => s.apps.includes(newApp));
                      setFormData({
                        ...formData, 
                        application: newApp,
                        environment: system ? system.envs[0] : (options.environments[0] || '')
                      });
                    }}
                  >
                    <option value="" disabled>Sélectionner une application</option>
                    {options.applications.map((app: string) => (
                      <option key={app} value={app}>{app}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest ml-1">Environnement Cible</label>
                  <select 
                    className="w-full px-4 py-3 border-2 border-[#E2E8F0] rounded-xl bg-white focus:border-[#003087] focus:ring-0 transition-all font-medium text-[#1E2937]"
                    value={formData.environment}
                    onChange={e => setFormData({...formData, environment: e.target.value})}
                  >
                    <option value="" disabled>Sélectionner un environnement</option>
                    {(options.systems?.find((s: any) => s.apps.includes(formData.application))?.envs || options.environments).map((env: string) => (
                      <option key={env} value={env}>{env}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest ml-1">Niveau d'Accès</label>
                  <select 
                    className="w-full px-4 py-3 border-2 border-[#E2E8F0] rounded-xl bg-white focus:border-[#003087] focus:ring-0 transition-all font-medium text-[#1E2937]"
                    value={formData.access_type}
                    onChange={e => setFormData({...formData, access_type: e.target.value})}
                  >
                    {options.access_types.map((type: string) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest ml-1">Motif de la Demande</label>
                  <select 
                    className="w-full px-4 py-3 border-2 border-[#E2E8F0] rounded-xl bg-white focus:border-[#003087] focus:ring-0 transition-all font-medium text-[#1E2937]"
                    value={formData.request_reason}
                    onChange={e => setFormData({...formData, request_reason: e.target.value})}
                  >
                    {options.reasons.map((r: any) => (
                      <option key={r.id} value={r.id}>{r.label}</option>
                    ))}
                  </select>
                </div>
                <div className="md:col-span-2 space-y-1">
                  <label className="block text-[10px] font-bold text-[#64748B] uppercase tracking-widest ml-1">Justification Détaillée</label>
                  <textarea 
                    className="w-full px-4 py-3 border-2 border-[#E2E8F0] rounded-xl bg-white focus:border-[#003087] focus:ring-0 transition-all font-medium text-[#1E2937] min-h-[100px]"
                    placeholder="Précisez le contexte de votre demande (n° incident, ticket iTop...)"
                    value={formData.justification}
                    onChange={e => setFormData({...formData, justification: e.target.value})}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-[#E2E8F0] mt-6 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-[#64748B]">
                  <Clock size={16} />
                  <span>Soumission en temps réel (le timestamp actuel sera analysé)</span>
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-[#003087] text-white px-6 py-2.5 rounded-lg font-medium hover:bg-[#002066] transition-colors flex items-center gap-2 disabled:opacity-70"
                >
                  {submitting ? 'Analyse...' : 'Soumettre'}
                  <Send size={16} />
                </button>
              </div>

            </form>
          )}

        </div>
      </div>
    </div>
  );
}
