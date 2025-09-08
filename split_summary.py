#!/usr/bin/env python3
"""
Summary of JSONL file splitting results
"""

import json
from pathlib import Path

def show_split_summary():
    """Show summary of the split operation"""
    
    strict_dir = Path("/home/anko/projects/tenantfirstaid/backend/scripts/documents/or/split_chapters_strict")
    metadata_file = strict_dir / "file_metadata.json"
    
    if not metadata_file.exists():
        print("Metadata file not found")
        return
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print("JSONL File Split Summary")
    print("=" * 50)
    print(f"Original file: ORS_full.jsonl (69.8MB)")
    print(f"Split into: {len(metadata)} files")
    print(f"Target: Each file under 10MB")
    print()
    
    total_records = 0
    total_size = 0
    
    print("Individual Files:")
    print("-" * 50)
    for i, file_info in enumerate(metadata, 1):
        filename = file_info['filename']
        size_mb = file_info['size_mb']
        record_count = file_info['record_count']
        chapters = file_info['chapters']
        
        total_records += record_count
        total_size += size_mb
        
        print(f"{i}. {filename}")
        print(f"   Size: {size_mb:.1f}MB")
        print(f"   Records: {record_count:,}")
        print(f"   Chapters: {len(chapters)} chapters")
        
        # Show first few and last few chapters
        if len(chapters) <= 10:
            chapter_str = ", ".join(chapters)
        else:
            first_5 = ", ".join(chapters[:5])
            last_5 = ", ".join(chapters[-5:])
            chapter_str = f"{first_5} ... {last_5}"
        print(f"   Range: {chapter_str}")
        print()
    
    print("Summary:")
    print("-" * 50)
    print(f"Total records: {total_records:,}")
    print(f"Total size: {total_size:.1f}MB")
    print(f"Average file size: {total_size / len(metadata):.1f}MB")
    print(f"Largest file: {max(file_info['size_mb'] for file_info in metadata):.1f}MB")
    print(f"Smallest file: {min(file_info['size_mb'] for file_info in metadata):.1f}MB")
    
    # Count null vs non-null chapters
    null_records = next(file_info['record_count'] for file_info in metadata if 'null' in file_info['chapters'])
    non_null_records = total_records - null_records
    
    print()
    print("Chapter Distribution:")
    print("-" * 50)
    print(f"Records with chapter numbers: {non_null_records:,}")
    print(f"Records with null chapter: {null_records:,}")
    print(f"Null chapter percentage: {(null_records / total_records) * 100:.1f}%")

if __name__ == "__main__":
    show_split_summary()
