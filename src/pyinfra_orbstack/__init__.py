"""
PyInfra OrbStack Connector

A PyInfra connector for managing OrbStack VMs and containers.
"""

__version__ = "0.1.0"
__author__ = "Matthew Turland"
__email__ = "me@matthewturland.com"

from .connector import OrbStackConnector

__all__ = ["OrbStackConnector"]
