import struct
import zlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dbfread import DBF
import logging

logger = logging.getLogger(__name__)

class DBFReader:
    """DBF file reader with delta detection capabilities"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.dbf = None
        
    def inspect_structure(self) -> Dict[str, Any]:
        """Inspect DBF file structure and return field information"""
        try:
            dbf = DBF(str(self.file_path), load=False)
            
            fields_info = []
            for field in dbf.fields:
                field_info = {
                    'name': field.name,
                    'type': field.type,
                    'length': field.length,
                    'decimal_count': getattr(field, 'decimal_count', 0)
                }
                fields_info.append(field_info)
            
            # Get header info
            with open(self.file_path, 'rb') as f:
                # Read DBF header
                header = f.read(32)
                num_records = struct.unpack('<I', header[4:8])[0]
                header_length = struct.unpack('<H', header[8:10])[0] 
                record_length = struct.unpack('<H', header[10:12])[0]
                
            return {
                'file_path': str(self.file_path),
                'num_records': num_records,
                'header_length': header_length,
                'record_length': record_length,
                'fields': fields_info
            }
            
        except Exception as e:
            logger.error(f"Error inspecting DBF structure: {e}")
            return {}
    
    def get_sample_records(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample records from DBF file"""
        try:
            # Handle memo files automatically
            dbf = DBF(str(self.file_path), load=False)
            records = []
            
            for i, record in enumerate(dbf):
                if i >= limit:
                    break
                # Convert record to dict and handle any encoding issues
                record_dict = dict(record)
                records.append(record_dict)
                
            return records
            
        except Exception as e:
            logger.error(f"Error reading sample records: {e}")
            return []
    
    def compute_record_checksums(self) -> Dict[int, int]:
        """Compute CRC32 checksum for each record"""
        checksums = {}
        
        try:
            with open(self.file_path, 'rb') as f:
                # Read header to get record info
                header = f.read(32)
                num_records = struct.unpack('<I', header[4:8])[0]
                header_length = struct.unpack('<H', header[8:10])[0]
                record_length = struct.unpack('<H', header[10:12])[0]
                
                # Position at first record
                f.seek(header_length)
                
                for i in range(num_records):
                    record_data = f.read(record_length)
                    if len(record_data) == record_length:
                        checksum = zlib.crc32(record_data) & 0xffffffff
                        checksums[i] = checksum
                        
            logger.info(f"Computed checksums for {len(checksums)} records")
            return checksums
            
        except Exception as e:
            logger.error(f"Error computing checksums: {e}")
            return {}
    
    def read_all_records(self) -> List[Dict[str, Any]]:
        """Read all records from DBF file"""
        try:
            # Handle memo files automatically
            dbf = DBF(str(self.file_path), load=False)
            records = []
            
            for record in dbf:
                record_dict = dict(record)
                records.append(record_dict)
                
            logger.info(f"Read {len(records)} records from {self.file_path}")
            return records
            
        except Exception as e:
            logger.error(f"Error reading all records: {e}")
            return []
    
    def check_memo_requirement(self) -> Dict[str, Any]:
        """Check if DBF file requires memo files and detect memo fields"""
        memo_info = {
            'requires_memo': False,
            'memo_file_type': None,
            'memo_fields': [],
            'header_type': None
        }
        
        try:
            # Read first byte of header to determine DB type
            with open(self.file_path, 'rb') as f:
                db_type = f.read(1)[0]
                memo_info['header_type'] = f"0x{db_type:02X}"
                
                # Check if memo is required based on header
                if db_type in [0x83, 0x8B]:  # dBASE with .DBT
                    memo_info['requires_memo'] = True
                    memo_info['memo_file_type'] = 'DBT'
                elif db_type in [0xF5, 0x30]:  # FoxPro with .FPT
                    memo_info['requires_memo'] = True  
                    memo_info['memo_file_type'] = 'FPT'
            
            # Check for memo fields
            dbf = DBF(str(self.file_path), load=False)
            for field in dbf.fields:
                if field.type == 'M':
                    memo_info['memo_fields'].append(field.name)
                    memo_info['requires_memo'] = True
                    
            return memo_info
            
        except Exception as e:
            logger.error(f"Error checking memo requirement: {e}")
            return memo_info