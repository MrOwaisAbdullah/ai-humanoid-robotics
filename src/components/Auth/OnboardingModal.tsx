/**
 * Onboarding modal component for collecting user background data.
 */

import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { createPortal } from 'react-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiRequest } from '../../services/api';

// Form schema for onboarding
const onboardingSchema = z.object({
  experience_level: z.enum(['beginner', 'intermediate', 'advanced']),
  years_experience: z.number().min(0).max(50),
  preferred_languages: z.array(z.string()),
  cpu_expertise: z.enum(['none', 'basic', 'intermediate', 'advanced']),
  gpu_expertise: z.enum(['none', 'basic', 'intermediate', 'advanced']),
  networking_expertise: z.enum(['none', 'basic', 'intermediate', 'advanced']),
});

type OnboardingFormData = z.infer<typeof onboardingSchema>;

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (data: OnboardingFormData) => void;
  initialData?: Partial<OnboardingFormData>;
}

const languages = [
  'python',
  'javascript',
  'java',
  'cpp',
  'c',
  'rust',
  'go',
  'typescript',
  'ruby',
  'php',
  'swift',
  'kotlin',
  'scala',
  'c#',
  'other'
];

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  onComplete,
  initialData = {}
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(initialData.preferred_languages || []);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset
  } = useForm<OnboardingFormData>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      experience_level: 'beginner',
      years_experience: 0,
      preferred_languages: [],
      cpu_expertise: 'none',
      gpu_expertise: 'none',
      networking_expertise: 'none',
      ...initialData
    }
  });

  const experienceLevel = watch('experience_level');

  const steps = [
    {
      title: 'Experience Level',
      subtitle: 'Tell us about your programming experience',
      content: (
        <div className="space-y-4">
          <div className="space-y-3">
            {[
              { value: 'beginner', label: 'Beginner', description: 'Just starting with programming' },
              { value: 'intermediate', label: 'Intermediate', description: 'Comfortable with programming concepts' },
              { value: 'advanced', label: 'Advanced', description: 'Experienced developer' }
            ].map((option) => (
              <label key={option.value} className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 border-zinc-200 dark:border-zinc-700 transition-colors">
                <input
                  type="radio"
                  value={option.value}
                  {...control.register('experience_level')}
                  className="sr-only"
                />
                <div className={`ml-3 flex-1 ${watch('experience_level') === option.value ? 'text-[#10a37f]' : 'text-zinc-900 dark:text-zinc-100'}`}>
                  <h3 className="font-medium">{option.label}</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{option.description}</p>
                </div>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  watch('experience_level') === option.value ? 'bg-[#10a37f] border-[#10a37f]' : 'border-zinc-300 dark:border-zinc-600'
                }`}>
                  {watch('experience_level') === option.value && (
                    <div className="w-3 h-3 bg-white rounded-full" />
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>
      )
    },
    {
      title: 'Years of Experience',
      subtitle: 'How many years have you been programming?',
      content: (
        <div className="space-y-4">
          <div>
            <Controller
              name="years_experience"
              control={control}
              render={({ field }) => (
                <div className="space-y-2">
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={field.value}
                    onChange={(e) => field.onChange(parseInt(e.target.value))}
                    className="w-full h-2 bg-zinc-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-[#10a37f]"
                  />
                  <div className="text-center text-2xl font-semibold text-[#10a37f]">
                    {field.value} {field.value === 1 ? 'year' : 'years'}
                  </div>
                  <div className="flex justify-between text-sm text-zinc-500 dark:text-zinc-400">
                    <span>0</span>
                    <span>25</span>
                    <span>50+</span>
                  </div>
                </div>
              )}
            />
          </div>
        </div>
      )
    },
    {
      title: 'Preferred Languages',
      subtitle: 'What programming languages do you use?',
      content: (
        <div className="space-y-4">
          <div className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
            Select all that apply (you can select multiple)
          </div>
          <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto">
            {languages.map((language) => (
              <label
                key={language}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800 ${
                  selectedLanguages.includes(language) 
                    ? 'bg-[#10a37f]/10 border-[#10a37f]' 
                    : 'border-zinc-200 dark:border-zinc-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedLanguages.includes(language)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      const updated = [...selectedLanguages, language];
                      setSelectedLanguages(updated);
                      setValue('preferred_languages', updated);
                    } else {
                      const updated = selectedLanguages.filter(l => l !== language);
                      setSelectedLanguages(updated);
                      setValue('preferred_languages', updated);
                    }
                  }}
                  className="sr-only"
                />
                <div className="ml-3">
                  <span className={`font-medium capitalize ${selectedLanguages.includes(language) ? 'text-[#10a37f]' : 'text-zinc-700 dark:text-zinc-300'}`}>
                    {language}
                  </span>
                </div>
                {selectedLanguages.includes(language) && (
                  <div className="ml-auto w-5 h-5 bg-[#10a37f] rounded flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-8-8a1 1 0 011.414-1.414l8 8z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </label>
            ))}
          </div>
        </div>
      )
    },
    {
      title: 'Hardware Expertise',
      subtitle: 'How familiar are you with computer hardware?',
      content: (
        <div className="space-y-6">
          {[
            {
              key: 'cpu_expertise',
              label: 'CPU',
              description: 'Processor architecture and performance'
            },
            {
              key: 'gpu_expertise',
              label: 'GPU',
              description: 'Graphics processing and parallel computing'
            },
            {
              key: 'networking_expertise',
              label: 'Networking',
              description: 'Network protocols and distributed systems'
            }
          ].map((field) => (
            <div key={field.key} className="space-y-2">
              <h3 className="font-medium text-zinc-900 dark:text-zinc-100">{field.label}</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">{field.description}</p>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { value: 'none', label: 'None', description: 'No experience' },
                  { value: 'basic', label: 'Basic', description: 'General knowledge' },
                  { value: 'intermediate', label: 'Intermediate', description: 'Some hands-on' },
                  { value: 'advanced', label: 'Advanced', description: 'Expert level' }
                ].map((option) => (
                  <label key={option.value} className="flex flex-col items-center p-3 border border-zinc-200 dark:border-zinc-700 rounded-lg cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-center">
                    <input
                      type="radio"
                      value={option.value}
                      {...control.register(field.key as any)}
                      className="sr-only"
                    />
                                          <div className={`mt-2 ${watch(field.key as any) === option.value ? 'text-[#10a37f]' : 'text-zinc-700 dark:text-zinc-300'}`}>
                                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                                            watch(field.key as any) === option.value ? 'bg-[#10a37f] border-[#10a37f]' : 'border-zinc-300 dark:border-zinc-600'
                                          }`}>                        {watch(field.key as any) === option.value && (
                          <div className="w-2 h-2 bg-white rounded-full" />
                        )}
                      </div>
                      <span className="text-xs font-medium">{option.label}</span>
                    </div>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{option.description}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )
    }
  ];

  const totalSteps = steps.length;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  const onSubmit = async (data: OnboardingFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // Submit onboarding data to API
      const responses = [
        { question_key: 'experience_level_selection', response_value: data.experience_level },
        { question_key: 'years_of_experience', response_value: data.years_experience },
        { question_key: 'preferred_languages', response_value: data.preferred_languages },
        { question_key: 'cpu_expertise', response_value: data.cpu_expertise },
        { question_key: 'gpu_expertise', response_value: data.gpu_expertise },
        { question_key: 'networking_expertise', response_value: data.networking_expertise }
      ];

      await apiRequest.post('/users/onboarding', { responses });

      // Call onComplete callback
      if (onComplete) {
        onComplete(data);
      }

      onClose();
      reset();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save onboarding data');
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    // Save current partial data and close
    const currentData = watch();
    if (onComplete) {
      onComplete(currentData as OnboardingFormData);
    }
    onClose();
  };

  const closeModal = () => {
    if (!isSubmitting) {
      onClose();
      reset();
      setCurrentStep(0);
      setSelectedLanguages([]);
    }
  };

  const modalContent = isOpen && mounted ? (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-black opacity-50 transition-opacity"
          onClick={closeModal}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-zinc-900 rounded-lg max-w-2xl w-full p-6 shadow-xl transition-all">
          {/* Progress bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                Step {currentStep + 1} of {totalSteps}
              </span>
              <button
                onClick={closeModal}
                className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-2">
              <div
                className="bg-[#10a37f] h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Step content */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
              {steps[currentStep].title}
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400">
              {steps[currentStep].subtitle}
            </p>
          </div>

          {steps[currentStep].content}

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 text-sm text-red-700 dark:text-red-200 bg-red-100 dark:bg-red-900/30 rounded-md">
              {error}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex justify-between mt-8">
            <div>
              {currentStep > 0 && (
                <button
                  type="button"
                  onClick={handlePrevious}
                  disabled={isSubmitting}
                  className="px-4 py-2 text-zinc-700 dark:text-zinc-200 bg-white dark:bg-zinc-700 border border-zinc-300 dark:border-zinc-600 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50 transition-colors"
                >
                  Previous
                </button>
              )}
            </div>

            <div className="space-x-3">
              <button
                type="button"
                onClick={handleSkip}
                disabled={isSubmitting}
                className="px-4 py-2 text-zinc-700 dark:text-zinc-200 bg-white dark:bg-zinc-700 border border-zinc-300 dark:border-zinc-600 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50 transition-colors"
              >
                Skip for now
              </button>

              {currentStep < totalSteps - 1 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-[#10a37f] text-white rounded-md hover:bg-[#0d8f6c] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50 transition-colors"
                >
                  Next
                </button>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="inline">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 bg-[#10a37f] text-white rounded-md hover:bg-[#0d8f6c] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50 transition-colors"
                  >
                    {isSubmitting ? 'Saving...' : 'Complete'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  ) : null;

  // Use createPortal to render modal at the document body level
  return mounted && createPortal(
    modalContent,
    document.body
  );
};
