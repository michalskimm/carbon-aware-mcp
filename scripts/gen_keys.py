"""Gen an RSA keypair and mint a test client token. Run ONCE; re-run to roteate keys and invalidate old tokens."""

from fastmcp.server.auth.providers.jwt import RSAKeyPair

ISSUER, AUDIENCE = "http://carbon-aware-mcp", "carbon-aware-mcp"
kp = RSAKeyPair.generate()
token = kp.create_token(
    subject="demo-client", issuer=ISSUER, audience=AUDIENCE,
    scopes=["read"], expires_in_seconds=60 * 60 * 24 * 30,
)
print("=== PUBLIC KEY (set as CARBON_MCP_PU configure MCP) ===\n" + kp.public_key)
print("\n=== CLIENT TOKEN (do NOT commit) ===\n" + token)