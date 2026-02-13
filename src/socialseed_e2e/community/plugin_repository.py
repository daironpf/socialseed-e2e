"""Plugin Repository for SocialSeed-E2E.

This module provides functionality for managing and sharing plugins.
"""

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.community import CommunityHub, PluginResource, ResourceType


@dataclass
class PluginManifest:
    """Manifest for a plugin."""

    name: str
    version: str
    description: str
    author: str
    entry_point: str
    hooks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compatible_framework_versions: List[str] = field(default_factory=list)
    min_python_version: str = "3.8"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "entry_point": self.entry_point,
            "hooks": self.hooks,
            "dependencies": self.dependencies,
            "compatible_framework_versions": self.compatible_framework_versions,
            "min_python_version": self.min_python_version,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create manifest from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            entry_point=data.get("entry_point", ""),
            hooks=data.get("hooks", []),
            dependencies=data.get("dependencies", []),
            compatible_framework_versions=data.get("compatible_framework_versions", []),
            min_python_version=data.get("min_python_version", "3.8"),
            tags=data.get("tags", []),
        )


class PluginRepository:
    """Repository for managing plugins."""

    def __init__(self, community_hub: Optional[CommunityHub] = None):
        """Initialize the plugin repository.

        Args:
            community_hub: Community hub instance
        """
        self.hub = community_hub or CommunityHub()
        self.plugins_dir = self.hub.storage_path / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        self.installed_dir = Path.home() / ".socialseed_e2e" / "plugins"
        self.installed_dir.mkdir(parents=True, exist_ok=True)

    def create_plugin_package(
        self,
        manifest: PluginManifest,
        plugin_code: str,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Create a plugin package.

        Args:
            manifest: Plugin manifest
            plugin_code: Plugin source code
            output_path: Output path for package

        Returns:
            Path to created package
        """
        import uuid

        plugin_id = str(uuid.uuid4())

        if output_path is None:
            output_path = self.plugins_dir / f"{manifest.name}-{manifest.version}.zip"

        # Create temporary directory for plugin files
        temp_dir = self.plugins_dir / plugin_id
        temp_dir.mkdir(exist_ok=True)

        try:
            # Write manifest
            manifest_file = temp_dir / "manifest.json"
            manifest_file.write_text(json.dumps(manifest.to_dict(), indent=2))

            # Write plugin code
            code_file = temp_dir / f"{manifest.name.lower().replace(' ', '_')}.py"
            code_file.write_text(plugin_code)

            # Create README
            readme_file = temp_dir / "README.md"
            readme_content = self._generate_readme(manifest)
            readme_file.write_text(readme_content)

            # Create zip package
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in temp_dir.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(temp_dir))

            return output_path

        finally:
            # Cleanup temp directory
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def publish_plugin(
        self, manifest: PluginManifest, package_path: Path
    ) -> Optional[PluginResource]:
        """Publish a plugin to the repository.

        Args:
            manifest: Plugin manifest
            package_path: Path to plugin package

        Returns:
            Published plugin resource or None
        """
        import uuid

        plugin_id = str(uuid.uuid4())

        # Create plugin resource
        plugin = PluginResource(
            id=plugin_id,
            name=manifest.name,
            description=manifest.description,
            author=manifest.author,
            version=manifest.version,
            tags=manifest.tags,
            file_path=package_path,
            entry_point=manifest.entry_point,
            hooks=manifest.hooks,
            dependencies=manifest.dependencies,
            compatible_versions=manifest.compatible_framework_versions,
        )

        # Publish to community hub
        if self.hub.publish_resource(plugin):
            return plugin

        return None

    def search_plugins(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        hook_type: Optional[str] = None,
    ) -> List[PluginResource]:
        """Search for plugins.

        Args:
            query: Search query
            tags: Filter by tags
            hook_type: Filter by hook type

        Returns:
            List of matching plugins
        """
        results = self.hub.search_resources(
            resource_type=ResourceType.PLUGIN,
            tags=tags,
            query=query,
        )

        if hook_type:
            results = [p for p in results if hook_type in p.hooks]

        return results

    def install_plugin(self, plugin_id: str) -> bool:
        """Install a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if installed successfully
        """
        plugin = self.hub.get_resource(plugin_id)
        if not plugin or not plugin.file_path:
            return False

        # Check if already installed
        install_dir = self.installed_dir / plugin.name
        if install_dir.exists():
            return False

        try:
            # Extract plugin package
            with zipfile.ZipFile(plugin.file_path, "r") as zf:
                zf.extractall(install_dir)

            # Increment download count
            self.hub.download_resource(plugin_id)

            return True

        except Exception:
            return False

    def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            True if uninstalled successfully
        """
        import shutil

        install_dir = self.installed_dir / plugin_name
        if not install_dir.exists():
            return False

        try:
            shutil.rmtree(install_dir)
            return True
        except Exception:
            return False

    def list_installed_plugins(self) -> List[Dict[str, Any]]:
        """List all installed plugins.

        Returns:
            List of installed plugin info
        """
        installed = []

        for plugin_dir in self.installed_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "manifest.json"
                if manifest_file.exists():
                    try:
                        data = json.loads(manifest_file.read_text())
                        data["install_path"] = str(plugin_dir)
                        installed.append(data)
                    except Exception:
                        pass

        return installed

    def get_plugin_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get manifest for an installed plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin manifest or None
        """
        manifest_file = self.installed_dir / plugin_name / "manifest.json"
        if not manifest_file.exists():
            return None

        try:
            data = json.loads(manifest_file.read_text())
            return PluginManifest.from_dict(data)
        except Exception:
            return None

    def is_plugin_installed(self, plugin_name: str) -> bool:
        """Check if a plugin is installed.

        Args:
            plugin_name: Plugin name

        Returns:
            True if installed
        """
        return (self.installed_dir / plugin_name).exists()

    def validate_plugin(self, package_path: Path) -> tuple[bool, List[str]]:
        """Validate a plugin package.

        Args:
            package_path: Path to plugin package

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not package_path.exists():
            return False, ["Package file does not exist"]

        if not zipfile.is_zipfile(package_path):
            return False, ["Not a valid zip file"]

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                # Check for manifest
                if "manifest.json" not in zf.namelist():
                    errors.append("Missing manifest.json")
                else:
                    # Validate manifest
                    manifest_data = json.loads(zf.read("manifest.json"))
                    required_fields = ["name", "version", "entry_point"]
                    for field in required_fields:
                        if field not in manifest_data:
                            errors.append(f"Missing required field: {field}")

                # Check for code file
                manifest_data = json.loads(zf.read("manifest.json"))
                plugin_name = manifest_data.get("name", "").lower().replace(" ", "_")
                code_file = f"{plugin_name}.py"

                if code_file not in zf.namelist():
                    errors.append(f"Missing code file: {code_file}")

        except zipfile.BadZipFile:
            return False, ["Invalid zip file"]
        except json.JSONDecodeError:
            return False, ["Invalid manifest.json"]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

        return len(errors) == 0, errors

    def get_plugin_hooks(self, hook_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Get all available hooks from installed plugins.

        Args:
            hook_type: Filter by hook type

        Returns:
            Dictionary mapping hook types to plugin names
        """
        hooks: Dict[str, List[str]] = {}

        for plugin_info in self.list_installed_plugins():
            plugin_hooks = plugin_info.get("hooks", [])
            plugin_name = plugin_info.get("name", "")

            for hook in plugin_hooks:
                if hook_type is None or hook == hook_type:
                    if hook not in hooks:
                        hooks[hook] = []
                    hooks[hook].append(plugin_name)

        return hooks

    def _generate_readme(self, manifest: PluginManifest) -> str:
        """Generate README content for plugin.

        Args:
            manifest: Plugin manifest

        Returns:
            README content
        """
        readme = f"""# {manifest.name}

{manifest.description}

## Version

{manifest.version}

## Author

{manifest.author}

## Entry Point

`{manifest.entry_point}`

## Hooks

"""
        if manifest.hooks:
            for hook in manifest.hooks:
                readme += f"- {hook}\n"
        else:
            readme += "No hooks registered.\n"

        readme += """
## Dependencies

"""
        if manifest.dependencies:
            for dep in manifest.dependencies:
                readme += f"- {dep}\n"
        else:
            readme += "No dependencies.\n"

        readme += """
## Compatible Versions

"""
        if manifest.compatible_framework_versions:
            for version in manifest.compatible_framework_versions:
                readme += f"- {version}\n"
        else:
            readme += "All versions.\n"

        readme += """
## Tags

"""
        if manifest.tags:
            readme += ", ".join(manifest.tags) + "\n"
        else:
            readme += "No tags.\n"

        return readme

    def update_plugin(
        self, plugin_name: str, new_version: str, new_package: Path
    ) -> bool:
        """Update an installed plugin to a new version.

        Args:
            plugin_name: Plugin name
            new_version: New version string
            new_package: Path to new package

        Returns:
            True if updated successfully
        """
        # Validate new package
        is_valid, errors = self.validate_plugin(new_package)
        if not is_valid:
            return False

        # Uninstall old version
        if not self.uninstall_plugin(plugin_name):
            return False

        # Read new manifest
        with zipfile.ZipFile(new_package, "r") as zf:
            manifest_data = json.loads(zf.read("manifest.json"))

        # Create new plugin resource
        plugin = PluginResource(
            id="",  # Will be generated
            name=manifest_data["name"],
            description=manifest_data.get("description", ""),
            author=manifest_data.get("author", ""),
            version=new_version,
            file_path=new_package,
            entry_point=manifest_data.get("entry_point", ""),
            hooks=manifest_data.get("hooks", []),
            dependencies=manifest_data.get("dependencies", []),
        )

        # Install new version
        return self.install_plugin(plugin.id)
