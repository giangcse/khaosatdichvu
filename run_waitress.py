import os
from waitress import serve

# Import the Flask app from wsgi (which prefers app factory)
from wsgi import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    threads = int(os.getenv("THREADS", "8"))
    connection_limit = int(os.getenv("CONN_LIMIT", "100"))

    print(f"Starting Waitress on {host}:{port} ...")
    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        connection_limit=connection_limit,
        url_scheme="https" if os.getenv("FORCE_HTTPS", "false").lower() == "true" else "http",
        ident="khaosatdichvu/production",
    )


