"""Manifest Generator for AI Project Knowledge Base.

This module generates and maintains the project_knowledge.json file
that stores all detected information about the user's project for AI
token optimization.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from socialseed_e2e.project_manifest.models import (
    EnvironmentVariable,
    FileMetadata,
    ManifestFreshness,
    ProjectKnowledge,
    ServiceInfo,
)
from socialseed_e2e.project_manifest.parsers import BaseParser, parser_registry


class ManifestGenerator:
    """Generates and maintains the project knowledge manifest."""

    MANIFEST_FILENAME = "project_knowledge.json"

    def __init__(
        self,
        project_root: Path,
        manifest_path: Optional[Path] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """Initialize the manifest generator.

        Args:
            project_root: Root directory of the project to analyze
            manifest_path: Path where to save the manifest (default: project_root/MANIFEST_FILENAME)
            exclude_patterns: List of glob patterns to exclude from scanning
        """
        self.project_root = Path(project_root).resolve()
        self.manifest_path = manifest_path or (
            self.project_root / self.MANIFEST_FILENAME
        )
        self.exclude_patterns = exclude_patterns or [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/venv/**",
            "**/.venv/**",
            "**/target/**",
            "**/build/**",
            "**/dist/**",
            "**/.idea/**",
            "**/.vscode/**",
            "**/ide-extensions/**",
            "**/.agent/**",
            "**/.github/**",
            "**/*_test.py",
            "**/*_spec.*",
        ]
        self._parsers_cache: Dict[str, BaseParser] = {}

    def generate(self, force_full_scan: bool = False) -> ProjectKnowledge:
        """Generate or update the project knowledge manifest.

        Args:
            force_full_scan: If True, perform full scan even if manifest exists

        Returns:
            ProjectKnowledge object with all detected information
        """
        # Try to load existing manifest
        existing_manifest = None
        if not force_full_scan and self.manifest_path.exists():
            try:
                existing_manifest = self._load_manifest()
            except (json.JSONDecodeError, KeyError):
                pass

        if existing_manifest:
            # Perform smart sync - only scan changed files
            return self._smart_sync(existing_manifest)
        else:
            # Perform full scan
            return self._full_scan()

    def _full_scan(self) -> ProjectKnowledge:
        """Perform a full scan of the project."""
        print(f"🔍 Performing full scan of project: {self.project_root}")

        # Discover all source files
        source_files = self._discover_source_files()

        # Compute SHA-256 hashes for all files
        source_hashes = self._compute_source_hashes(source_files)

        # Group files by service/directory
        service_files = self._group_files_by_service(source_files)

        # Parse all services
        services: List[ServiceInfo] = []
        file_metadata: Dict[str, FileMetadata] = {}

        for service_name, files in service_files.items():
            service_info = self._parse_service(service_name, files)
            services.append(service_info)

            # Collect file metadata
            for file_path in files:
                file_key = str(file_path.relative_to(self.project_root))
                if file_key in self._parsers_cache:
                    metadata = self._parsers_cache[file_key]
                    if hasattr(metadata, "file_metadata"):
                        file_metadata[file_key] = metadata.file_metadata

        # Detect global environment variables
        global_env_vars = self._detect_global_env_vars(services)

        # Create project knowledge
        project_name = self._detect_project_name()

        manifest = ProjectKnowledge(
            version="2.0",
            project_name=project_name,
            project_root=str(self.project_root),
            services=services,
            file_metadata=file_metadata,
            source_hashes=source_hashes,
            manifest_freshness=ManifestFreshness.FRESH,
            global_env_vars=global_env_vars,
            generated_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )

        # Save manifest
        self._save_manifest(manifest)

        print(f"✅ Full scan complete. Found {len(services)} services.")
        print(f"   - {sum(len(s.endpoints) for s in services)} endpoints")
        print(f"   - {sum(len(s.dto_schemas) for s in services)} DTOs")
        print(f"   - {len(global_env_vars)} global environment variables")
        print(f"   - {len(source_hashes)} source files hashed")
        print(f"   📄 Manifest saved to: {self.manifest_path}")

        return manifest

    def _smart_sync(self, existing_manifest: ProjectKnowledge) -> ProjectKnowledge:
        """Perform smart sync - only scan changed files."""
        print(f"🔄 Performing smart sync for project: {self.project_root}")

        # Discover all source files
        source_files = self._discover_source_files()

        # Detect changed files
        changed_files, removed_files = self._detect_changes(
            source_files, existing_manifest
        )

        if not changed_files and not removed_files:
            print("✅ No changes detected. Manifest is up to date.")
            return existing_manifest

        print(f"   Changed files: {len(changed_files)}")
        print(f"   Removed files: {len(removed_files)}")

        # Update services based on changes
        services = existing_manifest.services.copy()
        file_metadata = dict(existing_manifest.file_metadata)

        # Remove deleted files from services
        for removed_file in removed_files:
            self._remove_file_from_services(services, removed_file)
            if removed_file in file_metadata:
                del file_metadata[removed_file]

        # Process changed files
        for file_path in changed_files:
            # Remove old data for this file
            self._remove_file_from_services(
                services, str(file_path.relative_to(self.project_root))
            )

            # Parse the file
            parser = parser_registry.get_parser(file_path, self.project_root)
            if parser:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    result = parser.parse_file(file_path, content)

                    # Add to appropriate service
                    service_name = self._get_service_name_for_file(file_path)
                    service = next(
                        (s for s in services if s.name == service_name), None
                    )

                    if not service:
                        service = ServiceInfo(
                            name=service_name,
                            language=parser.LANGUAGE,
                            root_path=str(self._get_service_root(file_path)),
                        )
                        services.append(service)

                    # Merge parsed data
                    service.endpoints.extend(result.endpoints)
                    service.dto_schemas.extend(result.dto_schemas)
                    service.ports.extend(result.ports)
                    service.environment_vars.extend(result.env_vars)
                    service.dependencies.extend(result.dependencies)

                    file_key = str(file_path.relative_to(self.project_root))
                    file_metadata[file_key] = result.file_metadata

                except Exception as e:
                    print(f"   ⚠️ Error parsing {file_path}: {e}")

        # Remove empty services
        services = [s for s in services if s.endpoints or s.dto_schemas]

        # Update source hashes for changed files
        source_hashes = dict(existing_manifest.source_hashes)
        for file_path in changed_files:
            file_key = str(file_path.relative_to(self.project_root))
            try:
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
                source_hashes[file_key] = f"sha256:{file_hash}"
            except (OSError, IOError):
                continue

        # Remove hashes for deleted files
        for removed_file in removed_files:
            if removed_file in source_hashes:
                del source_hashes[removed_file]

        # Update manifest
        existing_manifest.services = services
        existing_manifest.file_metadata = file_metadata
        existing_manifest.source_hashes = source_hashes
        existing_manifest.manifest_freshness = ManifestFreshness.FRESH
        existing_manifest.update_timestamp()

        # Re-detect global env vars
        existing_manifest.global_env_vars = self._detect_global_env_vars(services)

        # Save updated manifest
        self._save_manifest(existing_manifest)

        print(f"✅ Smart sync complete. {len(services)} services.")

        return existing_manifest

    def _discover_source_files(self) -> List[Path]:
        """Discover all source files in the project."""
        source_files = []

        for ext in ["*.py", "*.java", "*.js", "*.ts", "*.go", "*.cs"]:
            for file_path in self.project_root.rglob(ext):
                if not self._should_exclude(file_path):
                    source_files.append(file_path)

        return source_files

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        import fnmatch

        str_path = str(file_path)
        relative_path = str(file_path.relative_to(self.project_root))

        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(
                relative_path, pattern
            ):
                return True

        return False

    def _group_files_by_service(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by service/directory."""
        service_files: Dict[str, List[Path]] = {}

        for file_path in files:
            service_name = self._get_service_name_for_file(file_path)

            if service_name not in service_files:
                service_files[service_name] = []

            service_files[service_name].append(file_path)

        return service_files

    def _get_service_name_for_file(self, file_path: Path) -> str:
        """Determine service name from file path."""
        # Get the first directory level under project root
        try:
            relative = file_path.relative_to(self.project_root)
            parts = relative.parts

            if len(parts) >= 1:
                # Use first directory or filename without extension
                service_name = parts[0]
                if service_name == "src" and len(parts) >= 2:
                    service_name = parts[1]
                return service_name
        except ValueError:
            pass

        return file_path.stem

    def _get_service_root(self, file_path: Path) -> Path:
        """Get the root directory for a service."""
        try:
            relative = file_path.relative_to(self.project_root)
            parts = relative.parts

            if len(parts) >= 1:
                service_root = self.project_root / parts[0]
                return service_root
        except ValueError:
            pass

        return file_path.parent

    def _parse_service(self, service_name: str, files: List[Path]) -> ServiceInfo:
        """Parse all files in a service."""
        endpoints = []
        dto_schemas = []
        ports = []
        env_vars = []
        dependencies = []
        file_paths = []
        config_files = []

        language = "unknown"
        framework = None

        for file_path in files:
            parser = parser_registry.get_parser(file_path, self.project_root)
            if not parser:
                continue

            language = parser.LANGUAGE

            try:
                content = file_path.read_text(encoding="utf-8")
                result = parser.parse_file(file_path, content)

                endpoints.extend(result.endpoints)
                dto_schemas.extend(result.dto_schemas)
                ports.extend(result.ports)
                env_vars.extend(result.env_vars)
                dependencies.extend(result.dependencies)

                file_key = str(file_path.relative_to(self.project_root))
                self._parsers_cache[file_key] = result

                file_paths.append(file_key)

                # Detect framework
                if not framework:
                    framework = self._detect_framework(content, language)

            except Exception as e:
                print(f"   ⚠️ Error parsing {file_path}: {e}")

        # Remove duplicates from environment variables
        unique_env_vars = []
        seen_vars = set()
        for var in env_vars:
            if var.name not in seen_vars:
                seen_vars.add(var.name)
                unique_env_vars.append(var)

        return ServiceInfo(
            name=service_name,
            language=language,
            framework=framework,
            root_path=str(
                self._get_service_root(files[0]) if files else self.project_root
            ),
            endpoints=endpoints,
            dto_schemas=dto_schemas,
            ports=ports,
            environment_vars=unique_env_vars,
            dependencies=dependencies,
            file_paths=file_paths,
            config_files=config_files,
        )

    def _detect_framework(self, content: str, language: str) -> Optional[str]:
        """Detect web framework from content."""
        if language == "python":
            if "from fastapi" in content or "import fastapi" in content:
                return "fastapi"
            elif "from flask" in content or "import flask" in content:
                return "flask"
            elif "from django" in content or "import django" in content:
                return "django"
        elif language == "java":
            if "@RestController" in content or "@Controller" in content:
                return "spring"
        elif language == "javascript":
            if "express" in content.lower():
                return "express"
            elif "@nestjs" in content.lower() or "@nestjs/common" in content:
                return "nestjs"
            elif "fastify" in content.lower():
                return "fastify"

        return None

    def _detect_global_env_vars(
        self, services: List[ServiceInfo]
    ) -> List[EnvironmentVariable]:
        """Detect global environment variables."""
        # Common environment variables across many projects
        common_vars = [
            EnvironmentVariable(
                name="DATABASE_URL",
                description="Database connection string",
                required=True,
            ),
            EnvironmentVariable(
                name="REDIS_URL",
                description="Redis connection string",
                required=False,
            ),
            EnvironmentVariable(
                name="JWT_SECRET",
                description="JWT signing secret",
                required=True,
            ),
            EnvironmentVariable(
                name="API_KEY",
                description="API authentication key",
                required=False,
            ),
            EnvironmentVariable(
                name="LOG_LEVEL",
                default_value="INFO",
                description="Logging level",
                required=False,
            ),
        ]

        # Check if these variables are used in any service
        found_vars = []
        service_env_names = set()
        for service in services:
            for env in service.environment_vars:
                service_env_names.add(env.name)

        for var in common_vars:
            if var.name in service_env_names:
                found_vars.append(var)

        return found_vars

    def _detect_project_name(self) -> str:
        """Detect project name from various sources."""
        # Try package.json for Node projects
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                return data.get("name", self.project_root.name)
            except (json.JSONDecodeError, KeyError):
                pass

        # Try pyproject.toml for Python projects
        pyproject_toml = self.project_root / "pyproject.toml"
        if pyproject_toml.exists():
            content = pyproject_toml.read_text()
            match = re.search(r'name\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)

        # Default to directory name
        return self.project_root.name

    def _detect_changes(
        self,
        current_files: List[Path],
        manifest: ProjectKnowledge,
    ) -> Tuple[List[Path], List[str]]:
        """Detect changed and removed files.

        Uses SHA-256 hashes from source_hashes if available (v2.0),
        otherwise falls back to MD5 checksums from file_metadata.

        Args:
            current_files: List of currently discovered files
            manifest: Existing manifest

        Returns:
            Tuple of (changed_files, removed_files)
        """
        changed_files = []
        removed_files = []

        current_file_paths = {
            str(f.relative_to(self.project_root)) for f in current_files
        }

        # Use source_hashes (v2.0) or fall back to file_metadata
        if manifest.source_hashes:
            manifest_file_paths = set(manifest.source_hashes.keys())
        else:
            manifest_file_paths = set(manifest.file_metadata.keys())

        # Find removed files
        removed_files = list(manifest_file_paths - current_file_paths)

        # Find changed or new files
        for file_path in current_files:
            file_key = str(file_path.relative_to(self.project_root))

            if file_key not in manifest_file_paths:
                # New file
                changed_files.append(file_path)
            else:
                # Check if file has changed using SHA-256 hash
                try:
                    content = file_path.read_bytes()
                    current_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

                    if manifest.source_hashes:
                        stored_hash = manifest.source_hashes.get(file_key)
                    else:
                        # Fall back to MD5 for older manifests
                        current_hash = hashlib.md5(content).hexdigest()
                        metadata = manifest.file_metadata.get(file_key)
                        stored_hash = metadata.checksum if metadata else None

                    if current_hash != stored_hash:
                        changed_files.append(file_path)

                except (OSError, IOError):
                    changed_files.append(file_path)

        return changed_files, removed_files

    def _compute_source_hashes(self, source_files: List[Path]) -> Dict[str, str]:
        """Compute SHA-256 hashes for all source files.

        Args:
            source_files: List of source file paths

        Returns:
            Dictionary mapping relative file paths to SHA-256 hashes
        """
        hashes = {}
        for file_path in source_files:
            try:
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
                relative_path = str(file_path.relative_to(self.project_root))
                hashes[relative_path] = f"sha256:{file_hash}"
            except (OSError, IOError):
                continue
        return hashes

    def _remove_file_from_services(
        self, services: List[ServiceInfo], file_path: str
    ) -> None:
        """Remove all data associated with a file from services."""
        for service in services:
            # Remove endpoints from this file
            service.endpoints = [
                e for e in service.endpoints if e.file_path != file_path
            ]

            # Remove DTOs from this file
            service.dto_schemas = [
                d for d in service.dto_schemas if d.file_path != file_path
            ]

            # Remove file from file_paths
            service.file_paths = [f for f in service.file_paths if f != file_path]

    def _load_manifest(self) -> Optional[ProjectKnowledge]:
        """Load existing manifest from disk."""
        if not self.manifest_path.exists():
            return None

        content = self.manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)

        return ProjectKnowledge.model_validate(data)

    def _save_manifest(self, manifest: ProjectKnowledge) -> None:
        """Save manifest to disk."""
        # Ensure directory exists
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to JSON
        data = manifest.model_dump(mode="json", exclude_none=True)

        # Write with pretty formatting
        self.manifest_path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    def get_manifest(self) -> Optional[ProjectKnowledge]:
        """Get the current manifest if it exists."""
        return self._load_manifest()
