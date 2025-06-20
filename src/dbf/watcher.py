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
            
        # Only process specific files we're interested in
        if not self._should_process_file(file_path):
            logger.debug(f"Skipping file not in target list: {file_path}")
            return
            
        # Avoid duplicate processing
        if str(file_path) in self.processing:
            logger.debug(f"Already processing {file_path}, skipping")
            return
            
        logger.info(f"DBF file modified: {file_path}")
        
        # Process file asynchronously
        asyncio.create_task(self._process_file(str(file_path)))
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if this file should be processed"""
        file_name = file_path.name.lower()
        
        # Only process specific files
        target_files = ['clientes.dbf', 'arts.dbf', 'movim.dbf']
        
        return file_name in target_files
    
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
            logger.info("Performing initial scan of target DBF files")
            
            # Find all DBF files
            all_dbf_files = list(watch_path.glob("**/*.DBF")) + list(watch_path.glob("**/*.dbf"))
            
            # Filter to only target files
            target_files = ['clientes.dbf', 'arts.dbf', 'movim.dbf']
            dbf_files = [f for f in all_dbf_files if f.name.lower() in target_files]
            
            logger.info(f"Found {len(all_dbf_files)} total DBF files, processing {len(dbf_files)} target files")
            
            # Process each target file
            for dbf_file in dbf_files:
                try:
                    logger.info(f"Processing target file: {dbf_file.name}")
                    await self.sync_service.process_dbf_file(str(dbf_file))
                except Exception as e:
                    logger.error(f"Error processing {dbf_file} during initial scan: {e}")
                    
        except Exception as e:
            logger.error(f"Error during initial scan: {e}")

# Global watcher instance
dbf_watcher = DBFWatcherService()