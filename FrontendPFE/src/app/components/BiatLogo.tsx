import { type FC } from 'react';
import biatLogo from '../../images/Biat.png';  // Chemin correct depuis src/app/ui/

interface BiatLogoProps {
  size?: 'small' | 'medium' | 'large' | 'xlarge';  // Ajout d'une taille extra-large
  showText?: boolean;
  className?: string;
}

export const BiatLogo: FC<BiatLogoProps> = ({
  size = 'medium',
  showText = false,          // Par défaut sans texte pour un logo plus clean/visible
  className = '',
}) => {
  const sizes = {
    small:  'h-16 w-auto',     // ~64px → un peu plus grand que avant
    medium: 'h-24 w-auto',     // ~96px → bon pour navbar ou sidebar
    large:  'h-32 w-auto',     // ~128px → bien visible dans header ou page
    xlarge: 'h-48 w-auto',     // ~192px → très grand, pour splashscreen ou hero
  };

  const sizeClass = sizes[size] || 'h-24 w-auto'; // fallback medium

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <img
        src={biatLogo}
        alt="Logo BIAT - Banque Internationale Arabe de Tunisie"
        className={`${sizeClass} object-contain drop-shadow-md`} // Ajout d'une légère ombre pour plus de visibilité
      />

      
      
    </div>
  );
};