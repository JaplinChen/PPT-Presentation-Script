"""
Centralized state management for the application.
"""
from typing import Dict, Optional

class StateManager:
    """Manages application state including uploaded files, parse status, and jobs"""
    
    def __init__(self):
        # File uploads and metadata
        self.uploaded_files: Dict[str, Dict] = {}
        
        # Background parsing status
        self.parse_status: Dict[str, Dict] = {}
        
        # Script generation cache
        self.generation_cache: Dict[str, Dict] = {}
        
        # Narrated PPT job tracking
        self.ppt_jobs: Dict[str, Dict] = {}
    
    # Uploaded Files
    def add_uploaded_file(self, file_id: str, data: Dict):
        """Add or update uploaded file metadata"""
        self.uploaded_files[file_id] = data
    
    def get_uploaded_file(self, file_id: str) -> Optional[Dict]:
        """Get uploaded file metadata"""
        return self.uploaded_files.get(file_id)
    
    def delete_uploaded_file(self, file_id: str):
        """Delete uploaded file metadata"""
        if file_id in self.uploaded_files:
            del self.uploaded_files[file_id]
    
    # Parse Status
    def set_parse_status(self, file_id: str, status: Dict):
        """Set parsing status"""
        self.parse_status[file_id] = status
    
    def get_parse_status(self, file_id: str) -> Optional[Dict]:
        """Get parsing status"""
        return self.parse_status.get(file_id)
    
    # Generation Cache
    def set_generation_cache(self, file_id: str, data: Dict):
        """Cache generated script"""
        self.generation_cache[file_id] = data
    
    def get_generation_cache(self, file_id: str) -> Optional[Dict]:
        """Get cached script"""
        return self.generation_cache.get(file_id)
    
    def clear_generation_cache_for_file(self, file_id: str):
        """Clear all cached generations for a specific file"""
        keys_to_delete = [key for key in self.generation_cache.keys() if key.startswith(f"{file_id}|")]
        for key in keys_to_delete:
            del self.generation_cache[key]
    
    # PPT Jobs
    def add_ppt_job(self, job_id: str, data: Dict):
        """Add narrated PPT job"""
        self.ppt_jobs[job_id] = data
    
    def get_ppt_job(self, job_id: str) -> Optional[Dict]:
        """Get PPT job status"""
        return self.ppt_jobs.get(job_id)
    
    def update_ppt_job(self, job_id: str, updates: Dict):
        """Update PPT job status"""
        if job_id in self.ppt_jobs:
            self.ppt_jobs[job_id].update(updates)

# Global state manager instance
state = StateManager()
