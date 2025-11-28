"""
Backblaze B2 Storage module for storing LinkedIn PDFs.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

try:
    from b2sdk.v2 import B2Api, InMemoryAccountInfo
except ImportError:
    B2Api = None
    InMemoryAccountInfo = None

logger = logging.getLogger(__name__)


class B2Storage:
    """
    Backblaze B2 storage handler for PDF files.
    """
    
    def __init__(
        self,
        key_id: str = None,
        application_key: str = None,
        bucket_name: str = None
    ):
        if B2Api is None:
            raise ImportError("b2sdk is not installed. Install with: pip install b2sdk")
        
        self.key_id = key_id or os.getenv("B2_KEY_ID", "")
        self.application_key = application_key or os.getenv("B2_APPLICATION_KEY", "")
        self.bucket_name = bucket_name or os.getenv("B2_BUCKET_NAME", "alumni-pdfs")
        
        self.b2_api: Optional[B2Api] = None
        self.bucket = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize B2 API connection."""
        try:
            if not self.key_id or not self.application_key:
                logger.error("B2 credentials not configured")
                return False
            
            info = InMemoryAccountInfo()
            self.b2_api = B2Api(info)
            self.b2_api.authorize_account("production", self.key_id, self.application_key)
            
            # Get the bucket
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            self._initialized = True
            
            logger.info(f"B2 storage initialized successfully. Bucket: {self.bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize B2 storage: {e}")
            return False
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str = None,
        content_type: str = "application/pdf"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to B2 storage.
        
        Args:
            local_path: Path to local file
            remote_path: Optional remote path/key. If not provided, uses filename with timestamp
            content_type: MIME type of the file
            
        Returns:
            Tuple of (success, file_url, file_key)
        """
        if not self._initialized:
            if not self.initialize():
                return False, None, None
        
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                logger.error(f"Local file not found: {local_path}")
                return False, None, None
            
            # Generate remote path if not provided
            if not remote_path:
                timestamp = datetime.now().strftime('%Y/%m/%d')
                remote_path = f"profiles/{timestamp}/{local_file.name}"
            
            # Upload the file
            uploaded_file = self.bucket.upload_local_file(
                local_file=str(local_file),
                file_name=remote_path,
                content_type=content_type
            )
            
            # Get file URL
            file_url = self.bucket.get_download_url(remote_path)
            file_key = uploaded_file.id_
            
            logger.info(f"File uploaded successfully: {remote_path}")
            return True, file_url, file_key
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False, None, None
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from B2 storage.
        
        Args:
            remote_path: Remote file path/key
            local_path: Local destination path
            
        Returns:
            bool indicating success
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            downloaded_file = self.bucket.download_file_by_name(remote_path)
            downloaded_file.save_to(str(local_file))
            
            logger.info(f"File downloaded successfully: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def delete_file(self, file_id: str, file_name: str) -> bool:
        """
        Delete a file from B2 storage.
        
        Args:
            file_id: B2 file ID
            file_name: B2 file name
            
        Returns:
            bool indicating success
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            self.b2_api.delete_file_version(file_id, file_name)
            logger.info(f"File deleted successfully: {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        List files in the bucket with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter files
            limit: Maximum number of files to return
            
        Returns:
            List of file info dictionaries
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            files = []
            for file_version, _ in self.bucket.ls(folder_to_list=prefix, latest_only=True):
                files.append({
                    'id': file_version.id_,
                    'name': file_version.file_name,
                    'size': file_version.size,
                    'upload_timestamp': file_version.upload_timestamp,
                    'content_type': file_version.content_type
                })
                if len(files) >= limit:
                    break
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def get_download_url(self, remote_path: str) -> Optional[str]:
        """
        Get the download URL for a file.
        
        Args:
            remote_path: Remote file path/key
            
        Returns:
            Download URL or None if failed
        """
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            return self.bucket.get_download_url(remote_path)
        except Exception as e:
            logger.error(f"Failed to get download URL: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        if not self._initialized:
            if not self.initialize():
                return {}
        
        try:
            total_size = 0
            file_count = 0
            
            for file_version, _ in self.bucket.ls(latest_only=True):
                total_size += file_version.size
                file_count += 1
            
            return {
                'bucket_name': self.bucket_name,
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
