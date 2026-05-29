import os
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, DATABASE_PATH
from .routes import admin as admin
from .routes import inspector as inspector

# Set default admin credentials if not already set via environment variables
if 'ADMIN_EMAIL' not in os.environ:
    os.environ['ADMIN_EMAIL'] = 'admin@gmail.com'
if 'ADMIN_PASSWORD' not in os.environ:
    os.environ['ADMIN_PASSWORD'] = 'admin123'

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Ensure legacy sqlite schema has the latest medicine columns
try:
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(medicines);')
        columns = [row[1] for row in cursor.fetchall()]
        if 'dosage' not in columns:
            cursor.execute('ALTER TABLE medicines ADD COLUMN dosage TEXT;')
        if 'manufacturer' not in columns:
            cursor.execute('ALTER TABLE medicines ADD COLUMN manufacturer TEXT;')
        conn.commit()
except sqlite3.DatabaseError:
    pass

app = FastAPI(
    title="Tablet Carton Authentication System API",
    description="Offline CV & ML-based pharmaceutical carton verification system.",
    version="1.0.0"
)

# CORS configuration to allow React app connection
app.add_middleware(
    CORSMiddleware,
    # Restrict to the frontend dev server origin so cookies are allowed with credentials
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for serving images (reference, query, and reports)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "reference"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "query"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "reports"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register routers
app.include_router(admin.router)
app.include_router(inspector.router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Tablet Carton Authentication Offline System API"}
