
"""
This is the main entry point for the FastAPI application.

It handles the application setup, including:
- Initializing the FastAPI app.
- Including API routers for different functionalities (bank transaction).
- Configuring CORS (Cross-Origin Resource Sharing) middleware.
- Importing the centralized logger from a utility file.
- Running the application using Uvicorn.
"""

import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import transaction
from backend.utils.logger import log_message
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- FastAPI Application Initialization ---

log_message('info', "Initializing FastAPI application...")
app = FastAPI(
    title="Project API",
    description="API for managing project proposals and an AI-powered agent.",
    version="1.0.0"
)

#index api:
@app.get("/")
def read_root():
    """
    This endpoint returns a JSON object with a welcome message.
    """
    return {"message": "Welcome to Bank Reconcilation"}

log_message('info', "Including API routers.")
try:

    app.include_router(transaction.router, tags=["Transaction Pipeline"])
except Exception as e:
    log_message('critical', f"Failed to include routers: {e}")
    sys.exit(1)  # Exit if a critical component fails to load.


try:
    origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    origins = origins_str.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log_message('info', f"CORS middleware configured with origins: {origins}")
except Exception as e:
    log_message('error', f"Failed to configure CORS middleware: {e}")
    # Application can still run, so we log the error but don't exit.

# --- Main Execution Block ---

if __name__ == "__main__":
    log_message('info', "Attempting to start Uvicorn server...")
    try:
        # Use environment variables to define host and port.
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))

        # Run the FastAPI application using Uvicorn.
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        # A critical error occurred that prevented the server from starting.
        log_message('critical', f"Failed to start Uvicorn server: {e}")
        raise # Re-raise the exception after logging for external error handling systems.