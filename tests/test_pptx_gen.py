import unittest
import sys
from pathlib import Path

# Add project root and src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.image_matcher import match_images
from src.lesson_parser import LezioneSpec, SlideSpec
from src.pptx_renderer import PPTXRenderer, SlideContent

class TestPPTXGenerator(unittest.TestCase):
    def test_image_matcher(self):
        # Create a temporary images directory
        tmp_images = Path("test_images")
        tmp_images.mkdir(exist_ok=True)
        (tmp_images / "TestDoc_img_001.png").touch()
        (tmp_images / "OtherDoc_img_002.png").touch()
        
        used = set()
        # Test exact match (normalized)
        match = match_images(["TestDoc.pdf"], tmp_images, used)
        self.assertIsNotNone(match)
        self.assertTrue(match.endswith("TestDoc_img_001.png"))
        
        # Test used images tracking
        match2 = match_images(["TestDoc"], tmp_images, used)
        self.assertIsNone(match2) # Already in 'used'
        
        # Cleanup
        for f in tmp_images.glob("*"): f.unlink()
        tmp_images.rmdir()

    def test_renderer_basic(self):
        renderer = PPTXRenderer() # New presentation
        renderer.add_title_slide("Test Title", "Test Subtitle")
        
        slide_data = SlideContent(
            titolo_slide="Slide di Prova",
            bullet_points=["Punto 1", "Punto 2"],
            note_relatore="Note per il relatore",
            source_doc_names=["Doc1"]
        )
        
        renderer.add_content_slide(slide_data)
        
        # Check if we can save it
        out_path = Path("test_output.pptx")
        renderer.save(out_path)
        self.assertTrue(out_path.exists())
        out_path.unlink()

if __name__ == "__main__":
    unittest.main()
