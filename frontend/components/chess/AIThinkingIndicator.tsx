'use client';

import { useEffect, useState } from 'react';

interface AIThinkingIndicatorProps {
  visible: boolean;
  message?: string;
  variant?: 'thinking' | 'analyzing' | 'generating';
}

export default function AIThinkingIndicator({
  visible,
  message = 'AI is thinking',
  variant = 'thinking'
}: AIThinkingIndicatorProps) {
  const [dots, setDots] = useState('');
  
  useEffect(() => {
    if (!visible) return;
    
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);
    
    return () => clearInterval(interval);
  }, [visible]);

  if (!visible) return null;

  const variantMessages = {
    thinking: 'Analyzing your position',
    analyzing: 'Evaluating position and variations',
    generating: 'Preparing personalized insights'
  };

  return (
    <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-chess-primary-50 to-indigo-50 rounded-lg border border-chess-primary-200 shadow-panel">
      {/* Animated Spinner */}
      <div className="relative w-8 h-8 flex-shrink-0">
        <div className="absolute inset-0 border-4 border-chess-primary-200 rounded-full" />
        <div className="absolute inset-0 border-4 border-chess-primary-500 rounded-full border-t-transparent animate-spin" />
      </div>

      {/* Message */}
      <div className="flex-1">
        <p className="text-sm font-medium text-chess-primary-900">
          {message}{dots}
        </p>
        
        <p className="text-xs text-chess-primary-600 mt-1">
          {variantMessages[variant]}
        </p>
      </div>

      {/* Pulse animation */}
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-chess-primary-500 rounded-full animate-pulse" 
             style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 bg-chess-primary-500 rounded-full animate-pulse" 
             style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 bg-chess-primary-500 rounded-full animate-pulse" 
             style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}
