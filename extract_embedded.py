#!/usr/bin/env python3
import re
import os
import zipfile
from io import BytesIO

def extract_embedded_python():
    with open('acli', 'rb') as f:
        data = f.read()
    
    # Find all PK headers
    pk_pattern = b'PK\x03\x04'
    matches = []
    
    start_pos = 0
    while True:
        pos = data.find(pk_pattern, start_pos)
        if pos == -1:
            break
        matches.append(pos)
        start_pos = pos + 1
    
    print(f"Found {len(matches)} ZIP entries")
    
    # Look for the start of the rovodev archive
    rovo_start = None
    for pos in matches:
        # Check around the position for rovodev content
        check_data = data[pos:pos+300]
        if b'atlassian_cli_rovodev' in check_data:
            rovo_start = pos
            print(f"Found rovodev archive starting at position: {pos}")
            break
    
    if not rovo_start:
        print("Could not find rovodev archive")
        return
    
    # Find the end of central directory record
    eocd_pattern = b'PK\x05\x06'
    eocd_pos = data.rfind(eocd_pattern)
    
    if eocd_pos == -1:
        print("Could not find end of central directory")
        return
    
    print(f"Found EOCD at position: {eocd_pos}")
    
    # Extract the ZIP data
    zip_data = data[rovo_start:eocd_pos+22]  # Include EOCD record
    
    # Try to process as ZIP
    try:
        with zipfile.ZipFile(BytesIO(zip_data), 'r') as zf:
            print(f"ZIP file contains {len(zf.namelist())} files")
            
            # Extract only rovodev related files
            for name in zf.namelist():
                if 'atlassian_cli_rovodev' in name and name.endswith('.py'):
                    try:
                        content = zf.read(name)
                        
                        # Create directory structure
                        os.makedirs(os.path.dirname(name), exist_ok=True)
                        
                        # Write file
                        with open(name, 'wb') as out_file:
                            out_file.write(content)
                        print(f"Extracted: {name}")
                    except Exception as e:
                        print(f"Error extracting {name}: {e}")
    
    except zipfile.BadZipFile as e:
        print(f"Bad ZIP file: {e}")
        # Try to extract individual files manually
        extract_individual_files(data, matches)

def extract_individual_files(data, matches):
    print("Attempting manual extraction...")
    os.makedirs('extracted_rovo', exist_ok=True)
    
    for i, pos in enumerate(matches):
        try:
            # Read local file header
            if pos + 30 > len(data):
                continue
                
            header = data[pos:pos+30]
            if header[:4] != b'PK\x03\x04':
                continue
            
            # Parse header
            filename_len = int.from_bytes(header[26:28], 'little')
            extra_len = int.from_bytes(header[28:30], 'little')
            
            if pos + 30 + filename_len > len(data):
                continue
                
            filename = data[pos+30:pos+30+filename_len].decode('utf-8', errors='ignore')
            
            if 'atlassian_cli_rovodev' in filename and '.py' in filename:
                print(f"Found file: {filename}")
                
                # Get compressed size from next entry or estimate
                file_start = pos + 30 + filename_len + extra_len
                if i + 1 < len(matches):
                    file_end = matches[i + 1]
                else:
                    file_end = min(file_start + 50000, len(data))
                
                file_data = data[file_start:file_end]
                
                # Try to decompress if it looks compressed
                try:
                    import zlib
                    decompressed = zlib.decompress(file_data, -15)  # Raw deflate
                    
                    # Save the file
                    safe_filename = filename.replace('lib/', 'extracted_rovo/')
                    os.makedirs(os.path.dirname(safe_filename), exist_ok=True)
                    
                    with open(safe_filename, 'wb') as f:
                        f.write(decompressed)
                    print(f"Extracted: {safe_filename}")
                    
                except:
                    # Save raw data
                    safe_filename = filename.replace('lib/', 'extracted_rovo/') + '.raw'
                    os.makedirs(os.path.dirname(safe_filename), exist_ok=True)
                    
                    with open(safe_filename, 'wb') as f:
                        f.write(file_data[:1000])  # Just first 1KB
                    print(f"Saved raw: {safe_filename}")
                    
        except Exception as e:
            continue

if __name__ == "__main__":
    extract_embedded_python()
