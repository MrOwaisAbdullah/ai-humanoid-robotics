"""
Integration tests for guest session persistence
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
import json

# Test configuration
BASE_URL = "http://localhost:7860"  # Adjust if your backend runs on different port
API_BASE = f"{BASE_URL}/api"


class TestGuestSessionPersistence:
    """Test suite for guest session persistence functionality"""

    @pytest.fixture(scope="class")
    def session_id(self):
        """Create a unique session ID for tests"""
        return f"test-session-{int(time.time())}"

    @pytest.fixture(autouse=True)
    def cleanup_session(self, session_id):
        """Cleanup session after tests"""
        yield
        # Note: In a real test environment, you might want to add cleanup endpoints
        # or directly access the database to clean up test data
        pass

    def test_get_anonymous_session_new(self, session_id):
        """Test fetching a new anonymous session that doesn't exist"""
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == session_id
        assert data["message_count"] == 0
        assert data["exists"] is False

    def test_get_anonymous_session_invalid_format(self):
        """Test fetching session with invalid ID format"""
        invalid_session_id = "invalid-session-id!"
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{invalid_session_id}")

        # Should still handle gracefully (implementation dependent)
        assert response.status_code in [200, 400, 422]

    def test_session_persistence_flow(self, session_id):
        """Test the complete session persistence flow"""
        # 1. Get initial session data
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")
        assert response.status_code == 200

        initial_data = response.json()
        assert initial_data["message_count"] == 0
        assert initial_data["exists"] is False

        # 2. Simulate sending messages (would normally go through chat API)
        # Note: This would require the chat API to be running
        # For now, we'll simulate by directly creating session data

        # 3. Verify session persistence
        # In a real test, you would:
        # - Send messages through the chat API
        # - Verify message count increments
        # - Check that session data persists across requests

        # 4. Check session after "refresh"
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")
        assert response.status_code == 200

        final_data = response.json()
        assert final_data["id"] == session_id
        # Message count would be updated if chat API was integrated

    def test_concurrent_session_access(self, session_id):
        """Test concurrent access to the same session"""
        import concurrent.futures
        import threading

        results = []
        errors = []

        def fetch_session():
            try:
                response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    errors.append(f"Status: {response.status_code}")
            except Exception as e:
                errors.append(str(e))

        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_session) for _ in range(10)]
            concurrent.futures.wait(futures)

        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10

        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            assert result["id"] == first_result["id"]
            assert result["message_count"] == first_result["message_count"]
            assert result["exists"] == first_result["exists"]

    def test_session_id_uniqueness(self):
        """Test that different session IDs return different data"""
        session_id_1 = f"test-session-1-{int(time.time())}"
        session_id_2 = f"test-session-2-{int(time.time())}"

        response_1 = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id_1}")
        response_2 = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id_2}")

        assert response_1.status_code == 200
        assert response_2.status_code == 200

        data_1 = response_1.json()
        data_2 = response_2.json()

        assert data_1["id"] != data_2["id"]
        assert data_1["message_count"] == data_2["message_count"] == 0
        assert data_1["exists"] == data_2["exists"] == False

    @pytest.mark.slow
    def test_session_expiration_boundary(self, session_id):
        """Test session behavior around expiration boundary"""
        # This test would be more relevant if sessions had automatic expiration
        # Currently, sessions are created on-demand and don't auto-expire from the GET endpoint

        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == session_id

        # In a real implementation with expiration:
        # - You might test session after 24 hours
        # - Verify expired sessions return specific responses
        # - Test renewal of near-expiry sessions

    def test_error_handling(self):
        """Test error handling for various edge cases"""
        # Test very long session ID
        long_session_id = "x" * 1000
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{long_session_id}")

        # Should handle gracefully (implementation dependent)
        assert response.status_code in [200, 400, 414, 422]

        # Test special characters in session ID
        special_session_id = "session-with-special-chars-!@#$%^&*()"
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{special_session_id}")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_response_format(self, session_id):
        """Test that response format is consistent"""
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields exist
        assert "id" in data
        assert "message_count" in data
        assert "exists" in data

        # Verify field types
        assert isinstance(data["id"], str)
        assert isinstance(data["message_count"], int)
        assert isinstance(data["exists"], bool)

        # Verify field values are valid
        assert data["message_count"] >= 0
        assert data["id"] == session_id

    @pytest.mark.parametrize("session_id", [
        "simple-session",
        "session-with-123",
        "SESSION-WITH-CAPS",
        "session_with_underscores",
        "session-with-dashes",
        "session123",
    ])
    def test_various_session_id_formats(self, session_id):
        """Test various valid session ID formats"""
        response = requests.get(f"{API_BASE}/auth/anonymous-session/{session_id}")

        # Should handle all valid formats
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == session_id
        assert isinstance(data["message_count"], int)
        assert isinstance(data["exists"], bool)


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])