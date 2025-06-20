import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import SessionLocal
from src.models import Customer, Product, Movement, DBFFileState, SyncLog
from src.dbf.reader import DBFReader
from src.dbf.delta import DeltaDetector

logger = logging.getLogger(__name__)

class DBFSyncService:
    """Service to synchronize DBF files with MySQL database"""
    
    def __init__(self):
        self.delta_detector = DeltaDetector()
        
    async def process_dbf_file(self, file_path: str):
        """Process a single DBF file and sync changes to database"""
        start_time = datetime.now()
        file_name = Path(file_path).name
        
        logger.info(f"Processing DBF file: {file_name}")
        
        db = SessionLocal()
        try:
            # Get or create file state record
            file_state = db.query(DBFFileState).filter(
                DBFFileState.file_path == file_path
            ).first()
            
            if not file_state:
                file_state = DBFFileState(
                    file_path=file_path,
                    file_name=file_name,
                    processing_status='PENDING'
                )
                db.add(file_state)
                db.commit()
                db.refresh(file_state)
            
            # Update status to processing
            file_state.processing_status = 'PROCESSING'
            db.commit()
            
            # Detect changes
            reader = DBFReader(file_path)
            current_checksums = reader.compute_record_checksums()
            
            # Get previous checksums
            previous_checksums = {}
            if file_state.checksum_map:
                try:
                    previous_checksums = json.loads(file_state.checksum_map)
                    # Convert string keys back to int
                    previous_checksums = {int(k): v for k, v in previous_checksums.items()}
                except:
                    logger.warning(f"Could not parse previous checksums for {file_name}")
            
            # Calculate deltas
            deltas = self.delta_detector.compute_deltas(previous_checksums, current_checksums)
            
            # Determine table based on file name
            table_name = self._get_table_name(file_name)
            
            if deltas['inserts'] or deltas['updates'] or deltas['deletes']:
                logger.info(f"Changes detected in {file_name}: "
                          f"{len(deltas['inserts'])} inserts, "
                          f"{len(deltas['updates'])} updates, "
                          f"{len(deltas['deletes'])} deletes")
                
                # Apply changes
                records_processed = await self._apply_changes(
                    db, file_path, table_name, deltas, reader
                )
                
                # Update file state
                file_state.checksum_map = json.dumps(current_checksums)
                file_state.record_count = len(current_checksums)
                file_state.last_modified = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
                file_state.processing_status = 'COMPLETED'
                file_state.last_processed = datetime.now()
                
                # Log sync operation
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                sync_log = SyncLog(
                    file_path=file_path,
                    table_name=table_name,
                    operation_type='UPDATE',
                    record_count=len(current_checksums),
                    records_processed=records_processed,
                    duration_ms=duration_ms,
                    success=True
                )
                db.add(sync_log)
                
            else:
                logger.info(f"No changes detected in {file_name}")
                file_state.processing_status = 'COMPLETED'
                file_state.last_processed = datetime.now()
            
            db.commit()
            logger.info(f"Successfully processed {file_name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            
            # Update file state with error
            if file_state:
                file_state.processing_status = 'ERROR'
                file_state.error_message = str(e)
                
                # Log failed sync
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                sync_log = SyncLog(
                    file_path=file_path,
                    table_name=self._get_table_name(file_name),
                    operation_type='UPDATE',
                    record_count=0,
                    records_processed=0,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=str(e)
                )
                db.add(sync_log)
                db.commit()
                
        finally:
            db.close()
    
    async def _apply_changes(self, db: Session, file_path: str, table_name: str, 
                           deltas: Dict, reader: DBFReader) -> int:
        """Apply detected changes to the database"""
        records_processed = 0
        
        try:
            # Read all records for processing inserts and updates
            all_records = reader.read_all_records()
            
            # Process deletes first
            for record_index in deltas['deletes']:
                await self._delete_record(db, table_name, record_index)
                records_processed += 1
            
            # Process inserts and updates
            for record_index in deltas['inserts'] + deltas['updates']:
                if record_index < len(all_records):
                    record_data = all_records[record_index]
                    await self._upsert_record(db, table_name, record_data)
                    records_processed += 1
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
            
        return records_processed
    
    async def _upsert_record(self, db: Session, table_name: str, record_data: Dict[str, Any]):
        """Insert or update a record in the database"""
        try:
            if table_name == 'customers':
                await self._upsert_customer(db, record_data)
            elif table_name == 'products':
                await self._upsert_product(db, record_data)
            elif table_name == 'movements':
                await self._upsert_movement(db, record_data)
                
        except Exception as e:
            logger.error(f"Error upserting {table_name} record: {e}")
            raise
    
    async def _upsert_customer(self, db: Session, record_data: Dict[str, Any]):
        """Upsert customer record"""
        numcli = record_data.get('NUMCLI')
        if not numcli:
            return
            
        # Clean and normalize the customer number
        numcli = str(numcli).strip()
        if not numcli:
            return
            
        customer = db.query(Customer).filter(Customer.numcli == numcli).first()
        
        if customer:
            # Update existing
            for key, value in record_data.items():
                field_name = key.lower()
                if hasattr(customer, field_name):
                    # Clean string values
                    if isinstance(value, str):
                        value = value.strip() if value else None
                    setattr(customer, field_name, value)
        else:
            # Create new - clean all string values
            customer_data = {}
            for key, value in record_data.items():
                field_name = key.lower()
                if isinstance(value, str):
                    value = value.strip() if value else None
                customer_data[field_name] = value
            
            # Ensure numcli is set correctly
            customer_data['numcli'] = numcli
            customer = Customer(**customer_data)
            db.add(customer)
    
    async def _upsert_product(self, db: Session, record_data: Dict[str, Any]):
        """Upsert product record"""
        numart = record_data.get('NUMART')
        if not numart:
            return
            
        # Clean and normalize the product number
        numart = str(numart).strip()
        if not numart:
            return
            
        product = db.query(Product).filter(Product.numart == numart).first()
        
        # Map DBF field names to model field names
        field_mapping = {
            'DESC': 'desc_product',
            'SERIES': 'series_control'
        }
        
        if product:
            # Update existing
            for key, value in record_data.items():
                model_field = field_mapping.get(key, key.lower())
                if hasattr(product, model_field):
                    setattr(product, model_field, value)
        else:
            # Create new
            product_data = {}
            for key, value in record_data.items():
                model_field = field_mapping.get(key, key.lower())
                product_data[model_field] = value
                
            product = Product(**product_data)
            db.add(product)
    
    async def _upsert_movement(self, db: Session, record_data: Dict[str, Any]):
        """Upsert movement record"""
        # Movements are usually append-only, so we'll just insert
        # Clean all string values first
        
        movement_data = {}
        for key, value in record_data.items():
            field_name = key.lower()
            if isinstance(value, str):
                value = value.strip() if value else None
            movement_data[field_name] = value
        
        movement = Movement(**movement_data)
        db.add(movement)
    
    async def _delete_record(self, db: Session, table_name: str, record_index: int):
        """Delete a record (placeholder - implement based on your business logic)"""
        # Note: DBF record index doesn't directly map to database primary key
        # You might need additional logic to identify which record to delete
        logger.warning(f"Delete operation not implemented for {table_name} at index {record_index}")
    
    def _get_table_name(self, file_name: str) -> str:
        """Determine target table based on file name"""
        file_name_lower = file_name.lower()
        
        if 'clientes' in file_name_lower:
            return 'customers'
        elif 'arts' in file_name_lower or 'articulos' in file_name_lower:
            return 'products'
        elif 'movim' in file_name_lower or 'movimientos' in file_name_lower:
            return 'movements'
        else:
            return 'unknown'
    
    async def bulk_load_file(self, file_path: str) -> int:
        """Perform initial bulk load of a DBF file"""
        start_time = datetime.now()
        file_name = Path(file_path).name
        table_name = self._get_table_name(file_name)
        
        logger.info(f"Starting bulk load for {file_name}")
        
        db = SessionLocal()
        try:
            reader = DBFReader(file_path)
            all_records = reader.read_all_records()
            
            logger.info(f"Bulk loading {len(all_records)} records into {table_name}")
            
            records_processed = 0
            batch_size = 1000
            
            for i in range(0, len(all_records), batch_size):
                batch = all_records[i:i + batch_size]
                
                for record_data in batch:
                    await self._upsert_record(db, table_name, record_data)
                    records_processed += 1
                
                db.commit()
                logger.info(f"Processed {records_processed}/{len(all_records)} records")
            
            # Update file state
            checksums = reader.compute_record_checksums()
            file_state = DBFFileState(
                file_path=file_path,
                file_name=file_name,
                last_modified=datetime.fromtimestamp(Path(file_path).stat().st_mtime),
                record_count=len(checksums),
                checksum_map=json.dumps(checksums),
                processing_status='COMPLETED'
            )
            db.merge(file_state)
            
            # Log bulk load operation
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            sync_log = SyncLog(
                file_path=file_path,
                table_name=table_name,
                operation_type='BULK_LOAD',
                record_count=len(all_records),
                records_processed=records_processed,
                duration_ms=duration_ms,
                success=True
            )
            db.add(sync_log)
            db.commit()
            
            logger.info(f"Bulk load completed for {file_name}: {records_processed} records")
            return records_processed
            
        except Exception as e:
            logger.error(f"Error during bulk load of {file_name}: {e}")
            db.rollback()
            
            # Log failed bulk load
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            sync_log = SyncLog(
                file_path=file_path,
                table_name=table_name,
                operation_type='BULK_LOAD',
                record_count=0,
                records_processed=0,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
            db.add(sync_log)
            db.commit()
            raise
            
        finally:
            db.close()