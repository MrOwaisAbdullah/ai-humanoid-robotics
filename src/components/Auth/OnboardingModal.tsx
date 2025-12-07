import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

interface OnboardingModalProps {
  isOpen: boolean;
  onComplete: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ isOpen, onComplete }) => {
  const [softwareBg, setSoftwareBg] = useState<string>('');
  const [hardwareBg, setHardwareBg] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!softwareBg || !hardwareBg) {
      setError('Please select both options');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch current preferences first to not overwrite existing chat settings
      const prefResponse = await axios.get('/auth/preferences');
      const currentSettings = prefResponse.data.chat_settings || {};

      // Update preferences with background info in chat_settings
      await axios.put('/auth/preferences', {
        ...prefResponse.data,
        chat_settings: {
          ...currentSettings,
          software_background: softwareBg,
          hardware_background: hardwareBg
        }
      });

      onComplete();
    } catch (err) {
      console.error('Failed to save preferences:', err);
      setError('Failed to save preferences. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white dark:bg-neutral-900 rounded-xl shadow-2xl max-w-md w-full p-6 border border-neutral-200 dark:border-neutral-800"
          >
            <h2 className="text-2xl font-bold mb-2 text-neutral-900 dark:text-white">Welcome! 👋</h2>
            <p className="text-neutral-600 dark:text-neutral-400 mb-6">
              To personalize your learning experience, please tell us a bit about your background.
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Software Background */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  What is your Software Background?
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['Novice', 'Intermediate', 'Expert'].map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setSoftwareBg(option)}
                      className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                        softwareBg === option
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-blue-500'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              {/* Hardware Background */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  What is your Hardware/Robotics Background?
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['None', 'Arduino', 'ROS-Pro'].map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setHardwareBg(option)}
                      className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                        hardwareBg === option
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-blue-500'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !softwareBg || !hardwareBg}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : 'Start Learning'}
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
