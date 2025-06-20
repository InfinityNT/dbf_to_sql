from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import Optional, List
import uvicorn
import logging
import time
import asyncio
from datetime import datetime, date

from src.database import get_db, test_connection, Base, engine
from src.models import Customer, Product, Movement, DBFFileState, SyncLog
from src.api.schemas import CustomerResponse, ProductResponse, MovementResponse
from src.config import settings
from src.utils.logging import setup_logging
from src.dbf.watcher import dbf_watcher

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DBF to SQL API",
    description="Real-time ERP data API from DBF files",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and start file monitoring"""
    logger.info("Starting DBF to SQL API...")
    
    # Wait for database with retries
    max_retries = 30
    retry_interval = 2
    
    logger.info("Waiting for database connection...")
    for attempt in range(max_retries):
        if test_connection():
            logger.info("Database connection established successfully")
            break
        logger.info(f"Database not ready, retrying in {retry_interval}s... (attempt {attempt + 1}/{max_retries})")
        await asyncio.sleep(retry_interval)
    else:
        logger.error("Failed to connect to database after all retries")
        raise Exception("Database connection failed after 30 attempts")
    
    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise Exception("Database table creation failed")
    
    # Start file watcher service
    try:
        dbf_watcher.start()
        logger.info("DBF file watcher started")
    except Exception as e:
        logger.error(f"Failed to start file watcher: {e}")
        # Don't fail startup if file watcher fails - API can still work
        logger.warning("Continuing without file watcher")
    
    logger.info("API started successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DBF to SQL API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check with database status"""
    try:
        # Test database query
        customer_count = db.query(Customer).count()
        product_count = db.query(Product).count()
        movement_count = db.query(Movement).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "records": {
                "customers": customer_count,
                "products": product_count,
                "movements": movement_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Customer endpoints
@app.get("/customers", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ciudad: Optional[str] = None,
    suspendido: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get customers with optional filtering"""
    query = db.query(Customer)
    
    if ciudad:
        query = query.filter(Customer.ciudad.ilike(f"%{ciudad}%"))
    if suspendido is not None:
        query = query.filter(Customer.suspendido == suspendido)
    
    customers = query.offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{numcli}", response_model=CustomerResponse)
async def get_customer(numcli: str, db: Session = Depends(get_db)):
    """Get customer by number"""
    customer = db.query(Customer).filter(Customer.numcli == numcli).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

# Product endpoints
@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    activo: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """Get products with optional filtering"""
    query = db.query(Product)
    
    if marca:
        query = query.filter(Product.marca.ilike(f"%{marca}%"))
    if familia:
        query = query.filter(Product.familia == familia)
    if activo is not None:
        query = query.filter(Product.activo == activo)
    
    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/products/{numart}", response_model=ProductResponse)
async def get_product(numart: str, db: Session = Depends(get_db)):
    """Get product by article number"""
    product = db.query(Product).filter(Product.numart == numart).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Movement endpoints
@app.get("/movements", response_model=List[MovementResponse])
async def get_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tipodoc: Optional[str] = None,
    numdoc: Optional[str] = None,
    numart: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get movements with optional filtering"""
    query = db.query(Movement)
    
    if tipodoc:
        query = query.filter(Movement.tipodoc == tipodoc)
    if numdoc:
        query = query.filter(Movement.numdoc == numdoc)
    if numart:
        query = query.filter(Movement.numart == numart)
    
    movements = query.offset(skip).limit(limit).all()
    return movements

@app.get("/movements/document/{tipodoc}/{numdoc}", response_model=List[MovementResponse])
async def get_movements_by_document(
    tipodoc: str, 
    numdoc: str, 
    db: Session = Depends(get_db)
):
    """Get all movements for a specific document"""
    movements = db.query(Movement).filter(
        Movement.tipodoc == tipodoc,
        Movement.numdoc == numdoc
    ).all()
    
    if not movements:
        raise HTTPException(status_code=404, detail="Document not found")
    return movements

# Analytics endpoints
@app.get("/analytics/sales-summary")
async def get_sales_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get sales summary analytics"""
    # This would require joining with document headers to get dates
    # For now, return basic movement counts
    query = db.query(Movement)
    
    if start_date or end_date:
        # Would need document date fields for proper filtering
        pass
    
    total_movements = query.count()
    sales_movements = query.filter(Movement.tipodoc == 'V').count()  # Assuming 'V' is sales
    
    return {
        "total_movements": total_movements,
        "sales_movements": sales_movements,
        "start_date": start_date,
        "end_date": end_date
    }

# File processing status
@app.get("/status/files")
async def get_file_status(db: Session = Depends(get_db)):
    """Get DBF file processing status"""
    files = db.query(DBFFileState).all()
    return {
        "files": [
            {
                "file_name": f.file_name,
                "record_count": f.record_count,
                "last_processed": f.last_processed,
                "status": f.processing_status
            }
            for f in files
        ]
    }

@app.get("/status/sync-log")
async def get_sync_log(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get recent sync operations log"""
    logs = db.query(SyncLog).order_by(SyncLog.timestamp.desc()).limit(limit).all()
    return {
        "logs": [
            {
                "table_name": log.table_name,
                "operation": log.operation_type,
                "record_count": log.record_count,
                "timestamp": log.timestamp,
                "success": log.success,
                "duration_ms": log.duration_ms
            }
            for log in logs
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )