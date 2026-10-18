import React from 'react';
import { Bot } from 'lucide-react';

const SIZE_MAP = {
  xs: 'w-6 h-6 text-[9px]',
  sm: 'w-8 h-8 text-[11px]',
  md: 'w-10 h-10 text-xs',
  lg: 'w-12 h-12 text-sm',
  xl: 'w-16 h-16 text-lg',
};

const ICON_SIZE_MAP = {
  xs: 10,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 26,
};

/**
 * Avatar — displays user initials in a gradient circle, or a bot icon for AI.
 *
 * @param {'xs'|'sm'|'md'|'lg'|'xl'} size
 * @param {string} initials — up to 2 characters
 * @param {string} gradient — tailwind gradient classes (from-[x] to-[y])
 * @param {boolean} isBot — if true, shows Bot icon instead of initials
 * @param {boolean} pulse — if true, adds a pulse glow ring
 * @param {string} className — extra classes
 */
export default function Avatar({
  size = 'sm',
  initials = '',
  gradient = 'from-[#1A6BB5] to-[#C41E2A]',
  isBot = false,
  pulse = false,
  className = '',
  ring = false,
}) {
  const sizeClass = SIZE_MAP[size] || SIZE_MAP.sm;
  const iconSize = ICON_SIZE_MAP[size] || ICON_SIZE_MAP.sm;

  return (
    <div
      className={`
        relative rounded-full bg-gradient-to-br ${gradient}
        flex items-center justify-center font-semibold text-white shrink-0
        shadow-md select-none transition-transform duration-150 hover:scale-105
        ${sizeClass}
        ${ring ? 'ring-2 ring-[#2E9BFF]/40 ring-offset-1 ring-offset-transparent' : ''}
        ${className}
      `}
      title={isBot ? 'Noetaris AI' : initials}
    >
      {/* Inner content */}
      {isBot ? (
        <div className="w-full h-full rounded-full bg-[#050B14]/80 flex items-center justify-center">
          <Bot size={iconSize} className="text-[#2E9BFF] drop-shadow-sm" />
        </div>
      ) : (
        <span className="tracking-tight drop-shadow-sm">{initials}</span>
      )}

      {/* Pulse glow ring */}
      {pulse && (
        <span className="absolute inset-0 rounded-full animate-ping opacity-20 bg-[#2E9BFF]" />
      )}
    </div>
  );
}

/**
 * BotAvatar — pre-configured for the Noetaris AI assistant.
 */
export function BotAvatar({ size = 'sm', pulse = false, className = '' }) {
  return (
    <Avatar
      size={size}
      isBot
      gradient="from-[#1A6BB5] to-[#2E9BFF]"
      pulse={pulse}
      ring
      className={className}
    />
  );
}

/**
 * UserAvatar — pre-configured for the current user.
 */
export function UserAvatar({ size = 'sm', initials = 'JD', gradient, className = '' }) {
  return (
    <Avatar
      size={size}
      initials={initials}
      gradient={gradient || 'from-[#1A6BB5] to-[#C41E2A]'}
      className={className}
    />
  );
}
