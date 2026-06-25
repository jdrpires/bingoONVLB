import os

from bingo_app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5002")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
