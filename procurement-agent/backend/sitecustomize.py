"""Azure App Service startup compatibility.

Azure's built-in Python image starts Gunicorn from the system interpreter. When
dependencies are deployed into `.python_packages/lib/site-packages`, the system
interpreter may not include that folder before Gunicorn tries to import the
Uvicorn worker. Python imports this module automatically at startup when the app
root is on `sys.path`, so we add the Azure package folder as early as possible.
"""

from __future__ import annotations

import sys
from pathlib import Path


AZURE_PACKAGES = Path(__file__).resolve().parent / ".python_packages" / "lib" / "site-packages"

if AZURE_PACKAGES.exists():
    azure_packages_path = str(AZURE_PACKAGES)
    if azure_packages_path not in sys.path:
        sys.path.insert(0, azure_packages_path)
