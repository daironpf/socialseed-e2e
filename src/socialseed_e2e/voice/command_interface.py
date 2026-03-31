"""
Voice/NLP Command Interface - EPIC-023
Speech-to-text and text-to-speech for dashboard operations.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel


class CommandIntent(str, Enum):
    """NLP command intents."""
    START_SNIFFER = "start_sniffer"
    STOP_SNIFFER = "stop_sniffer"
    RUN_TESTS = "run_tests"
    SHOW_TRAFFIC = "show_traffic"
    SHOW_ALERTS = "show_alerts"
    SHOW_METRICS = "show_metrics"
    CREATE_TEST = "create_test"
    GENERATE_REPORT = "generate_report"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class VoiceCommand:
    """A voice command."""
    id: str
    transcript: str
    intent: CommandIntent
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class NLPParser:
    """Parses natural language to commands."""
    
    def __init__(self):
        self._command_mappings = {
            "start": CommandIntent.START_SNIFFER,
            "inicia": CommandIntent.START_SNIFFER,
            "begin": CommandIntent.START_SNIFFER,
            "stop": CommandIntent.STOP_SNIFFER,
            "detener": CommandIntent.STOP_SNIFFER,
            "para": CommandIntent.STOP_SNIFFER,
            "run": CommandIntent.RUN_TESTS,
            "ejecuta": CommandIntent.RUN_TESTS,
            "corre": CommandIntent.RUN_TESTS,
            "show": CommandIntent.SHOW_TRAFFIC,
            "mostrar": CommandIntent.SHOW_TRAFFIC,
            "muestra": CommandIntent.SHOW_TRAFFIC,
            "test": CommandIntent.CREATE_TEST,
            "crear": CommandIntent.CREATE_TEST,
            "genera": CommandIntent.GENERATE_REPORT,
            "reporte": CommandIntent.GENERATE_REPORT,
            "ayuda": CommandIntent.HELP,
            "help": CommandIntent.HELP,
        }
    
    def parse(self, transcript: str) -> VoiceCommand:
        """Parse transcript to command."""
        import uuid
        
        transcript_lower = transcript.lower()
        
        intent = CommandIntent.UNKNOWN
        confidence = 0.0
        parameters = {}
        
        for keyword, intent_candidate in self._command_mappings.items():
            if keyword in transcript_lower:
                intent = intent_candidate
                confidence = 0.9
                break
        
        if "traffic" in transcript_lower:
            intent = CommandIntent.SHOW_TRAFFIC
            parameters["view"] = "traffic"
        elif "alert" in transcript_lower or "alerta" in transcript_lower:
            intent = CommandIntent.SHOW_ALERTS
            parameters["view"] = "alerts"
        elif "metric" in transcript_lower or "métrica" in transcript_lower:
            intent = CommandIntent.SHOW_METRICS
            parameters["view"] = "metrics"
        
        if "auth" in transcript_lower:
            parameters["service"] = "auth"
        elif "socialuser" in transcript_lower:
            parameters["service"] = "socialuser"
        
        if "x2" in transcript_lower or "double" in transcript_lower or "dos" in transcript_lower:
            parameters["speed"] = 2
        elif "x0.5" in transcript_lower or "half" in transcript_lower or "mitad" in transcript_lower:
            parameters["speed"] = 0.5
        
        if intent == CommandIntent.UNKNOWN:
            intent = CommandIntent.HELP
        
        return VoiceCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            transcript=transcript,
            intent=intent,
            confidence=confidence,
            parameters=parameters,
        )


class CommandExecutor:
    """Executes voice commands."""
    
    def __init__(self):
        self._handlers: Dict[CommandIntent, Callable] = {}
    
    def register_handler(self, intent: CommandIntent, handler: Callable) -> None:
        """Register a handler for an intent."""
        self._handlers[intent] = handler
    
    async def execute(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute a voice command."""
        handler = self._handlers.get(command.intent)
        
        if handler:
            try:
                result = await handler(command.parameters)
                return {
                    "success": True,
                    "result": result,
                    "message": f"Executed: {command.intent.value}",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to execute {command.intent.value}",
                }
        
        return {
            "success": False,
            "error": "No handler for intent",
            "message": f"Unknown command: {command.transcript}",
        }


class VoiceInterface:
    """Main voice interface manager."""
    
    def __init__(self):
        self.parser = NLPParser()
        self.executor = CommandExecutor()
        self._command_history: List[VoiceCommand] = []
        self._tts_enabled = True
    
    def parse_and_execute(self, transcript: str) -> Dict[str, Any]:
        """Parse transcript and execute command."""
        command = self.parser.parse(transcript)
        self._command_history.append(command)
        
        import asyncio
        return asyncio.run(self.executor.execute(command))
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command history."""
        return [
            {
                "id": c.id,
                "transcript": c.transcript,
                "intent": c.intent.value,
                "confidence": c.confidence,
                "parameters": c.parameters,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in self._command_history
        ]
    
    def enable_tts(self, enabled: bool = True) -> None:
        """Enable/disable text-to-speech."""
        self._tts_enabled = enabled
    
    def get_tts_config(self) -> Dict[str, Any]:
        """Get TTS configuration for frontend."""
        return {
            "enabled": self._tts_enabled,
            "voices": [
                {"name": "en-US", "lang": "en-US"},
                {"name": "es-ES", "lang": "es-ES"},
            ],
        }


_global_interface: Optional[VoiceInterface] = None


def get_voice_interface() -> VoiceInterface:
    """Get global voice interface."""
    global _global_interface
    if _global_interface is None:
        _global_interface = VoiceInterface()
    return _global_interface
