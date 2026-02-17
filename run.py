import os
import sys

from dotenv import load_dotenv

# .env laden
load_dotenv()

# src/ zum Python-Path hinzufuegen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hauskeeping import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host=host, port=port)
