import React from 'react';
import { useLocalization } from '../../contexts/LocalizationContext';
import { Globe, ChevronDown } from 'lucide-react';

interface LanguageOption {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  direction: 'ltr' | 'rtl';
}

const languages: LanguageOption[] = [
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    direction: 'ltr'
  },
  {
    code: 'ur',
    name: 'Urdu',
    nativeName: 'اردو',
    flag: '🇵🇰',
    direction: 'rtl'
  },
  {
    code: 'ur-roman',
    name: 'Roman Urdu',
    nativeName: 'Roman Urdu',
    flag: '🇵🇰',
    direction: 'ltr'
  }
];

export const LanguageSelector: React.FC = () => {
  const { language, setLanguage, isRTL } = useLocalization();
  const [isOpen, setIsOpen] = React.useState(false);

  const currentLanguage = languages.find(lang => lang.code === language) || languages[0];

  const handleLanguageChange = (langCode: string) => {
    setLanguage(langCode as 'en' | 'ur' | 'ur-roman');
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'ArrowDown' && !isOpen) {
      e.preventDefault();
      setIsOpen(true);
    } else if (e.key === 'Enter' && !isOpen) {
      e.preventDefault();
      setIsOpen(true);
    }
  };

  return (
    <div className={`language-selector ${isRTL ? 'rtl' : 'ltr'}`}>
      <button
        className="language-selector-trigger"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label={`Current language: ${currentLanguage.name}`}
      >
        <Globe className="language-selector-icon" size={18} />
        <span className="language-selector-flag">{currentLanguage.flag}</span>
        <span className="language-selector-text">{currentLanguage.nativeName}</span>
        <ChevronDown
          className={`language-selector-chevron ${isOpen ? 'open' : ''}`}
          size={16}
        />
      </button>

      {isOpen && (
        <>
          <div
            className="language-selector-backdrop"
            onClick={() => setIsOpen(false)}
          />
          <ul
            className="language-selector-dropdown"
            role="listbox"
            aria-label="Select language"
          >
            {languages.map((lang) => (
              <li key={lang.code} role="option">
                <button
                  className={`language-selector-option ${lang.code === language ? 'active' : ''}`}
                  onClick={() => handleLanguageChange(lang.code)}
                  aria-selected={lang.code === language}
                  dir={lang.direction}
                >
                  <span className="language-option-flag">{lang.flag}</span>
                  <div className="language-option-content">
                    <span className="language-option-native">{lang.nativeName}</span>
                    <span className="language-option-english">{lang.name}</span>
                  </div>
                  {lang.code === language && (
                    <span className="language-option-check">✓</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

// Mobile version with different UI
export const MobileLanguageSelector: React.FC = () => {
  const { language, setLanguage } = useLocalization();

  const handleLanguageChange = (langCode: string) => {
    setLanguage(langCode as 'en' | 'ur' | 'ur-roman');
  };

  return (
    <div className="mobile-language-selector">
      <div className="mobile-language-title">Language / زبان</div>
      <div className="mobile-language-options">
        {languages.map((lang) => (
          <button
            key={lang.code}
            className={`mobile-language-option ${lang.code === language ? 'active' : ''}`}
            onClick={() => handleLanguageChange(lang.code)}
            aria-pressed={lang.code === language}
          >
            <span className="mobile-language-flag">{lang.flag}</span>
            <span className="mobile-language-name">{lang.nativeName}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

// Compact version for sidebar or header
export const CompactLanguageSelector: React.FC = () => {
  const { language, setLanguage } = useLocalization();
  const [isOpen, setIsOpen] = React.useState(false);

  const currentLanguage = languages.find(lang => lang.code === language) || languages[0];

  const handleLanguageChange = (langCode: string) => {
    setLanguage(langCode as 'en' | 'ur' | 'ur-roman');
    setIsOpen(false);
  };

  return (
    <div className="compact-language-selector">
      <button
        className="compact-language-trigger"
        onClick={() => setIsOpen(!isOpen)}
        title={`Change language (current: ${currentLanguage.name})`}
        aria-label={`Language: ${currentLanguage.flag} ${currentLanguage.name}`}
      >
        <span>{currentLanguage.flag}</span>
      </button>

      {isOpen && (
        <>
          <div
            className="language-selector-backdrop"
            onClick={() => setIsOpen(false)}
          />
          <div className="compact-language-dropdown">
            {languages.map((lang) => (
              <button
                key={lang.code}
                className={`compact-language-option ${lang.code === language ? 'active' : ''}`}
                onClick={() => handleLanguageChange(lang.code)}
                aria-selected={lang.code === language}
                dir={lang.direction}
              >
                <span>{lang.flag}</span>
                <span>{lang.nativeName}</span>
                {lang.code === language && <span>✓</span>}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// Language switcher with smooth transition effect
export const AnimatedLanguageSelector: React.FC = () => {
  const { language, setLanguage, isRTL, formatText } = useLocalization();
  const [isAnimating, setIsAnimating] = React.useState(false);

  const handleLanguageChange = async (langCode: string) => {
    if (langCode === language || isAnimating) return;

    setIsAnimating(true);

    // Add transition class
    document.body.classList.add('language-transition');

    // Change language
    setLanguage(langCode as 'en' | 'ur' | 'ur-roman');

    // Wait for transition
    await new Promise(resolve => setTimeout(resolve, 300));

    // Remove transition class
    document.body.classList.remove('language-transition');
    setIsAnimating(false);
  };

  return (
    <div className={`animated-language-selector ${isRTL ? 'rtl' : 'ltr'} ${isAnimating ? 'animating' : ''}`}>
      <div className="animated-language-current">
        {formatText('Language')}
      </div>
      <div className="animated-language-options">
        {languages.map((lang) => (
          <button
            key={lang.code}
            className={`animated-language-option ${lang.code === language ? 'active' : ''}`}
            onClick={() => handleLanguageChange(lang.code)}
            disabled={isAnimating}
            dir={lang.direction}
          >
            <span className="animated-language-flag">{lang.flag}</span>
            <span className="animated-language-name">{lang.nativeName}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default LanguageSelector;