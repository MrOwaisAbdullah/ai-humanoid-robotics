import os
import sys
import subprocess

# For HF Spaces Docker deployment, just start the server directly
if __name__ == "__main__":
    print("🚀 Starting application via app.py for Hugging Face Spaces...")

    # Change to backend directory if needed
    if os.path.exists("backend"):
        os.chdir("backend")
        print("Changed to backend directory")

    # Run start_server.py
    os.execvp(sys.executable, [sys.executable, "start_server.py"])