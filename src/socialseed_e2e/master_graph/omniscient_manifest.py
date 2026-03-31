"""
The Omniscient Project Manifest - EPIC-025
Master graph brain unifying all subsystems.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    CODE = "code"
    DTO = "dto"
    ENDPOINT = "endpoint"
    TEST = "test"
    SERVICE = "service"
    ALERT = "alert"
    VULNERABILITY = "vulnerability"
    CHAOS_EVENT = "chaos_event"
    SNAPSHOT = "snapshot"
    ANOMALY = "anomaly"
    REPLAY = "replay"
    JOURNEY = "journey"


class RelationshipType(str, Enum):
    """Types of relationships."""
    CALLS = "calls"
    GENERATES = "generates"
    TRIGGERS = "triggers"
    CAUSED_BY = "caused_by"
    FIXED_BY = "fixed_by"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    CORRELATES_WITH = "correlates_with"


@dataclass
class GraphEntity:
    """An entity in the knowledge graph."""
    id: str
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphRelationship:
    """A relationship between entities."""
    from_entity: str
    to_entity: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """Central knowledge graph unifying all subsystems."""
    
    def __init__(self):
        self._entities: Dict[str, GraphEntity] = {}
        self._relationships: List[GraphRelationship] = {}
        self._index: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()
    
    def add_entity(self, entity: GraphEntity) -> None:
        """Add an entity to the graph."""
        with self._lock:
            self._entities[entity.id] = entity
            
            key = f"{entity.entity_type.value}:{entity.name}"
            if key not in self._index:
                self._index[key] = set()
            self._index[key].add(entity.id)
    
    def add_relationship(self, rel: GraphRelationship) -> None:
        """Add a relationship."""
        with self._lock:
            key = f"{rel.from_entity}->{rel.to_entity}"
            self._relationships[key] = rel
    
    def query(
        self,
        entity_type: Optional[EntityType] = None,
        name_contains: Optional[str] = None,
        related_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query the knowledge graph."""
        results = []
        
        with self._lock:
            for entity in self._entities.values():
                if entity_type and entity.entity_type != entity_type:
                    continue
                
                if name_contains and name_contains.lower() not in entity.name.lower():
                    continue
                
                results.append({
                    "id": entity.id,
                    "type": entity.entity_type.value,
                    "name": entity.name,
                    "properties": entity.properties,
                    "created_at": entity.created_at.isoformat(),
                })
        
        if related_to:
            related_ids = set()
            for rel in self._relationships.values():
                if rel.from_entity == related_to:
                    related_ids.add(rel.to_entity)
                elif rel.to_entity == related_to:
                    related_ids.add(rel.from_entity)
            
            results = [r for r in results if r["id"] in related_ids]
        
        return results
    
    def traverse(
        self,
        start_entity_id: str,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """Traverse the graph from a starting entity."""
        visited = set()
        result = {"nodes": [], "edges": []}
        
        def _traverse(entity_id: str, depth: int):
            if depth > max_depth or entity_id in visited:
                return
            
            visited.add(entity_id)
            
            with self._lock:
                entity = self._entities.get(entity_id)
                if entity:
                    result["nodes"].append({
                        "id": entity.id,
                        "type": entity.entity_type.value,
                        "name": entity.name,
                    })
                
                for rel in self._relationships.values():
                    if rel.from_entity == entity_id:
                        result["edges"].append({
                            "from": rel.from_entity,
                            "to": rel.to_entity,
                            "type": rel.relationship_type.value,
                        })
                        _traverse(rel.to_entity, depth + 1)
        
        _traverse(start_entity_id, 0)
        return result
    
    def get_centrality(self) -> List[Dict[str, Any]]:
        """Get entity centrality scores."""
        scores = {e.id: 0 for e in self._entities.values()}
        
        with self._lock:
            for rel in self._relationships.values():
                scores[rel.from_entity] = scores.get(rel.from_entity, 0) + 1
                scores[rel.to_entity] = scores.get(rel.to_entity, 0) + 1
        
        return [
            {"id": eid, "score": score}
            for eid, score in scores.items()
        ][:20]
    
    def natural_language_query(self, query: str) -> str:
        """Process natural language queries."""
        query_lower = query.lower()
        
        if "latency" in query_lower and "chaos" in query_lower:
            return self._query_latency_chaos()
        elif "vulnerability" in query_lower or "security" in query_lower:
            return self._query_vulnerabilities()
        elif "test" in query_lower and "heal" in query_lower:
            return self._query_self_healing()
        elif "endpoint" in query_lower or "dto" in query_lower:
            return self._query_endpoints_dtos()
        else:
            return "Query not understood. Try: 'latency during chaos test', 'vulnerabilities', 'self-healing tests', or 'endpoints and DTOs'"
    
    def _query_latency_chaos(self) -> str:
        """Query: latency during chaos tests."""
        chaos_entities = self.query(entity_type=EntityType.CHAOS_EVENT)
        latency_entities = self.query(entity_type=EntityType.ANOMALY)
        
        result = "# Latency Analysis during Chaos Events\n\n"
        result += f"**Chaos Events:** {len(chaos_entities)}\n"
        result += f"**Latency Anomalies:** {len(latency_entities)}\n\n"
        
        for c in chaos_entities[:5]:
            result += f"- {c['name']}: {c.get('properties', {}).get('type', 'N/A')}\n"
        
        return result
    
    def _query_vulnerabilities(self) -> str:
        """Query: security vulnerabilities."""
        vulns = self.query(entity_type=EntityType.VULNERABILITY)
        
        result = "# Security Vulnerabilities\n\n"
        result += f"**Total:** {len(vulns)}\n\n"
        
        for v in vulns[:10]:
            result += f"- {v['name']}: {v.get('properties', {}).get('severity', 'N/A')}\n"
        
        return result
    
    def _query_self_healing(self) -> str:
        """Query: self-healing tests."""
        tests = self.query(name_contains="heal")
        
        result = "# Self-Healing Tests\n\n"
        result += f"**Healed Tests:** {len(tests)}\n\n"
        
        for t in tests[:10]:
            result += f"- {t['name']}\n"
        
        return result
    
    def _query_endpoints_dtos(self) -> str:
        """Query: endpoints and DTOs."""
        endpoints = self.query(entity_type=EntityType.ENDPOINT)
        dtos = self.query(entity_type=EntityType.DTO)
        
        result = "# Endpoints and DTOs\n\n"
        result += f"**Endpoints:** {len(endpoints)}\n"
        result += f"**DTOs:** {len(dtos)}\n\n"
        
        for e in endpoints[:5]:
            result += f"- {e['name']}\n"
        
        return result
    
    def export_graph_json(self) -> Dict[str, Any]:
        """Export entire graph as JSON."""
        with self._lock:
            return {
                "entities": [
                    {
                        "id": e.id,
                        "type": e.entity_type.value,
                        "name": e.name,
                        "properties": e.properties,
                    }
                    for e in self._entities.values()
                ],
                "relationships": [
                    {
                        "from": r.from_entity,
                        "to": r.to_entity,
                        "type": r.relationship_type.value,
                    }
                    for r in self._relationships.values()
                ],
                "stats": {
                    "total_entities": len(self._entities),
                    "total_relationships": len(self._relationships),
                },
            }


_global_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Get global knowledge graph."""
    global _global_graph
    if _global_graph is None:
        _global_graph = KnowledgeGraph()
    return _global_graph
