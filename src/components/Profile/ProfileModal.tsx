import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../context/AuthContext';
import { UpdateProfileData, UserPreferences } from '../../types/auth-new';

// Form validation schema
const profileSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  timezone: z.string().optional(),
  language: z.string().optional(),
  profileDescription: z.string().max(500, 'Profile description must be less than 500 characters').optional(),
  preferences: z.object({
    notificationPreferences: z.object({
      emailNotifications: z.boolean(),
      chatReminders: z.boolean(),
      featureUpdates: z.boolean(),
      securityAlerts: z.boolean(),
    }).optional(),
    chatSettings: z.object({
      modelPreference: z.string().optional(),
      temperature: z.number().min(0).max(2).optional(),
      maxTokens: z.number().min(100).max(4000).optional(),
      saveHistory: z.boolean(),
      showSources: z.boolean(),
    }).optional(),
  }).optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Common timezones
const timezones = [
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Dubai',
  'Australia/Sydney',
];

// Common languages
const languages = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'ar', name: 'Arabic' },
];

// Chat model preferences
const chatModels = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3', label: 'Claude 3' },
  { value: 'llama-2', label: 'Llama 2' },
];

export const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const { user, updateProfile, isLoading, error } = useAuth();
  const [activeTab, setActiveTab] = useState<'basic' | 'preferences' | 'chat'>('basic');

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    watch,
    setValue,
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || '',
      timezone: user?.preferences?.timezone || 'UTC',
      language: user?.preferences?.language || 'en',
      profileDescription: user?.profileDescription || '',
      preferences: {
        notificationPreferences: {
          emailNotifications: user?.preferences?.notificationPreferences?.emailNotifications ?? true,
          chatReminders: user?.preferences?.notificationPreferences?.chatReminders ?? true,
          featureUpdates: user?.preferences?.notificationPreferences?.featureUpdates ?? false,
          securityAlerts: user?.preferences?.notificationPreferences?.securityAlerts ?? true,
        },
        chatSettings: {
          modelPreference: user?.preferences?.chatSettings?.modelPreference || 'gpt-4',
          temperature: user?.preferences?.chatSettings?.temperature || 0.7,
          maxTokens: user?.preferences?.chatSettings?.maxTokens || 2000,
          saveHistory: user?.preferences?.chatSettings?.saveHistory ?? true,
          showSources: user?.preferences?.chatSettings?.showSources ?? true,
        },
      },
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.name || '',
        timezone: user.preferences?.timezone || 'UTC',
        language: user.preferences?.language || 'en',
        profileDescription: user.profileDescription || '',
        preferences: {
          notificationPreferences: {
            emailNotifications: user.preferences?.notificationPreferences?.emailNotifications ?? true,
            chatReminders: user.preferences?.notificationPreferences?.chatReminders ?? true,
            featureUpdates: user.preferences?.notificationPreferences?.featureUpdates ?? false,
            securityAlerts: user.preferences?.notificationPreferences?.securityAlerts ?? true,
          },
          chatSettings: {
            modelPreference: user.preferences?.chatSettings?.modelPreference || 'gpt-4',
            temperature: user.preferences?.chatSettings?.temperature || 0.7,
            maxTokens: user.preferences?.chatSettings?.maxTokens || 2000,
            saveHistory: user.preferences?.chatSettings?.saveHistory ?? true,
            showSources: user.preferences?.chatSettings?.showSources ?? true,
          },
        },
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: ProfileFormData) => {
    try {
      const response = await updateProfile(data);

      if (response.success) {
        onClose();
      }
    } catch (err: any) {
      console.error('Profile update error:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-2xl font-bold text-gray-900">Profile Settings</h2>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            className={`px-6 py-3 font-medium text-sm ${
              activeTab === 'basic'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('basic')}
          >
            Basic Info
          </button>
          <button
            className={`px-6 py-3 font-medium text-sm ${
              activeTab === 'preferences'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('preferences')}
          >
            Preferences
          </button>
          <button
            className={`px-6 py-3 font-medium text-sm ${
              activeTab === 'chat'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('chat')}
          >
            Chat Settings
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6">
          <div className="max-h-[60vh] overflow-y-auto">
            {activeTab === 'basic' && (
              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    {...register('name')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your full name"
                    disabled={isLoading}
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                {/* Email (display only) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <p className="mt-1 text-sm text-gray-500">Email cannot be changed here</p>
                </div>

                {/* Timezone */}
                <div>
                  <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
                    Timezone
                  </label>
                  <select
                    id="timezone"
                    {...register('timezone')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  >
                    {timezones.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Language */}
                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    id="language"
                    {...register('language')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  >
                    {languages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Profile Description */}
                <div>
                  <label htmlFor="profileDescription" className="block text-sm font-medium text-gray-700 mb-1">
                    Bio
                  </label>
                  <textarea
                    id="profileDescription"
                    {...register('profileDescription')}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Tell us about yourself..."
                    disabled={isLoading}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {watch('profileDescription')?.length || 0}/500 characters
                  </p>
                  {errors.profileDescription && (
                    <p className="mt-1 text-sm text-red-600">{errors.profileDescription.message}</p>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.notificationPreferences.emailNotifications')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Email notifications</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.notificationPreferences.chatReminders')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Chat reminders</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.notificationPreferences.featureUpdates')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Feature updates</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.notificationPreferences.securityAlerts')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Security alerts</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Chat Settings</h3>
                  <div className="space-y-4">
                    {/* Model Preference */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        AI Model
                      </label>
                      <select
                        {...register('preferences.chatSettings.modelPreference')}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isLoading}
                      >
                        {chatModels.map((model) => (
                          <option key={model.value} value={model.value}>
                            {model.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Temperature */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Temperature: {watch('preferences.chatSettings.temperature')}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        {...register('preferences.chatSettings.temperature', { valueAsNumber: true })}
                        className="w-full"
                        disabled={isLoading}
                      />
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>More focused</span>
                        <span>More creative</span>
                      </div>
                    </div>

                    {/* Max Tokens */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Response Length
                      </label>
                      <input
                        type="range"
                        min="100"
                        max="4000"
                        step="100"
                        {...register('preferences.chatSettings.maxTokens', { valueAsNumber: true })}
                        className="w-full"
                        disabled={isLoading}
                      />
                      <div className="text-center text-sm text-gray-600">
                        {watch('preferences.chatSettings.maxTokens')} tokens
                      </div>
                    </div>

                    {/* Toggles */}
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.chatSettings.saveHistory')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Save chat history</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('preferences.chatSettings.showSources')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="ml-2 text-sm text-gray-700">Show sources</span>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !isDirty}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};