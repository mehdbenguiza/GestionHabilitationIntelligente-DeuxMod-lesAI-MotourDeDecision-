import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ArrowLeft, Key, CheckCircle, AlertCircle, Lock, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { BiatLogo } from '../components/BiatLogo';

type Step = 'email' | 'otp' | 'newPassword' | 'success';

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

  // Fonction pour valider la force du mot de passe
  const validatePasswordStrength = (password: string): { isValid: boolean; message: string } => {
    const checks = {
      minLength: password.length >= 8,
      maxLength: password.length <= 72, // Ajout de la limite max
      hasUpperCase: /[A-Z]/.test(password),
      hasLowerCase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    if (!checks.minLength) {
      return { isValid: false, message: 'Minimum 8 caractères' };
    }
    if (!checks.maxLength) {
      return { isValid: false, message: 'Maximum 72 caractères (limite technique)' };
    }
    if (!checks.hasUpperCase) {
      return { isValid: false, message: 'Au moins une majuscule' };
    }
    if (!checks.hasLowerCase) {
      return { isValid: false, message: 'Au moins une minuscule' };
    }
    if (!checks.hasNumber) {
      return { isValid: false, message: 'Au moins un chiffre' };
    }
    if (!checks.hasSpecialChar) {
      return { isValid: false, message: 'Au moins un caractère spécial (!@#$%^&*)' };
    }

    return { isValid: true, message: 'Mot de passe fort' };
  };

  // Envoyer l'email de réinitialisation
  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/forgot-password/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erreur lors de l\'envoi de l\'email');
      }

      setSuccessMessage(data.message || 'Code envoyé avec succès');
      
      setTimeout(() => {
        setCurrentStep('otp');
        startTimer();
        setSuccessMessage('');
      }, 1500);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  // Démarrer le timer pour le renvoi d'OTP
  const startTimer = () => {
    setTimer(60);
    setCanResend(false);
    const interval = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Vérifier l'OTP
  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const otpString = otp.join('');
    if (otpString.length !== 6) {
      setError('Veuillez entrer le code à 6 chiffres');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/forgot-password/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email, 
          code: otpString 
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Code invalide');
      }

      setResetToken(data.reset_token);
      setSuccessMessage('Code vérifié avec succès');
      
      setTimeout(() => {
        setCurrentStep('newPassword');
        setSuccessMessage('');
      }, 1000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  // Renvoyer l'OTP
  const handleResendOTP = async () => {
    if (!canResend) return;
    
    setOtp(['', '', '', '', '', '']);
    setError('');
    setSuccessMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/forgot-password/resend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erreur lors du renvoi');
      }

      setSuccessMessage('Nouveau code envoyé');
      startTimer();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  // Réinitialiser le mot de passe
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Valider le mot de passe
    const passwordValidation = validatePasswordStrength(newPassword);
    if (!passwordValidation.isValid) {
      setError(passwordValidation.message);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/forgot-password/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email, 
          new_password: newPassword,
          reset_token: resetToken
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erreur lors de la réinitialisation');
      }

      setSuccessMessage('Mot de passe réinitialisé avec succès !');
      
      setTimeout(() => {
        setCurrentStep('success');
        setSuccessMessage('');
      }, 1500);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  // Gérer la saisie OTP
  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  // Calculer la force du mot de passe
  const getPasswordStrength = () => {
    const checks = {
      minLength: newPassword.length >= 8,
      maxLength: newPassword.length <= 72, // Ajout de la limite max
      hasUpperCase: /[A-Z]/.test(newPassword),
      hasLowerCase: /[a-z]/.test(newPassword),
      hasNumber: /[0-9]/.test(newPassword),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(newPassword)
    };

    const score = Object.values(checks).filter(Boolean).length;
    
    if (score <= 2) return { label: 'Faible', color: 'text-red-500', bg: 'bg-red-500', width: '20%' };
    if (score <= 3) return { label: 'Moyen', color: 'text-orange-500', bg: 'bg-orange-500', width: '40%' };
    if (score <= 4) return { label: 'Bon', color: 'text-yellow-500', bg: 'bg-yellow-500', width: '60%' };
    if (score <= 5) return { label: 'Très bon', color: 'text-blue-500', bg: 'bg-blue-500', width: '80%' };
    return { label: 'Fort', color: 'text-green-500', bg: 'bg-green-500', width: '100%' };
  };

  // Afficher l'étape correspondante
  const renderStep = () => {
    switch (currentStep) {
      case 'email':
        return (
          <>
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                <Mail size={32} className="text-[#003087]" />
              </div>
              <h1 className="text-2xl font-bold text-[#1E2937] mb-2">
                Mot de passe oublié
              </h1>
              <p className="text-sm text-[#64748B]">
                Saisissez votre adresse email pour recevoir un code de récupération
              </p>
            </div>

            <form onSubmit={handleSendEmail} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-[#1E2937] mb-2">
                  Adresse email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                  placeholder="exemple@biat-it.com.tn"
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} className="text-[#EF4444]" />
                  <span className="text-sm text-[#EF4444]">{error}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                  <CheckCircle size={16} className="text-[#10B981]" />
                  <span className="text-sm text-[#10B981]">{successMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || !email}
                className="w-full py-3 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <RefreshCw size={20} className="animate-spin" />
                    Envoi en cours...
                  </>
                ) : (
                  'Envoyer le code'
                )}
              </button>

              <button
                type="button"
                onClick={() => navigate('/login')}
                className="w-full flex items-center justify-center gap-2 text-sm text-[#64748B] hover:text-[#003087] transition-colors"
              >
                <ArrowLeft size={16} />
                Retour à la connexion
              </button>
            </form>
          </>
        );

      case 'otp':
        return (
          <>
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                <Key size={32} className="text-[#003087]" />
              </div>
              <h1 className="text-2xl font-bold text-[#1E2937] mb-2">
                Vérification
              </h1>
              <p className="text-sm text-[#64748B]">
                Nous avons envoyé un code à 6 chiffres à <span className="font-semibold text-[#003087]">{email}</span>
              </p>
            </div>

            <form onSubmit={handleVerifyOTP} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-[#1E2937] mb-4 text-center">
                  Code de vérification
                </label>
                <div className="flex justify-center gap-2">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-${index}`}
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e)}
                      className="w-12 h-12 text-center text-xl font-semibold bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent"
                      required
                    />
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} className="text-[#EF4444]" />
                  <span className="text-sm text-[#EF4444]">{error}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                  <CheckCircle size={16} className="text-[#10B981]" />
                  <span className="text-sm text-[#10B981]">{successMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || otp.some(d => !d)}
                className="w-full py-3 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Vérification...' : 'Vérifier le code'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={!canResend || isLoading}
                  className="text-sm text-[#003087] hover:text-[#00AEEF] font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {canResend ? 'Renvoyer le code' : `Renvoyer dans ${timer}s`}
                </button>
              </div>

              <button
                type="button"
                onClick={() => setCurrentStep('email')}
                className="w-full flex items-center justify-center gap-2 text-sm text-[#64748B] hover:text-[#003087] transition-colors"
              >
                <ArrowLeft size={16} />
                Modifier l'email
              </button>
            </form>
          </>
        );

      case 'newPassword':
        const passwordStrength = getPasswordStrength();
        
        return (
          <>
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                <Lock size={32} className="text-[#003087]" />
              </div>
              <h1 className="text-2xl font-bold text-[#1E2937] mb-2">
                Nouveau mot de passe
              </h1>
              <p className="text-sm text-[#64748B]">
                Choisissez un nouveau mot de passe sécurisé (8-72 caractères)
              </p>
            </div>

            <form onSubmit={handleResetPassword} className="space-y-5">
              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-[#1E2937] mb-2">
                  Nouveau mot de passe
                </label>
                <div className="relative">
                  <input
                    id="newPassword"
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value.slice(0, 72))} // Limite à 72 caractères
                    className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    placeholder="8-72 caractères"
                    maxLength={72} // Limite HTML
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#003087]"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                <div className="text-right text-xs text-[#64748B] mt-1">
                  {newPassword.length}/72 caractères
                </div>
                
                {newPassword && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-[#64748B]">Force du mot de passe:</span>
                      <span className={`text-xs font-semibold ${passwordStrength.color}`}>
                        {passwordStrength.label}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${passwordStrength.bg} transition-all`}
                        style={{ width: passwordStrength.width }}
                      />
                    </div>
                    <ul className="mt-3 text-xs text-[#64748B] space-y-1">
                      <li className={newPassword.length >= 8 ? 'text-green-600' : ''}>
                        ✓ Minimum 8 caractères ({newPassword.length}/8)
                      </li>
                      <li className={newPassword.length <= 72 ? 'text-green-600' : ''}>
                        ✓ Maximum 72 caractères ({newPassword.length}/72)
                      </li>
                      <li className={/[A-Z]/.test(newPassword) ? 'text-green-600' : ''}>
                        ✓ Au moins une majuscule
                      </li>
                      <li className={/[a-z]/.test(newPassword) ? 'text-green-600' : ''}>
                        ✓ Au moins une minuscule
                      </li>
                      <li className={/[0-9]/.test(newPassword) ? 'text-green-600' : ''}>
                        ✓ Au moins un chiffre
                      </li>
                      <li className={/[!@#$%^&*(),.?":{}|<>]/.test(newPassword) ? 'text-green-600' : ''}>
                        ✓ Au moins un caractère spécial (!@#$%^&*)
                      </li>
                    </ul>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#1E2937] mb-2">
                  Confirmer le mot de passe
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value.slice(0, 72))}
                    className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003087] focus:border-transparent pr-12"
                    placeholder="Confirmez votre mot de passe"
                    maxLength={72}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#003087]"
                  >
                    {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">Les mots de passe ne correspondent pas</p>
                )}
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} className="text-[#EF4444]" />
                  <span className="text-sm text-[#EF4444]">{error}</span>
                </div>
              )}

              {successMessage && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
                  <CheckCircle size={16} className="text-[#10B981]" />
                  <span className="text-sm text-[#10B981]">{successMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <RefreshCw size={20} className="animate-spin" />
                    Réinitialisation...
                  </>
                ) : (
                  'Réinitialiser le mot de passe'
                )}
              </button>
            </form>
          </>
        );

      case 'success':
        return (
          <>
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-50 rounded-full mb-4">
                <CheckCircle size={32} className="text-[#10B981]" />
              </div>
              <h1 className="text-2xl font-bold text-[#1E2937] mb-2">
                Mot de passe modifié !
              </h1>
              <p className="text-sm text-[#64748B]">
                Votre mot de passe a été réinitialisé avec succès
              </p>
            </div>

            <button
              onClick={() => navigate('/login')}
              className="w-full py-3 bg-[#003087] text-white rounded-lg font-semibold hover:bg-[#002066] transition-colors shadow-lg hover:shadow-xl"
            >
              Se connecter
            </button>
          </>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#003087] via-[#004099] to-[#00AEEF] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-2xl p-8">
          <div className="flex justify-center mb-8">
            <BiatLogo size="large" showText={true} />
          </div>

          {renderStep()}
        </div>

        <p className="text-center text-sm text-white mt-6 opacity-90">
          © BIAT 2026 - Tous droits réservés
        </p>
      </div>
    </div>
  );
}