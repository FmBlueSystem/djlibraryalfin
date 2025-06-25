"""
TagLib-based metadata writer for DjAlfin.
Provides superior performance and reliability compared to mutagen/eyeD3.
"""

import os
import taglib
from typing import Dict, Optional, List, Union, Any

class TagLibMetadataWriter:
    """
    High-performance metadata writer using TagLib.
    
    Benefits over mutagen/eyeD3:
    - No external dependencies (eyeD3)
    - Consistent API across all formats
    - Better preservation of existing metadata
    - Atomic operations (safe writes)
    - Native performance
    """
    
    # Standard tag mappings for writing
    WRITE_TAG_MAP = {
        'title': 'TITLE',
        'artist': 'ARTIST', 
        'album': 'ALBUM',
        'albumartist': 'ALBUMARTIST',
        'genre': 'GENRE',
        'year': 'DATE',
        'date': 'DATE',
        'track': 'TRACKNUMBER',
        'track_number': 'TRACKNUMBER',
        'disc': 'DISCNUMBER',
        'comment': 'COMMENT',
        'comments': 'COMMENT'
    }
    
    # DJ-specific tag mappings
    DJ_TAG_MAP = {
        'bpm': 'BPM',
        'key': 'INITIALKEY', 
        'energy': 'ENERGY',
        'energylevel': 'ENERGYLEVEL',
        'mood': 'MOOD',
        'rating': 'RATING',
        'grouping': 'GROUPING',
        'label': 'LABEL'
    }
    
    # Analysis tags for DJ software compatibility
    ANALYSIS_TAG_MAP = {
        'danceability': 'DANCEABILITY',
        'valence': 'VALENCE',
        'acousticness': 'ACOUSTICNESS',
        'instrumentalness': 'INSTRUMENTALNESS',
        'liveness': 'LIVENESS',
        'speechiness': 'SPEECHINESS',
        'loudness': 'LOUDNESS',
        'tempo_confidence': 'TEMPO_CONFIDENCE',
        'key_confidence': 'KEY_CONFIDENCE'
    }
    
    @classmethod
    def write_metadata(cls, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to audio file using TagLib.
        
        Args:
            file_path: Path to audio file
            metadata: Dictionary with metadata to write
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
            
        if not metadata:
            print(f"⚠️ No metadata provided for: {file_path}")
            return False
            
        try:
            # Use save_on_exit for atomic operations
            with taglib.File(file_path, save_on_exit=True) as audio_file:
                if not audio_file.tags:
                    print(f"⚠️ Could not access tags for: {file_path}")
                    return False
                
                # Write standard metadata
                success_count = 0
                total_count = 0
                
                for field, value in metadata.items():
                    if cls._write_field(audio_file, field, value):
                        success_count += 1
                    total_count += 1
                
                # File is automatically saved on context exit
                print(f"✅ Written {success_count}/{total_count} fields to: {os.path.basename(file_path)}")
                return success_count > 0
                
        except Exception as e:
            print(f"❌ TagLib write error for {file_path}: {e}")
            return False
    
    @classmethod
    def _write_field(cls, audio_file, field: str, value: Any) -> bool:
        """Write a single metadata field."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
            
        # Normalize field name
        field_lower = field.lower()
        
        # Determine target tag name
        tag_name = None
        if field_lower in cls.WRITE_TAG_MAP:
            tag_name = cls.WRITE_TAG_MAP[field_lower]
        elif field_lower in cls.DJ_TAG_MAP:
            tag_name = cls.DJ_TAG_MAP[field_lower]
        elif field_lower in cls.ANALYSIS_TAG_MAP:
            tag_name = cls.ANALYSIS_TAG_MAP[field_lower]
        else:
            # Use field name as-is for custom tags
            tag_name = field.upper()
        
        try:
            # Convert value to appropriate format
            if isinstance(value, (int, float)):
                tag_value = [str(value)]
            elif isinstance(value, str):
                tag_value = [value.strip()]
            elif isinstance(value, list):
                tag_value = [str(v).strip() for v in value if v]
            else:
                tag_value = [str(value)]
            
            # Special handling for certain fields
            if field_lower == 'year' or field_lower == 'date':
                tag_value = [cls._normalize_year(tag_value[0])]
            elif field_lower in ['bpm', 'energy', 'rating']:
                tag_value = [cls._normalize_numeric(tag_value[0])]
            elif field_lower in ['key', 'initialkey']:
                tag_value = [cls._normalize_key(tag_value[0])]
            
            # Write to file
            audio_file.tags[tag_name] = tag_value
            return True
            
        except Exception as e:
            print(f"❌ Error writing field '{field}': {e}")
            return False
    
    @classmethod
    def _normalize_year(cls, value: str) -> str:
        """Normalize year value to YYYY format."""
        if not value:
            return ""
            
        # Extract 4-digit year from various formats
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', str(value))
        if year_match:
            return year_match.group()
        return str(value)[:4] if len(str(value)) >= 4 else str(value)
    
    @classmethod
    def _normalize_numeric(cls, value: str) -> str:
        """Normalize numeric values."""
        if isinstance(value, (int, float)):
            return str(value)
            
        # Extract numeric part from strings like "120.5 BPM"
        import re
        numeric_match = re.search(r'[\d.]+', str(value))
        if numeric_match:
            return numeric_match.group()
        return str(value)
    
    @classmethod
    def _normalize_key(cls, value: str) -> str:
        """Normalize key notation."""
        if not value:
            return ""
            
        value = str(value).strip()
        
        # Handle Open Key notation (1A, 2B, etc.)
        if len(value) == 2 and value[0].isdigit() and value[1].isalpha():
            return value.upper()
        
        # Handle standard notation
        return value.title()
    
    @classmethod
    def write_single_field(cls, file_path: str, field: str, value: Any) -> bool:
        """
        Write a single metadata field to file.
        
        Args:
            file_path: Path to audio file
            field: Field name to write
            value: Value to write
            
        Returns:
            True if successful, False otherwise
        """
        return cls.write_metadata(file_path, {field: value})
    
    @classmethod
    def update_metadata(cls, file_path: str, updates: Dict[str, Any], preserve_existing: bool = True) -> bool:
        """
        Update specific metadata fields while preserving others.
        
        Args:
            file_path: Path to audio file
            updates: Dictionary with fields to update
            preserve_existing: Whether to preserve existing metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not preserve_existing:
            return cls.write_metadata(file_path, updates)
        
        try:
            # Read existing metadata first
            existing_metadata = {}
            with taglib.File(file_path) as audio_file:
                if audio_file.tags:
                    existing_metadata = {k: v for k, v in audio_file.tags.items()}
            
            # Merge with updates
            merged_metadata = {}
            
            # Convert existing tags to our field names for merging
            for tag_name, tag_values in existing_metadata.items():
                field_name = cls._tag_to_field_name(tag_name)
                if field_name and tag_values:
                    merged_metadata[field_name] = tag_values[0] if len(tag_values) == 1 else tag_values
            
            # Apply updates
            merged_metadata.update(updates)
            
            return cls.write_metadata(file_path, merged_metadata)
            
        except Exception as e:
            print(f"❌ Error updating metadata for {file_path}: {e}")
            return False
    
    @classmethod 
    def _tag_to_field_name(cls, tag_name: str) -> Optional[str]:
        """Convert tag name back to field name for merging."""
        tag_upper = tag_name.upper()
        
        # Reverse lookup in our maps
        for field, tag in cls.WRITE_TAG_MAP.items():
            if tag == tag_upper:
                return field
                
        for field, tag in cls.DJ_TAG_MAP.items():
            if tag == tag_upper:
                return field
                
        for field, tag in cls.ANALYSIS_TAG_MAP.items():
            if tag == tag_upper:
                return field
        
        return tag_name.lower()
    
    @classmethod
    def clear_metadata(cls, file_path: str, fields: Optional[List[str]] = None) -> bool:
        """
        Clear specific metadata fields or all metadata.
        
        Args:
            file_path: Path to audio file
            fields: List of fields to clear, or None for all
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with taglib.File(file_path, save_on_exit=True) as audio_file:
                if not audio_file.tags:
                    return False
                
                if fields is None:
                    # Clear all tags
                    audio_file.tags.clear()
                    print(f"✅ Cleared all metadata from: {os.path.basename(file_path)}")
                else:
                    # Clear specific fields
                    cleared_count = 0
                    for field in fields:
                        tag_name = cls._field_to_tag_name(field)
                        if tag_name and tag_name in audio_file.tags:
                            del audio_file.tags[tag_name]
                            cleared_count += 1
                    
                    print(f"✅ Cleared {cleared_count} fields from: {os.path.basename(file_path)}")
                
                return True
                
        except Exception as e:
            print(f"❌ Error clearing metadata for {file_path}: {e}")
            return False
    
    @classmethod
    def _field_to_tag_name(cls, field: str) -> Optional[str]:
        """Convert field name to tag name."""
        field_lower = field.lower()
        
        if field_lower in cls.WRITE_TAG_MAP:
            return cls.WRITE_TAG_MAP[field_lower]
        elif field_lower in cls.DJ_TAG_MAP:
            return cls.DJ_TAG_MAP[field_lower]
        elif field_lower in cls.ANALYSIS_TAG_MAP:
            return cls.ANALYSIS_TAG_MAP[field_lower]
        
        return field.upper()
    
    @classmethod
    def backup_metadata(cls, file_path: str) -> Optional[Dict]:
        """
        Create a backup of current metadata.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with current metadata or None if error
        """
        try:
            with taglib.File(file_path) as audio_file:
                if not audio_file.tags:
                    return None
                
                backup = {}
                for tag_name, tag_values in audio_file.tags.items():
                    backup[tag_name] = tag_values.copy() if isinstance(tag_values, list) else tag_values
                
                return backup
                
        except Exception as e:
            print(f"❌ Error backing up metadata for {file_path}: {e}")
            return None
    
    @classmethod
    def restore_metadata(cls, file_path: str, backup: Dict) -> bool:
        """
        Restore metadata from backup.
        
        Args:
            file_path: Path to audio file
            backup: Backup dictionary from backup_metadata()
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with taglib.File(file_path, save_on_exit=True) as audio_file:
                # Clear existing tags
                audio_file.tags.clear()
                
                # Restore from backup
                for tag_name, tag_values in backup.items():
                    audio_file.tags[tag_name] = tag_values.copy() if isinstance(tag_values, list) else tag_values
                
                print(f"✅ Restored metadata for: {os.path.basename(file_path)}")
                return True
                
        except Exception as e:
            print(f"❌ Error restoring metadata for {file_path}: {e}")
            return False


# Compatibility functions for drop-in replacement
def write_metadata(file_path: str, metadata: Dict[str, Any]) -> bool:
    """Drop-in replacement for mutagen-based write_metadata function."""
    return TagLibMetadataWriter.write_metadata(file_path, metadata)

def write_metadata_tag(file_path: str, field: str, value: Any) -> bool:
    """Drop-in replacement for single field writing."""
    return TagLibMetadataWriter.write_single_field(file_path, field, value)

def write_metadata_tags(file_path: str, metadata: Dict[str, Any]) -> bool:
    """Drop-in replacement for batch writing."""
    return TagLibMetadataWriter.write_metadata(file_path, metadata)


if __name__ == "__main__":
    # Test with a copy of the Rihanna track
    import shutil
    
    source_file = "/Volumes/KINGSTON/Audio/Rihanna Feat. Drake - Work_PN.flac"
    test_file = "/tmp/test_taglib_write.flac"
    
    if os.path.exists(source_file):
        print("🎵 Testing TagLib metadata writer...")
        
        # Create test copy
        shutil.copy2(source_file, test_file)
        print(f"📁 Created test copy: {test_file}")
        
        # Test writing metadata
        test_metadata = {
            'title': 'TagLib Test Title',
            'artist': 'TagLib Test Artist',
            'album': 'TagLib Test Album',
            'bpm': '128.5',
            'key': '4A',
            'comments': 'Written by TagLib writer test'
        }
        
        success = write_metadata(test_file, test_metadata)
        print(f"📝 Write result: {'✅ Success' if success else '❌ Failed'}")
        
        if success:
            # Verify by reading back
            from .taglib_metadata_reader import read_metadata
            read_back = read_metadata(test_file)
            
            if read_back:
                print(f"\n📖 Verification - read back metadata:")
                for key in test_metadata:
                    written_value = test_metadata[key]
                    read_value = read_back.get(key, 'NOT FOUND')
                    match = '✅' if str(written_value) == str(read_value) else '❌'
                    print(f"  {key}: {written_value} -> {read_value} {match}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️ Cleaned up test file")
    
    else:
        print(f"❌ Source file not found: {source_file}")