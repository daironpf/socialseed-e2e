"""
The Omniscient Project Manifest - EPIC-025
Master graph brain unifying all subsystems.
"""

from .omniscient_manifest import (
    EntityType,
    GraphEntity,
    GraphRelationship,
    KnowledgeGraph,
    RelationshipType,
    get_knowledge_graph,
)

__all__ = [
    "EntityType",
    "GraphEntity",
    "GraphRelationship",
    "KnowledgeGraph",
    "RelationshipType",
    "get_knowledge_graph",
]
