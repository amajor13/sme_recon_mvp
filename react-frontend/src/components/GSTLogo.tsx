import React from 'react';

interface GSTLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const GSTLogo: React.FC<GSTLogoProps> = ({ size = 'md', className = '' }) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'w-8 h-8';
      case 'md':
        return 'w-10 h-10';
      case 'lg':
        return 'w-12 h-12';
      case 'xl':
        return 'w-16 h-16';
      default:
        return 'w-10 h-10';
    }
  };

  return (
    <div className={`${getSizeClasses()} ${className} relative`}>
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Background Circle with Gradient */}
        <defs>
          <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
          <linearGradient id="textGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#E5E7EB" />
          </linearGradient>
        </defs>
        
        {/* Main Circle Background */}
        <circle
          cx="32"
          cy="32"
          r="30"
          fill="url(#bgGradient)"
          stroke="#1E40AF"
          strokeWidth="2"
        />
        
        {/* Inner Circle for Depth */}
        <circle
          cx="32"
          cy="32"
          r="26"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="1"
          opacity="0.3"
        />
        
        {/* GST Text */}
        <text
          x="32"
          y="38"
          fontFamily="Arial, sans-serif"
          fontSize="16"
          fontWeight="bold"
          textAnchor="middle"
          fill="url(#textGradient)"
        >
          GST
        </text>
        
        {/* Small Tax Icon/Symbol */}
        <path
          d="M20 16 L44 16 L42 20 L22 20 Z"
          fill="#FFFFFF"
          opacity="0.8"
        />
        <path
          d="M22 20 L42 20 L40 24 L24 24 Z"
          fill="#FFFFFF"
          opacity="0.6"
        />
        
        {/* Document Lines for Reconciliation Symbol */}
        <line x1="18" y1="48" x2="46" y2="48" stroke="#FFFFFF" strokeWidth="2" opacity="0.7" />
        <line x1="20" y1="52" x2="44" y2="52" stroke="#FFFFFF" strokeWidth="1.5" opacity="0.5" />
      </svg>
    </div>
  );
};

export default GSTLogo;