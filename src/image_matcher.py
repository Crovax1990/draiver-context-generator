"""
Draiver Context Generator – Image Matcher
Matches slide content to available images in output/images/.
"""
import logging
import re
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

def match_images(
    source_doc_names: List[str], 
    images_dir: Path,
    used_images: Set[str]
) -> Optional[str]:
    """
    Finds the first available image that matches any of the source document names.
    Images are expected to follow the pattern: [DocName]_img_[NNN].png
    """
    if not images_dir.exists():
        logger.warning("Images directory %s does not exist", images_dir)
        return None

    all_images = list(images_dir.glob("*.png"))
    
    for doc_name in source_doc_names:
        # Normalize doc_name: remove extension and common suffixes
        clean_name = doc_name.replace(".pdf", "").replace(".docx", "").replace(".pptx", "").strip()
        
        # Build a regex to match the document name at the start of the image filename
        # Pattern: ^[CleanName]_img_\d+\.png
        # We use re.escape to handle special characters in filenames
        pattern = re.compile(
            r"^" + re.escape(clean_name) + r"_img_\d+\.png$", 
            re.IGNORECASE
        )
        
        candidates = [
            img for img in all_images 
            if pattern.match(img.name) and str(img) not in used_images
        ]
        
        if candidates:
            # Sort candidates to be deterministic (e.g. by image number)
            candidates.sort(key=lambda x: x.name)
            selected = candidates[0]
            used_images.add(str(selected))
            logger.info("Matched image %s for doc %s", selected.name, clean_name)
            return str(selected)

    return None

def get_placeholder_image(images_dir: Path) -> Optional[str]:
    """Fallback if no specific match is found."""
    # Could return a generic logo or a randomly selected image from the set
    all_images = list(images_dir.glob("*.png"))
    if all_images:
        return str(all_images[0])
    return None
