"""
Draiver Context Generator – Image Deduplicator

Standalone script to find and move duplicate images in the output/images folder.
Uses MD5 hashing for speed, as Docling often extracts identical binary data 
referenced multiple times across a document.

Usage:
    python scripts/deduplicate_images.py [--dir output/images] [--dry-run]
"""
import argparse
import hashlib
import logging
import shutil
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("deduplicator")

def get_file_hash(path: Path) -> str:
    """Computes MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        # Read in chunks for memory efficiency with large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def deduplicate(target_dir: Path, dry_run: bool = False):
    if not target_dir.exists():
        logger.error(f"Directory not found: {target_dir}")
        return

    logger.info(f"Scanning directory: {target_dir}")
    
    hashes = {} # hash -> list of paths
    files = list(target_dir.glob("*.png")) + list(target_dir.glob("*.jpg"))
    
    for path in files:
        file_hash = get_file_hash(path)
        if file_hash not in hashes:
            hashes[file_hash] = []
        hashes[file_hash].append(path)

    duplicates_found = 0
    total_freed = 0
    
    dup_dir = target_dir / "duplicates"
    
    for file_hash, paths in hashes.items():
        if len(paths) > 1:
            # Keep the first one, move the others
            # Sort by name length or name to keep the "nicest" or first extracted
            paths.sort(key=lambda x: (len(x.name), x.name))
            keep = paths[0]
            dups = paths[1:]
            
            logger.info(f"Found {len(dups)} duplicates for file: {keep.name}")
            
            for dup in dups:
                duplicates_found += 1
                total_freed += dup.stat().st_size
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would move {dup.name} -> duplicates/")
                else:
                    dup_dir.mkdir(exist_ok=True)
                    dest = dup_dir / dup.name
                    # Handle name collisions in duplicates folder
                    if dest.exists():
                        dest = dup_dir / f"{dup.stem}_{hashlib.md5(dup.name.encode()).hexdigest()[:8]}{dup.suffix}"
                    
                    try:
                        shutil.move(str(dup), str(dest))
                        logger.info(f"Moved {dup.name} to duplicates/")
                    except Exception as e:
                        logger.error(f"Failed to move {dup.name}: {e}")

    print("\n" + "="*40)
    print(f"  Total files scanned: {len(files)}")
    print(f"  Duplicates found:    {duplicates_found}")
    print(f"  Space to be freed:   {total_freed / (1024*1024):.2f} MB")
    print(f"  Action:              {'Dry-run (no changes)' if dry_run else 'Moved to ' + str(dup_dir)}")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deduplicate images in a folder.")
    parser.add_argument("--dir", type=Path, default=Path("output/images"), help="Directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Don't move files, just show what would happen")
    
    args = parser.parse_args()
    deduplicate(args.dir, args.dry_run)
