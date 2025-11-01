"""
PyInfra OrbStack Connector

A PyInfra connector for managing OrbStack VMs and containers.
"""

# Version is automatically managed by hatch-vcs from git tags
# This imports from _version.py (generated at build time) or uses importlib.metadata
try:
    from ._version import __version__
except ImportError:
    # Fallback for development installations or when _version.py doesn't exist
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            __version__ = version("pyinfra-orbstack")
        except PackageNotFoundError:
            # Package not installed, use placeholder
            __version__ = "0.0.0.dev0+unknown"
    except ImportError:
        # Python < 3.8 fallback (though project requires >= 3.9)
        __version__ = "0.0.0.dev0+unknown"

__author__ = "Matthew Turland"
__email__ = "me@matthewturland.com"

from .connector import OrbStackConnector

__all__ = ["OrbStackConnector", "__version__"]
