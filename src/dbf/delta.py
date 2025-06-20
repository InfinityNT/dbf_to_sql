from typing import Dict, List, Set

class DeltaDetector:
    """Detect changes between DBF file snapshots using checksums"""
    
    def compute_deltas(self, old_checksums: Dict[int, int], 
                      new_checksums: Dict[int, int]) -> Dict[str, List[int]]:
        """
        Compute deltas between two checksum maps
        
        Args:
            old_checksums: Previous checksum map {record_index: checksum}
            new_checksums: Current checksum map {record_index: checksum}
            
        Returns:
            Dictionary with lists of record indices for inserts, updates, deletes
        """
        old_indices = set(old_checksums.keys())
        new_indices = set(new_checksums.keys())
        
        # Records that exist in new but not in old (inserts)
        inserts = list(new_indices - old_indices)
        
        # Records that exist in old but not in new (deletes)
        deletes = list(old_indices - new_indices)
        
        # Records that exist in both but have different checksums (updates)
        common_indices = old_indices & new_indices
        updates = [
            idx for idx in common_indices
            if old_checksums[idx] != new_checksums[idx]
        ]
        
        return {
            'inserts': sorted(inserts),
            'updates': sorted(updates), 
            'deletes': sorted(deletes)
        }
    
    def get_change_summary(self, deltas: Dict[str, List[int]]) -> str:
        """Get a human-readable summary of changes"""
        insert_count = len(deltas['inserts'])
        update_count = len(deltas['updates'])
        delete_count = len(deltas['deletes'])
        
        return (f"Changes: {insert_count} inserts, "
               f"{update_count} updates, {delete_count} deletes")
    
    def has_changes(self, deltas: Dict[str, List[int]]) -> bool:
        """Check if there are any changes"""
        return bool(deltas['inserts'] or deltas['updates'] or deltas['deletes'])