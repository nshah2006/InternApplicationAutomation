/**
 * Preview mode toggle component.
 */

import { useState } from 'react';

export default function PreviewToggle({ 
  isActive, 
  onToggle, 
  disabled = false,
  className = '' 
}) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <span className={`text-sm font-medium ${isActive ? 'text-primary-600' : 'text-gray-600'}`}>
        Preview Mode
      </span>
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        className={`
          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
          transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          ${isActive ? 'bg-primary-600' : 'bg-gray-200'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        role="switch"
        aria-checked={isActive}
        aria-label="Toggle preview mode"
      >
        <span
          className={`
            pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
            transition duration-200 ease-in-out
            ${isActive ? 'translate-x-5' : 'translate-x-0'}
          `}
        />
      </button>
      {isActive && (
        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full font-medium">
          ACTIVE
        </span>
      )}
    </div>
  );
}

