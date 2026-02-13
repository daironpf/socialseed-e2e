"""Session Recorder for Shadow Runner.

Records and manages user sessions for replay.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.shadow_runner.traffic_interceptor import CapturedInteraction


@dataclass
class UserSession:
    """A recorded user session."""

    session_id: str
    user_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    interactions: List[CapturedInteraction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Alias for session_id for backward compatibility."""
        return self.session_id

    def add_interaction(self, interaction: CapturedInteraction) -> None:
        """Add an interaction to the session.

        Args:
            interaction: Captured interaction
        """
        interaction.session_id = self.session_id
        self.interactions.append(interaction)

    def close(self) -> None:
        """Close the session."""
        self.end_time = datetime.utcnow()

    @property
    def duration_ms(self) -> float:
        """Get session duration in milliseconds.

        Returns:
            Duration in milliseconds
        """
        if not self.end_time:
            return (datetime.utcnow() - self.start_time).total_seconds() * 1000
        return (self.end_time - self.start_time).total_seconds() * 1000

    def get_duration_seconds(self) -> float:
        """Get session duration in seconds.

        Returns:
            Duration in seconds
        """
        return self.duration_ms / 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "interactions": [i.to_dict() for i in self.interactions],
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Create from dictionary."""
        from socialseed_e2e.shadow_runner.traffic_interceptor import (
            CapturedInteraction,
            CapturedRequest,
            CapturedResponse,
        )

        session = cls(
            session_id=data.get("session_id", data.get("id", str(uuid.uuid4()))),
            user_id=data.get("user_id"),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"])
            if data.get("end_time")
            else None,
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

        for interaction_data in data.get("interactions", []):
            request = CapturedRequest.from_dict(interaction_data["request"])
            response = None
            if interaction_data.get("response"):
                response = CapturedResponse.from_dict(interaction_data["response"])

            interaction = CapturedInteraction(
                id=interaction_data["id"],
                request=request,
                response=response,
                session_id=interaction_data.get("session_id"),
                sequence_number=interaction_data.get("sequence_number", 0),
                tags=interaction_data.get("tags", []),
            )
            session.interactions.append(interaction)

        return session


class SessionRecorder:
    """Records and manages user sessions."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the session recorder.

        Args:
            output_dir: Path to store sessions
        """
        self.output_dir = Path(output_dir) if output_dir else Path(".e2e/sessions")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.active_sessions: Dict[str, UserSession] = {}
        self.session_timeout_minutes = 30

    def start_session(
        self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new session.

        Args:
            user_id: Optional user identifier
            metadata: Session metadata

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            metadata=metadata or {},
        )

        self.active_sessions[session_id] = session
        return session_id

    def end_session(self, session_id: str) -> Optional[UserSession]:
        """End a session and save it.

        Args:
            session_id: Session ID

        Returns:
            Ended session or None
        """
        session = self.active_sessions.pop(session_id, None)
        if not session:
            return None

        session.close()
        self._save_session(session)
        return session

    def add_interaction_to_session(
        self, session_id: str, interaction: CapturedInteraction
    ) -> bool:
        """Add an interaction to an active session.

        Args:
            session_id: Session ID
            interaction: Interaction to add

        Returns:
            True if added successfully
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.add_interaction(interaction)
        return True

    def get_active_session(self, session_id: str) -> Optional[UserSession]:
        """Get an active session.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        return self.active_sessions.get(session_id)

    def get_all_active_sessions(self) -> List[UserSession]:
        """Get all active sessions.

        Returns:
            List of active sessions
        """
        return list(self.active_sessions.values())

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = []
        now = datetime.utcnow()
        timeout = timedelta(minutes=self.session_timeout_minutes)

        for session_id, session in self.active_sessions.items():
            if now - session.start_time > timeout:
                expired_ids.append(session_id)

        for session_id in expired_ids:
            self.end_session(session_id)

        return len(expired_ids)

    def _save_session(self, session: UserSession) -> None:
        """Save a session to file.

        Args:
            session: Session to save
        """
        file_path = self.output_dir / f"{session.session_id}.json"
        file_path.write_text(json.dumps(session.to_dict(), indent=2))

    def load_session(self, session_id: str) -> Optional[UserSession]:
        """Load a session from file.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        file_path = self.output_dir / f"{session_id}.json"
        if not file_path.exists():
            return None

        data = json.loads(file_path.read_text())
        return UserSession.from_dict(data)

    def load_all_sessions(self) -> List[UserSession]:
        """Load all saved sessions.

        Returns:
            List of sessions
        """
        sessions = []

        for file_path in self.output_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                session = UserSession.from_dict(data)
                sessions.append(session)
            except Exception:
                pass

        return sessions

    def replay_session(
        self,
        session_id: str,
        callback: Optional[callable] = None,
        delay_ms: float = 0,
    ) -> List[Dict[str, Any]]:
        """Replay a session.

        Args:
            session_id: Session ID to replay
            callback: Optional callback for each interaction
            delay_ms: Delay between interactions in milliseconds

        Returns:
            List of replay results
        """
        session = self.load_session(session_id)
        if not session:
            return []

        results = []

        for index, interaction in enumerate(
            sorted(session.interactions, key=lambda i: i.sequence_number)
        ):
            result = {
                "interaction_id": interaction.id,
                "method": interaction.request.method,
                "path": interaction.request.path,
                "status_code": interaction.response.status_code
                if interaction.response
                else None,
                "success": False,
            }

            # Execute replay (simplified - would actually make the request)
            try:
                # Here you would actually replay the request
                # For now, just record that we would replay it
                result["success"] = True

                if callback:
                    callback(interaction, index)

            except Exception as e:
                result["error"] = str(e)

            results.append(result)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

        return results

    def find_similar_sessions(
        self, session_id: str, threshold: float = 0.8
    ) -> List[UserSession]:
        """Find sessions similar to a given session.

        Args:
            session_id: Reference session ID
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar sessions
        """
        reference = self.load_session(session_id)
        if not reference:
            return []

        reference_paths = {i.request.path for i in reference.interactions}
        if not reference_paths:
            return []

        similar_sessions = []

        for session in self.load_all_sessions():
            if session.session_id == session_id:
                continue

            session_paths = {i.request.path for i in session.interactions}
            if not session_paths:
                continue

            # Calculate Jaccard similarity
            intersection = len(reference_paths & session_paths)
            union = len(reference_paths | session_paths)

            if union == 0:
                continue

            similarity = intersection / union

            if similarity >= threshold:
                similar_sessions.append((session, similarity))

        # Sort by similarity
        similar_sessions.sort(key=lambda x: x[1], reverse=True)

        return [s[0].session_id for s in similar_sessions]

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Statistics dictionary
        """
        sessions = self.load_all_sessions()

        total_sessions = len(sessions)
        total_interactions = sum(len(s.interactions) for s in sessions)

        avg_duration = 0
        if sessions:
            durations = [s.get_duration_seconds() for s in sessions]
            avg_duration = sum(durations) / len(durations)

        # Count by user
        users = {}
        for session in sessions:
            user = session.user_id or "anonymous"
            users[user] = users.get(user, 0) + 1

        return {
            "total_sessions": total_sessions,
            "active_sessions": len(self.active_sessions),
            "total_interactions": total_interactions,
            "avg_interactions_per_session": total_interactions / total_sessions
            if total_sessions
            else 0,
            "interactions_per_session_avg": total_interactions / total_sessions
            if total_sessions
            else 0,
            "avg_session_duration_seconds": avg_duration,
            "unique_users": len(users),
            "top_users": sorted(users.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def list_sessions(self) -> List[str]:
        """List all session IDs.

        Returns:
            List of session IDs
        """
        sessions = self.load_all_sessions()
        return [s.session_id for s in sessions]

    def clear_all_sessions(self) -> None:
        """Clear all sessions (active and saved)."""
        # Clear active sessions
        self.active_sessions.clear()

        # Delete all session files
        for file_path in self.output_dir.glob("*.json"):
            file_path.unlink()

    def export_session(self, session_id: str, output_path: Path) -> bool:
        """Export a session to a file.

        Args:
            session_id: Session ID
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        session = self.load_session(session_id)
        if not session:
            return False

        output_path.write_text(json.dumps(session.to_dict(), indent=2))
        return True

    def import_session(self, file_path: Path) -> Optional[str]:
        """Import a session from a file.

        Args:
            file_path: Path to session file

        Returns:
            Imported session ID or None
        """
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text())
            session = UserSession.from_dict(data)

            # Generate new ID to avoid conflicts
            session.session_id = str(uuid.uuid4())

            self._save_session(session)
            return session.session_id

        except Exception:
            return None
