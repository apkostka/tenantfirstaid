#!/usr/bin/env python3
"""
Improved script to split a large JSONL file by chapter_number field.
Each output file will be strictly under 10MB.
"""

import json
import os
from collections import defaultdict
from pathlib import Path

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

def split_jsonl_by_chapter_strict(input_file, output_dir, max_size_mb=10):
    """
    Split JSONL file by chapter_number, keeping files strictly under max_size_mb.
    
    Args:
        input_file: Path to input JSONL file
        output_dir: Directory to save split files
        max_size_mb: Maximum size per file in MB
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # First pass: group records by chapter_number
    chapter_records = defaultdict(list)
    
    print(f"Reading {input_file}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
            
            try:
                record = json.loads(line.strip())
                chapter_num = record.get('chapter_number', 'null')
                chapter_records[chapter_num].append(record)
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
    
    print(f"Found {len(chapter_records)} unique chapter numbers")
    
    # Second pass: write files, using actual file sizes to stay under limit
    current_chapters = []
    file_counter = 1
    file_metadata = []
    
    # Sort chapters to ensure consistent output
    sorted_chapters = sorted(chapter_records.keys(), key=lambda x: (x is None, x))
    
    # Create temporary file to track current size
    temp_file = output_path / "temp_current.jsonl"
    
    for chapter_num in sorted_chapters:
        records = chapter_records[chapter_num]
        print(f"Processing chapter {chapter_num} with {len(records)} records...")
        
        # Try adding this chapter to current file
        with open(temp_file, 'w', encoding='utf-8') as f:
            # Write existing chapters if any
            for existing_chapter in current_chapters:
                for record in chapter_records[existing_chapter]:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            
            # Write new chapter
            for record in records:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        
        temp_size = get_file_size_mb(temp_file)
        
        if temp_size > max_size_mb and current_chapters:
            # Would exceed limit, write current file first
            filename = f"ORS_part_{file_counter:03d}.jsonl"
            output_file = output_path / filename
            
            # Write current chapters (without the new one)
            record_count = 0
            with open(output_file, 'w', encoding='utf-8') as f:
                for existing_chapter in current_chapters:
                    for record in chapter_records[existing_chapter]:
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n')
                        record_count += 1
            
            actual_size = get_file_size_mb(output_file)
            chapter_list = ', '.join(map(str, current_chapters[:10]))
            if len(current_chapters) > 10:
                chapter_list += f" ... and {len(current_chapters) - 10} more"
            
            print(f"  Wrote {filename}: {record_count} records, {actual_size:.1f}MB")
            print(f"    Chapters: {chapter_list}")
            
            # Track metadata
            file_metadata.append({
                'filename': filename,
                'chapters': current_chapters.copy(),
                'record_count': record_count,
                'size_mb': actual_size
            })
            
            file_counter += 1
            current_chapters = [chapter_num]
        else:
            # Add to current batch
            current_chapters.append(chapter_num)
    
    # Write remaining records
    if current_chapters:
        filename = f"ORS_part_{file_counter:03d}.jsonl"
        output_file = output_path / filename
        
        record_count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for chapter in current_chapters:
                for record in chapter_records[chapter]:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
                    record_count += 1
        
        actual_size = get_file_size_mb(output_file)
        chapter_list = ', '.join(map(str, current_chapters[:10]))
        if len(current_chapters) > 10:
            chapter_list += f" ... and {len(current_chapters) - 10} more"
        
        print(f"  Wrote {filename}: {record_count} records, {actual_size:.1f}MB")
        print(f"    Chapters: {chapter_list}")
        
        # Track metadata
        file_metadata.append({
            'filename': filename,
            'chapters': current_chapters.copy(),
            'record_count': record_count,
            'size_mb': actual_size
        })
    
    # Clean up temp file
    if temp_file.exists():
        temp_file.unlink()
    
    # Write metadata file
    metadata_file = output_path / "file_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(file_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\nMetadata saved to {metadata_file}")
    print(f"Split complete! Files saved to {output_dir}")
    
    # Show final file sizes
    print("\nFinal output file sizes:")
    total_size = 0
    for file_info in file_metadata:
        size_mb = file_info['size_mb']
        total_size += size_mb
        print(f"  {file_info['filename']}: {size_mb:.1f}MB ({file_info['record_count']} records)")
    
    print(f"\nTotal size: {total_size:.1f}MB")
    original_size = get_file_size_mb(input_file)
    print(f"Original size: {original_size:.1f}MB")

if __name__ == "__main__":
    input_file = "/home/anko/projects/tenantfirstaid/backend/scripts/documents/or/ORS_full.jsonl"
    output_dir = "/home/anko/projects/tenantfirstaid/backend/scripts/documents/or/split_chapters_strict"
    
    print(f"Splitting {input_file} into files strictly under 10MB each...")
    split_jsonl_by_chapter_strict(input_file, output_dir)
