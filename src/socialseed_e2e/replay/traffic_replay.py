"""
Traffic Replay Engine with Speed Controls - EPIC-016
Playback controls for Time-Machine traffic replay.
"""

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel


class PlaybackState(str, Enum):
    """Playback state."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"


class PlaybackSpeed(float, Enum):
    """Playback speed options."""
    SPEED_0_25 = 0.25
    SPEED_0_5 = 0.5
    SPEED_1_0 = 1.0
    SPEED_2_0 = 2.0
    SPEED_4_0 = 4.0
    SPEED_8_0 = 8.0


@dataclass
class CapturedRequest:
    """A captured request for replay."""
    id: str
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    relative_time_ms: int = 0


@dataclass
class PlaybackConfig:
    """Configuration for traffic replay."""
    target_url: str
    speed: PlaybackSpeed = PlaybackSpeed.SPEED_1_0
    loop: bool = False
    start_offset_ms: int = 0
    end_offset_ms: Optional[int] = None
    assert_on_response: bool = False


class TrafficReplayEngine:
    """Engine for replaying captured traffic with speed controls."""
    
    def __init__(self):
        self._requests: List[CapturedRequest] = []
        self._lock = threading.Lock()
        self._state = PlaybackState.STOPPED
        self._current_index = 0
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._speed: PlaybackSpeed = PlaybackSpeed.SPEED_1_0
        self._on_request_callback: Optional[Callable] = None
        self._on_complete_callback: Optional[Callable] = None
    
    def load_requests(self, requests: List[Dict[str, Any]]) -> None:
        """Load requests for replay."""
        with self._lock:
            self._requests = []
            
            if not requests:
                return
            
            first_timestamp = None
            for req in requests:
                ts = req.get("timestamp")
                if ts and not first_timestamp:
                    try:
                        first_timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except:
                        first_timestamp = datetime.now()
            
            if not first_timestamp:
                first_timestamp = datetime.now()
            
            for i, req in enumerate(requests):
                ts = req.get("timestamp")
                if ts:
                    try:
                        req_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        relative_ms = int((req_time - first_timestamp).total_seconds() * 1000)
                    except:
                        relative_ms = i * 1000
                else:
                    relative_ms = i * 1000
                
                self._requests.append(CapturedRequest(
                    id=req.get("id", f"req-{i}"),
                    method=req.get("method", "GET"),
                    url=req.get("url", ""),
                    headers=req.get("headers", {}),
                    body=req.get("body"),
                    timestamp=datetime.now(),
                    relative_time_ms=relative_ms,
                ))
    
    def set_speed(self, speed: PlaybackSpeed) -> None:
        """Set playback speed."""
        self._speed = speed
    
    def play(self, config: PlaybackConfig) -> None:
        """Start playback."""
        if self._state == PlaybackState.PLAYING:
            return
        
        self._stop_event.clear()
        self._pause_event.clear()
        self._state = PlaybackState.PLAYING
        self._speed = config.speed
        
        self._playback_thread = threading.Thread(
            target=self._playback_loop,
            args=(config,),
            daemon=True,
        )
        self._playback_thread.start()
    
    def _playback_loop(self, config: PlaybackConfig) -> None:
        """Main playback loop."""
        try:
            with self._lock:
                if not self._requests:
                    self._state = PlaybackState.COMPLETED
                    return
                
                start_time = time.time()
            
            for i, req in enumerate(self._requests):
                if self._stop_event.is_set():
                    self._state = PlaybackState.STOPPED
                    return
                
                while self._state == PlaybackState.PAUSED:
                    self._pause_event.wait()
                    if self._stop_event.is_set():
                        self._state = PlaybackState.STOPPED
                        return
                
                expected_elapsed = (req.relative_time_ms - config.start_offset_ms) / self._speed.value
                actual_elapsed = time.time() - start_time
                
                if expected_elapsed > actual_elapsed:
                    sleep_time = (expected_elapsed - actual_elapsed) / 1000
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                if self._on_request_callback:
                    result = self._on_request_callback(req)
                    if config.assert_on_response and result:
                        pass
                
                self._current_index = i
            
            self._state = PlaybackState.COMPLETED
            
            if config.loop and self._state != PlaybackState.STOPPED:
                self._current_index = 0
                self.play(config)
            
            if self._on_complete_callback:
                self._on_complete_callback()
                
        except Exception as e:
            self._state = PlaybackState.STOPPED
    
    def pause(self) -> None:
        """Pause playback."""
        if self._state == PlaybackState.PLAYING:
            self._state = PlaybackState.PAUSED
            self._pause_event.set()
    
    def resume(self) -> None:
        """Resume playback."""
        if self._state == PlaybackState.PAUSED:
            self._state = PlaybackState.PLAYING
            self._pause_event.clear()
    
    def stop(self) -> None:
        """Stop playback."""
        self._stop_event.set()
        self._state = PlaybackState.STOPPED
        self._current_index = 0
    
    def skip_forward(self, count: int = 1) -> None:
        """Skip forward in the replay."""
        with self._lock:
            new_index = min(self._current_index + count, len(self._requests) - 1)
            self._current_index = new_index
    
    def skip_backward(self, count: int = 1) -> None:
        """Skip backward in the replay."""
        with self._lock:
            new_index = max(self._current_index - count, 0)
            self._current_index = new_index
    
    def seek_to(self, index: int) -> None:
        """Seek to a specific index."""
        with self._lock:
            if 0 <= index < len(self._requests):
                self._current_index = index
    
    def set_request_callback(self, callback: Callable[[CapturedRequest], Any]) -> None:
        """Set callback for each request."""
        self._on_request_callback = callback
    
    def set_complete_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for playback completion."""
        self._on_complete_callback = callback
    
    def get_state(self) -> Dict[str, Any]:
        """Get current playback state."""
        return {
            "state": self._state.value,
            "current_index": self._current_index,
            "total_requests": len(self._requests),
            "speed": self._speed.value,
            "current_request": self._requests[self._current_index].id if self._requests else None,
        }
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """Get all loaded requests."""
        return [
            {
                "id": r.id,
                "method": r.method,
                "url": r.url,
                "relative_time_ms": r.relative_time_ms,
            }
            for r in self._requests
        ]


class PlaybackControllerAPI:
    """API for controlling playback from the dashboard."""
    
    def __init__(self):
        self.engine = TrafficReplayEngine()
    
    async def load_capture(self, capture_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load a capture file."""
        self.engine.load_requests(capture_data)
        return {"success": True, "request_count": len(capture_data)}
    
    async def play(self, speed: float = 1.0) -> Dict[str, Any]:
        """Start playback."""
        config = PlaybackConfig(
            target_url="",
            speed=PlaybackSpeed(speed),
        )
        self.engine.play(config)
        return self.engine.get_state()
    
    async def pause(self) -> Dict[str, Any]:
        """Pause playback."""
        self.engine.pause()
        return self.engine.get_state()
    
    async def resume(self) -> Dict[str, Any]:
        """Resume playback."""
        self.engine.resume()
        return self.engine.get_state()
    
    async def stop(self) -> Dict[str, Any]:
        """Stop playback."""
        self.engine.stop()
        return self.engine.get_state()
    
    async def set_speed(self, speed: float) -> Dict[str, Any]:
        """Set playback speed."""
        self.engine.set_speed(PlaybackSpeed(speed))
        return self.engine.get_state()
    
    async def seek(self, index: int) -> Dict[str, Any]:
        """Seek to position."""
        self.engine.seek_to(index)
        return self.engine.get_state()
    
    async def skip_forward(self, count: int = 1) -> Dict[str, Any]:
        """Skip forward."""
        self.engine.skip_forward(count)
        return self.engine.get_state()
    
    async def skip_backward(self, count: int = 1) -> Dict[str, Any]:
        """Skip backward."""
        self.engine.skip_backward(count)
        return self.engine.get_state()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return self.engine.get_state()
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """Get loaded requests."""
        return self.engine.get_requests()


_global_api: Optional[PlaybackControllerAPI] = None


def get_playback_api() -> PlaybackControllerAPI:
    """Get global playback API."""
    global _global_api
    if _global_api is None:
        _global_api = PlaybackControllerAPI()
    return _global_api
