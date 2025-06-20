import asyncio
import logging
from pathlib import Path
from typing import Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.dbf.sync import DBFSyncService
from src.config import settings

logger = logging.getLogger(__name__)

class DBFFileHandler(FileSystemEventHandler):
    """Handle DBF file changes"""
    
    def __init__(self, sync_service: 'DBFSyncService'):
        self.sync_service = sync_service
        self.processing: Set[str] = set()
        
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process DBF files
        if file_path.suffix.upper() not in ['.DBF']:
            return
            
        # Avoid duplicate processing
        if str(file_path) in self.processing:
            logger.debug(f"Already processing {file_path}, skipping")
            return
            
        logger.info(f"DBF file modified: {file_path}")
        
        # Process file asynchronously
        asyncio.create_task(self._process_file(str(file_path)))
    
    async def _process_file(self, file_path: str):
        """Process a modified DBF file"""
        try:
            self.processing.add(file_path)
            
            # Small delay to ensure file write is complete
            await asyncio.sleep(1)
            
            # Process the file
            await self.sync_service.process_dbf_file(file_path)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        finally:
            self.processing.discard(file_path)

class DBFWatcherService:
    """Service to monitor DBF files for changes"""
    
    def __init__(self):
        self.observer = Observer()
        self.sync_service = DBFSyncService()
        self.handler = DBFFileHandler(self.sync_service)
        self.is_running = False
        
    def start(self):
        """Start monitoring DBF files"""
        watch_path = Path(settings.dbf_watch_path)
        
        if not watch_path.exists():
            logger.warning(f"DBF watch path does not exist: {watch_path}")
            return
            
        logger.info(f"Starting DBF file watcher on: {watch_path}")
        
        # Set up file system watcher
        self.observer.schedule(
            self.handler,
            str(watch_path),
            recursive=True
        )
        
        self.observer.start()
        self.is_running = True
        
        # Process existing files on startup
        asyncio.create_task(self._initial_scan())
        
        logger.info("DBF file watcher started successfully")
    
    def stop(self):
        """Stop monitoring"""
        if self.is_running:
            logger.info("Stopping DBF file watcher")
            self.observer.stop()
            self.observer.join()
            self.is_running = False
    
    async def _initial_scan(self):
        """Scan for existing DBF files on startup"""
        try:
            watch_path = Path(settings.dbf_watch_path)
            logger.info("Performing initial scan of DBF files")
            
            # Find all DBF files
            dbf_files = list(watch_path.glob("**/*.DBF")) + list(watch_path.glob("**/*.dbf"))
            
            logger.info(f"Found {len(dbf_files)} DBF files")
            
            # Process each file
            for dbf_file in dbf_files:
                try:
                    await self.sync_service.process_dbf_file(str(dbf_file))
                except Exception as e:
                    logger.error(f"Error processing {dbf_file} during initial scan: {e}")
                    
        except Exception as e:
            logger.error(f"Error during initial scan: {e}")

# Global watcher instance
dbf_watcher = DBFWatcherService()