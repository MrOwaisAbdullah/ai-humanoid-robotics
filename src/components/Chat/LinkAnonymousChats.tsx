import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/auth-api';

interface AnonymousSession {
  id: string;
  message_count: number;
  created_at: string;
  last_activity: string;
  title?: string;
}

interface LinkAnonymousChatsProps {
  onLinkSuccess?: () => void;
  className?: string;
}

export const LinkAnonymousChats: React.FC<LinkAnonymousChatsProps> = ({
  onLinkSuccess,
  className = '',
}) => {
  const { user, isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState<AnonymousSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch anonymous sessions from localStorage
  useEffect(() => {
    if (isAuthenticated) {
      const storedSessions = localStorage.getItem('anonymous_sessions');
      if (storedSessions) {
        try {
          const parsedSessions = JSON.parse(storedSessions);
          setSessions(parsedSessions);
        } catch (err) {
          console.error('Failed to parse anonymous sessions:', err);
        }
      }
    }
  }, [isAuthenticated]);

  const handleSessionSelect = (sessionId: string) => {
    setSelectedSessions(prev =>
      prev.includes(sessionId)
        ? prev.filter(id => id !== sessionId)
        : [...prev, sessionId]
    );
  };

  const handleSelectAll = () => {
    if (selectedSessions.length === sessions.length) {
      setSelectedSessions([]);
    } else {
      setSelectedSessions(sessions.map(s => s.id));
    }
  };

  const handleLinkSessions = async () => {
    if (selectedSessions.length === 0) {
      setError('Please select at least one session to link');
      return;
    }

    setLinking(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await authAPI.linkAnonymousSessions(selectedSessions);

      if (response.success) {
        setSuccess(`Successfully linked ${selectedSessions.length} session(s) to your account`);

        // Remove linked sessions from localStorage
        const remainingSessions = sessions.filter(s => !selectedSessions.includes(s.id));
        setSessions(remainingSessions);
        setSelectedSessions([]);

        // Store remaining sessions back
        if (remainingSessions.length > 0) {
          localStorage.setItem('anonymous_sessions', JSON.stringify(remainingSessions));
        } else {
          localStorage.removeItem('anonymous_sessions');
        }

        if (onLinkSuccess) {
          onLinkSuccess();
        }

        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(response.error || 'Failed to link sessions');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to link sessions');
    } finally {
      setLinking(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Don't show if not authenticated or no sessions
  if (!isAuthenticated || sessions.length === 0) {
    return null;
  }

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-blue-900">Link Previous Anonymous Chats</h3>
        <p className="text-sm text-blue-700 mt-1">
          We found {sessions.length} anonymous chat session(s) from before you signed in.
          Would you like to link them to your account to save your chat history?
        </p>
      </div>

      {/* Sessions List */}
      {sessions.length > 0 && (
        <div className="space-y-2 mb-4">
          {/* Select All */}
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={selectedSessions.length === sessions.length}
              onChange={handleSelectAll}
              className="rounded border-blue-300 text-blue-600 focus:ring-blue-500"
              disabled={linking}
            />
            <span className="font-medium">
              Select All ({selectedSessions.length}/{sessions.length})
            </span>
          </label>

          {/* Session Items */}
          <div className="max-h-60 overflow-y-auto space-y-2">
            {sessions.map((session) => (
              <label
                key={session.id}
                className="flex items-start space-x-3 p-3 bg-white rounded border border-blue-200 cursor-pointer hover:bg-blue-50"
              >
                <input
                  type="checkbox"
                  checked={selectedSessions.includes(session.id)}
                  onChange={() => handleSessionSelect(session.id)}
                  className="mt-1 rounded border-blue-300 text-blue-600 focus:ring-blue-500"
                  disabled={linking}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {session.title || `Chat Session ${session.id.slice(-8)}`}
                  </div>
                  <div className="text-xs text-gray-500">
                    {session.message_count} messages • {formatDate(session.last_activity)}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="mb-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-md text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-3 bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded-md text-sm">
          {success}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={() => localStorage.removeItem('anonymous_sessions')}
          className="text-sm text-gray-600 hover:text-gray-800"
          disabled={linking}
        >
          Dismiss
        </button>
        <button
          onClick={handleLinkSessions}
          disabled={selectedSessions.length === 0 || linking}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {linking ? 'Linking...' : `Link ${selectedSessions.length} Session(s)`}
        </button>
      </div>
    </div>
  );
};