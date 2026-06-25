# Install Or Repair

The Topology Studio web app generates a personalized install prompt from:

`/api/integration/cursor/prompt`

If the MCP stops working:

1. Open Topology Studio.
2. Click **Connect Cursor**.
3. Rotate the token.
4. Paste the generated install prompt into Cursor.
5. Reload the Cursor window.
6. Verify with `topology_health`.

Do not share the token. It grants access only to the issuing user's topology environment, but it should still be treated like a secret.

