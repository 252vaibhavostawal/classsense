import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Render and other hosts provide PORT. Bind to 0.0.0.0 in deployment.
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
