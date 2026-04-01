import React from 'react';
import { Clock } from 'lucide-react';

interface IdleWarningModalProps {
  isOpen: boolean;
  timeLeft: number;
  onStay: () => void;
  onLogout: () => void;
}

export const IdleWarningModal: React.FC<IdleWarningModalProps> = ({
  isOpen,
  timeLeft,
  onStay,
  onLogout
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
      <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl animate-fadeIn">
        <div className="text-center">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Clock size={32} className="text-yellow-600" />
          </div>
          
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            Session bientôt expirée
          </h3>
          
          <p className="text-gray-600 mb-4">
            Vous allez être déconnecté dans{' '}
            <span className="font-bold text-yellow-600">{timeLeft} seconde{timeLeft > 1 ? 's' : ''}</span>{' '}
            en raison d'inactivité.
          </p>
          
          <div className="flex gap-3">
            <button
              onClick={onLogout}
              className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
            >
              Déconnexion
            </button>
            <button
              onClick={onStay}
              className="flex-1 py-2.5 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors"
            >
              Rester connecté
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};