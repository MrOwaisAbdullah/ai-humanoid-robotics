import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { PasswordInput } from './PasswordInput';

interface RegistrationData {
  email: string;
  password: string;
  name: string;
  softwareExperience?: 'Beginner' | 'Intermediate' | 'Advanced';
  hardwareExpertise?: 'None' | 'Arduino' | 'ROS-Pro';
  yearsOfExperience?: number;
  primaryInterest?: 'Computer Vision' | 'Machine Learning' | 'Control Systems' | 'Path Planning' | 'State Estimation' | 'Sensors & Perception' | 'Hardware Integration' | 'Human-Robot Interaction' | 'All of the Above';
}

interface RegistrationFormProps {
  onSubmit: (data: RegistrationData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export const RegistrationForm: React.FC<RegistrationFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  error = null
}) => {
  const [formData, setFormData] = useState<RegistrationData>({
    email: '',
    password: '',
    name: '',
    softwareExperience: 'Beginner',
    hardwareExpertise: 'None',
    yearsOfExperience: 0,
    primaryInterest: 'All of the Above'
  });

  const [showOptionalFields, setShowOptionalFields] = useState(true); // Always show optional fields

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onSubmit(formData);
    } catch (err) {
      // Error handling is managed by parent
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'yearsOfExperience' ? parseInt(value) || 0 : value
    }));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-3xl mx-auto p-4 sm:p-6 bg-white dark:bg-zinc-900 rounded-lg shadow-lg"
    >
      <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">
        Create Account
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Required Fields - 2 Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label htmlFor="name" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
              placeholder="Your full name"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Email *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
              placeholder="your@email.com"
            />
          </div>

          <div className="lg:col-span-2">
            <PasswordInput
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
              label={<span className="text-xs font-medium">Password</span>}
              className="px-2 py-1.5 text-sm"
              placeholder="••••••••"
              autoComplete="new-password"
            />
          </div>
        </div>

        {/* Optional Background Information - Always Visible */}
        <div className="pt-3 border-t border-zinc-200 dark:border-zinc-700">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
            Background Information <span className="text-zinc-500 font-normal text-xs">(optional)</span>
          </h3>
          <p className="text-zinc-600 dark:text-zinc-400 mb-3 text-xs">
            This helps us personalize your learning experience
          </p>

          {/* 2-column layout for all fields */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <div>
              <label htmlFor="softwareExperience" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Software Experience
              </label>
              <select
                id="softwareExperience"
                name="softwareExperience"
                value={formData.softwareExperience}
                onChange={handleChange}
                className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>

            <div>
              <label htmlFor="hardwareExpertise" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Hardware Expertise
              </label>
              <select
                id="hardwareExpertise"
                name="hardwareExpertise"
                value={formData.hardwareExpertise}
                onChange={handleChange}
                className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
              >
                <option value="None">None</option>
                <option value="Arduino">Arduino</option>
                <option value="ROS-Pro">ROS-Pro</option>
              </select>
            </div>

            <div>
              <label htmlFor="primaryInterest" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Primary Interest Area
              </label>
              <select
                id="primaryInterest"
                name="primaryInterest"
                value={formData.primaryInterest}
                onChange={handleChange}
                className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
              >
                <option value="Computer Vision">Computer Vision</option>
                <option value="Machine Learning">Machine Learning</option>
                <option value="Control Systems">Control Systems</option>
                <option value="Path Planning">Path Planning</option>
                <option value="State Estimation">State Estimation</option>
                <option value="Sensors & Perception">Sensors & Perception</option>
                <option value="Hardware Integration">Hardware Integration</option>
                <option value="Human-Robot Interaction">Human-Robot Interaction</option>
                <option value="All of the Above">All of the Above</option>
              </select>
            </div>

            <div>
              <label htmlFor="yearsOfExperience" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Years of Experience
              </label>
              <input
                type="number"
                id="yearsOfExperience"
                name="yearsOfExperience"
                value={formData.yearsOfExperience}
                onChange={handleChange}
                min="0"
                max="50"
                className="mt-1 block w-full px-2 py-1.5 text-sm border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                placeholder="0"
              />
            </div>

          </div>
        </div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-6 py-4 rounded-md"
          >
            {error}
          </motion.div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-3 py-2.5 text-xs text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-600 rounded-md font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 px-3 py-2.5 text-xs bg-[#10a37f] text-white rounded-md font-medium hover:bg-[#0d8f6c] focus:outline-none focus:ring-2 focus:ring-[#10a37f] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Creating account...' : 'Sign Up'}
          </button>
        </div>
      </form>
    </motion.div>
  );
};