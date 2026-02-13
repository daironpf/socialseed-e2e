"""Tests for session_recorder module."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from socialseed_e2e.shadow_runner.session_recorder import SessionRecorder, UserSession
from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    CapturedRequest,
    CapturedResponse,
)


class TestUserSession:
    """Test suite for UserSession dataclass."""

    def test_user_session_creation(self):
        """Test creating a UserSession instance."""
        session = UserSession(
            session_id="test-session-123",
            user_id="user-456",
            start_time=datetime.now(),
            interactions=[],
        )

        assert session.session_id == "test-session-123"
        assert session.user_id == "user-456"
        assert session.start_time is not None
        assert session.interactions == []

    def test_user_session_defaults(self):
        """Test UserSession with default values."""
        session = UserSession(session_id="test")

        assert session.session_id == "test"
        assert session.user_id is None
        assert session.start_time is not None
        assert session.end_time is None
        assert session.interactions == []
        assert session.metadata == {}

    def test_user_session_duration(self):
        """Test calculating session duration."""
        start = datetime.now()
        end = datetime.now()

        session = UserSession(
            session_id="test",
            start_time=start,
            end_time=end,
        )

        assert session.duration_ms >= 0

    def test_user_session_to_dict(self):
        """Test converting UserSession to dictionary."""
        session = UserSession(
            session_id="test",
            user_id="user-1",
        )

        data = session.to_dict()

        assert data["session_id"] == "test"
        assert data["user_id"] == "user-1"
        assert "start_time" in data


class TestSessionRecorder:
    """Test suite for SessionRecorder class."""

    def test_session_recorder_creation(self, tmp_path):
        """Test creating a SessionRecorder instance."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        assert recorder.output_dir == tmp_path
        assert recorder.active_sessions == {}

    def test_start_session(self, tmp_path):
        """Test starting a new session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        session_id = recorder.start_session(user_id="user-123")

        assert session_id is not None
        assert session_id in recorder.active_sessions
        assert recorder.active_sessions[session_id].user_id == "user-123"

    def test_start_session_with_metadata(self, tmp_path):
        """Test starting a session with metadata."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        metadata = {"source": "test", "version": "1.0"}
        session_id = recorder.start_session(
            user_id="user-123",
            metadata=metadata,
        )

        session = recorder.active_sessions[session_id]
        assert session.metadata["source"] == "test"
        assert session.metadata["version"] == "1.0"

    def test_end_session(self, tmp_path):
        """Test ending a session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session(user_id="user-123")

        recorder.end_session(session_id)

        assert session_id not in recorder.active_sessions

    def test_add_interaction_to_session(self, tmp_path):
        """Test adding interaction to session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session()

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/test"),
            response=CapturedResponse(status_code=200),
        )

        recorder.add_interaction_to_session(session_id, interaction)

        session = recorder.active_sessions[session_id]
        assert len(session.interactions) == 1
        assert session.interactions[0].request.path == "/api/test"

    def test_add_interaction_to_nonexistent_session(self, tmp_path):
        """Test adding interaction to non-existent session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/test"),
            response=CapturedResponse(status_code=200),
        )

        # Should not raise exception
        recorder.add_interaction_to_session("nonexistent", interaction)

    def test_save_session(self, tmp_path):
        """Test saving session to file."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session(user_id="user-123")

        interaction = CapturedInteraction(
            request=CapturedRequest(
                method="POST",
                path="/api/users",
            ),
            response=CapturedResponse(status_code=201),
        )
        recorder.add_interaction_to_session(session_id, interaction)
        recorder.end_session(session_id)

        # Load saved session
        session_file = tmp_path / f"{session_id}.json"
        assert session_file.exists()

        with open(session_file) as f:
            data = json.load(f)

        assert data["session_id"] == session_id
        assert data["user_id"] == "user-123"
        assert len(data["interactions"]) == 1

    def test_load_session(self, tmp_path):
        """Test loading session from file."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session(user_id="user-123")

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )
        recorder.add_interaction_to_session(session_id, interaction)
        recorder.end_session(session_id)

        # Load session
        loaded = recorder.load_session(session_id)

        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.user_id == "user-123"
        assert len(loaded.interactions) == 1

    def test_load_nonexistent_session(self, tmp_path):
        """Test loading non-existent session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        loaded = recorder.load_session("nonexistent")

        assert loaded is None

    def test_list_sessions(self, tmp_path):
        """Test listing all sessions."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        # Create multiple sessions
        session1 = recorder.start_session(user_id="user-1")
        recorder.end_session(session1)

        session2 = recorder.start_session(user_id="user-2")
        recorder.end_session(session2)

        sessions = recorder.list_sessions()

        assert len(sessions) == 2
        assert session1 in sessions
        assert session2 in sessions

    def test_clear_all_sessions(self, tmp_path):
        """Test clearing all sessions."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        session_id = recorder.start_session()
        recorder.end_session(session_id)

        recorder.clear_all_sessions()

        sessions = recorder.list_sessions()
        assert len(sessions) == 0
        assert len(recorder.active_sessions) == 0

    def test_replay_session(self, tmp_path):
        """Test replaying a session."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session()

        # Add interactions
        for i in range(3):
            interaction = CapturedInteraction(
                request=CapturedRequest(
                    method="GET",
                    path=f"/api/resource/{i}",
                ),
                response=CapturedResponse(status_code=200),
            )
            recorder.add_interaction_to_session(session_id, interaction)

        recorder.end_session(session_id)

        # Replay session
        results = []

        def callback(interaction, index):
            results.append(
                {
                    "path": interaction.request.path,
                    "index": index,
                }
            )

        recorder.replay_session(session_id, callback)

        assert len(results) == 3
        assert results[0]["path"] == "/api/resource/0"
        assert results[2]["path"] == "/api/resource/2"

    def test_find_similar_sessions(self, tmp_path):
        """Test finding similar sessions."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        # Create session with specific pattern
        session1 = recorder.start_session(user_id="user-1")
        recorder.add_interaction_to_session(
            session1,
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/login"),
                response=CapturedResponse(status_code=200),
            ),
        )
        recorder.add_interaction_to_session(
            session1,
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/profile"),
                response=CapturedResponse(status_code=200),
            ),
        )
        recorder.end_session(session1)

        # Create another similar session
        session2 = recorder.start_session(user_id="user-2")
        recorder.add_interaction_to_session(
            session2,
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/login"),
                response=CapturedResponse(status_code=200),
            ),
        )
        recorder.add_interaction_to_session(
            session2,
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/profile"),
                response=CapturedResponse(status_code=200),
            ),
        )
        recorder.end_session(session2)

        # Find similar sessions
        similar = recorder.find_similar_sessions(session1, threshold=0.5)

        assert session2 in similar

    def test_get_session_statistics(self, tmp_path):
        """Test getting session statistics."""
        recorder = SessionRecorder(output_dir=str(tmp_path))
        session_id = recorder.start_session(user_id="user-123")

        # Add various interactions
        recorder.add_interaction_to_session(
            session_id,
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/users"),
                response=CapturedResponse(status_code=201),
            ),
        )
        recorder.add_interaction_to_session(
            session_id,
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/users"),
                response=CapturedResponse(status_code=200),
            ),
        )
        recorder.add_interaction_to_session(
            session_id,
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/users"),
                response=CapturedResponse(status_code=201),
            ),
        )

        recorder.end_session(session_id)

        stats = recorder.get_session_statistics()

        assert stats["total_sessions"] == 1
        assert stats["total_interactions"] == 3
        assert stats["interactions_per_session_avg"] == 3.0


class TestSessionIntegration:
    """Integration tests for session recording."""

    def test_complete_session_workflow(self, tmp_path):
        """Test complete session workflow from start to save."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        # Start session
        session_id = recorder.start_session(
            user_id="test-user",
            metadata={"browser": "chrome", "platform": "mac"},
        )

        # Add interactions
        interactions = [
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/login"),
                response=CapturedResponse(status_code=200),
            ),
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/profile"),
                response=CapturedResponse(status_code=200),
            ),
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/orders"),
                response=CapturedResponse(status_code=201),
            ),
        ]

        for interaction in interactions:
            recorder.add_interaction_to_session(session_id, interaction)

        # End session
        recorder.end_session(session_id)

        # Verify saved session
        loaded = recorder.load_session(session_id)
        assert loaded is not None
        assert loaded.user_id == "test-user"
        assert loaded.metadata["browser"] == "chrome"
        assert len(loaded.interactions) == 3

    def test_multiple_concurrent_sessions(self, tmp_path):
        """Test managing multiple concurrent sessions."""
        recorder = SessionRecorder(output_dir=str(tmp_path))

        # Start multiple sessions
        session1 = recorder.start_session(user_id="user-1")
        session2 = recorder.start_session(user_id="user-2")
        session3 = recorder.start_session(user_id="user-3")

        # Add interactions to different sessions
        recorder.add_interaction_to_session(
            session1,
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/user1-data"),
                response=CapturedResponse(status_code=200),
            ),
        )

        recorder.add_interaction_to_session(
            session2,
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/user2-data"),
                response=CapturedResponse(status_code=200),
            ),
        )

        # Verify sessions are independent
        assert len(recorder.active_sessions[session1].interactions) == 1
        assert len(recorder.active_sessions[session2].interactions) == 1
        assert len(recorder.active_sessions[session3].interactions) == 0

        # End all sessions
        for session_id in [session1, session2, session3]:
            recorder.end_session(session_id)

        # Verify all saved
        assert len(recorder.list_sessions()) == 3
