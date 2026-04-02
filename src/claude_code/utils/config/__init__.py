"""
Global / project configuration types (narrow subset of utils/config.ts).

Full persistence lives in utils/config_utils.py; this package holds shared shapes.
"""

from .types import AccountInfo, GlobalConfigLite, ProjectConfigLite

__all__ = ["AccountInfo", "GlobalConfigLite", "ProjectConfigLite"]
