#!/usr/bin/env python3
"""
Script to split a large JSONL file by chapter_number field.
Each output file will be under 10MB and contain records for one or more chapters.
"""

import json
import os
from collections import defaultdict
from pathlib import Path

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

def split_jsonl_by_chapter(input_file, output_dir, max_size_mb=10):
    """
    Split JSONL file by chapter_number, keeping files under max_size_mb.
    
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
    
    # Second pass: write files, combining chapters if needed to stay under size limit
    current_file_records = []
    current_chapters = []
    file_counter = 1
    file_metadata = []  # Track which chapters are in which files
    
    # Sort chapters to ensure consistent output
    sorted_chapters = sorted(chapter_records.keys(), key=lambda x: (x is None, x))
    
    for chapter_num in sorted_chapters:
        records = chapter_records[chapter_num]
        
        # Create a temporary file to check size
        temp_records = current_file_records + records
        temp_filename = output_path / "temp_test.jsonl"
        
        # Write temp file to check size
        with open(temp_filename, 'w', encoding='utf-8') as f:
            for record in temp_records:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        
        temp_size = get_file_size_mb(temp_filename)
        os.remove(temp_filename)  # Clean up temp file
        
        if temp_size > max_size_mb and current_file_records:
            # Current batch would exceed limit, write current batch first
            filename = f"ORS_part_{file_counter:03d}.jsonl"
            output_file = output_path / filename
            
            chapter_list = ', '.join(map(str, current_chapters[:10]))  # Show first 10 chapters
            if len(current_chapters) > 10:
                chapter_list += f" ... and {len(current_chapters) - 10} more"
            
            print(f"Writing {filename} with {len(current_file_records)} records ({get_file_size_estimate(current_file_records):.1f}MB)")
            print(f"  Chapters: {chapter_list}")
            
            # Track metadata
            file_metadata.append({
                'filename': filename,
                'chapters': current_chapters.copy(),
                'record_count': len(current_file_records)
            })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for record in current_file_records:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            
            file_counter += 1
            current_file_records = records
            current_chapters = [chapter_num]
        else:
            # Add to current batch
            current_file_records.extend(records)
            current_chapters.append(chapter_num)
    
    # Write remaining records
    if current_file_records:
        filename = f"ORS_part_{file_counter:03d}.jsonl"
        output_file = output_path / filename
        
        chapter_list = ', '.join(map(str, current_chapters[:10]))  # Show first 10 chapters
        if len(current_chapters) > 10:
            chapter_list += f" ... and {len(current_chapters) - 10} more"
        
        print(f"Writing {filename} with {len(current_file_records)} records ({get_file_size_estimate(current_file_records):.1f}MB)")
        print(f"  Chapters: {chapter_list}")
        
        # Track metadata
        file_metadata.append({
            'filename': filename,
            'chapters': current_chapters.copy(),
            'record_count': len(current_file_records)
        })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in current_file_records:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
    
    # Write metadata file
    metadata_file = output_path / "file_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(file_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Metadata saved to {metadata_file}")
    
    print(f"\nSplit complete! Files saved to {output_dir}")
    
    # Show final file sizes
    print("\nOutput file sizes:")
    for file in sorted(output_path.glob("ORS_part_*.jsonl")):
        size_mb = get_file_size_mb(file)
        print(f"  {file.name}: {size_mb:.1f}MB")

def get_file_size_estimate(records):
    """Estimate file size in MB for a list of records"""
    if not records:
        return 0
    
    # Estimate based on JSON serialization of a sample
    sample_size = min(100, len(records))
    sample_bytes = sum(len(json.dumps(record, ensure_ascii=False)) + 1 for record in records[:sample_size])
    avg_bytes_per_record = sample_bytes / sample_size
    total_bytes = avg_bytes_per_record * len(records)
    return total_bytes / (1024 * 1024)

if __name__ == "__main__":
    input_file = "/home/anko/projects/tenantfirstaid/backend/scripts/documents/or/ORS_full.jsonl"
    output_dir = "/home/anko/projects/tenantfirstaid/backend/scripts/documents/or/split_chapters"
    
    print(f"Splitting {input_file} into files under 10MB each...")
    split_jsonl_by_chapter(input_file, output_dir)
