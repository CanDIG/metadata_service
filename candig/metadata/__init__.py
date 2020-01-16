"""Metadata version information."""

#__import__('pkg_resources').declare_namespace(__name__)

__version__ = "0.5.0"
try:
    from . import _version
    __version__ = _version.version
except ImportError:
    pass
