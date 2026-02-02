import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tiktaktoe")

TIKTAKTOE_API_BASE = "http://127.0.0.1:5000"  # Passe ggf. den Port/URL an

SESSION_ID = None

async def create_new_game() -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{TIKTAKTOE_API_BASE}/new_game")
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
    return {}


async def ensure_session():
    global SESSION_ID
    if SESSION_ID is None:
        result = await create_new_game()
        if result and result.get("success"):
            SESSION_ID = result["data"]["session_id"]
    return SESSION_ID

# --- Helper: Hole aktuellen Spielstand ---
async def fetch_game_state(session_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TIKTAKTOE_API_BASE}/get_state", params={"session_id": session_id})
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
    return {}


# --- Helper: Führe einen Spielzug aus ---
async def post_move(session_id: str, row: int, col: int) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            payload = {"session_id": session_id, "row": row, "col": col}
            response = await client.post(f"{TIKTAKTOE_API_BASE}/make_move", json=payload)
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
    return {}



# --- Tool: Spielzug machen ---
@mcp.tool()
async def make_move(row: int, col: int) -> str:
    """Führt einen Spielzug aus (Session wird automatisch verwaltet)."""
    session_id = await ensure_session()
    result = await post_move(session_id, row, col)
    if not result:
        return "Fehler beim Ausführen des Spielzugs."
    return f"Spielzug ausgeführt: {result}"

@mcp.tool()
async def get_board() -> str:
    """Zeigt das aktuelle Spielfeld an."""
    session_id = await ensure_session()
    state = await fetch_game_state(session_id)
    if not state:
        return "Fehler beim Abrufen des Spielstands."
    return f"Aktueller Spielstand: {state}"


# --- Tool: Beispielzüge anzeigen ---
@mcp.tool()
async def example_moves() -> str:
    """Zeigt Beispielzüge für TikTakToe."""
    return (
        "Beispielzüge:\n"
        "make_move('X', 0, 0)  # X setzt oben links\n"
        "make_move('O', 1, 1)  # O setzt in die Mitte\n"
        "make_move('X', 2, 2)  # X setzt unten rechts"
    )

# --- Entry point ---
if __name__ == "__main__":
    mcp.run(transport="stdio")
