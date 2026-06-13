"""pytest setup: make the server importable in tests.

server.py reads CARBON_MCP_PUBLIC_KEY at import time. Unit tests never verify real
tokens, so a dummy value is enough — setdefault so a real env var (CI/local) wins.
"""

import os

os.environ.setdefault("CARBON_MCP_PUBLIC_KEY", "dummy-key-unit-tests-do-not-verify-tokens")
