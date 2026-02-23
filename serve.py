import os
import time
from livereload import Server, shell
import build_site

def run_build():
    print(f"\n[Watcher] Change detected at {time.strftime('%H:%M:%S')}")
    try:
        build_site.build()
        print("[Watcher] Build successful.")
    except Exception as e:
        print(f"[Watcher] Build error: {e}")

if __name__ == "__main__":
    if not build_site.SITE.exists():
        build_site.build()

    server = Server()

    server.watch("ctfs/", run_build)
    server.watch("templates/", run_build)
    server.watch("static/", run_build)
    server.watch("authors.yml", run_build)
    server.watch("build_site.py", run_build)

    print("[System] Starting LiveReload server on http://localhost:8000")
    server.serve(root=str(build_site.SITE), port=8000, host="0.0.0.0")