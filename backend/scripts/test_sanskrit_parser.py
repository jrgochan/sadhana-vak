import logging
from sanskrit_parser.parser.sandhi_analyzer import LexicalSandhiAnalyzer
from sanskrit_parser.base.sanskrit_base import SanskritObject

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_sanskrit_parser")

def main():
    logger.info("Initializing LexicalSandhiAnalyzer...")
    try:
        # The analyzer builds a graph of possible splits and morphological matches
        analyzer = LexicalSandhiAnalyzer()
        
        # Test sentence (we expect the LLM to output sentences like this for us to score)
        text_str = "विद्वान् पुरुषः सत्यं जानति"
        text = SanskritObject(text_str)
        logger.info(f"Parsing sentence: {text_str}")
        
        # Use simple split for now to see how many valid paths it finds
        graph = analyzer.getSandhiSplits(text)
        
        splits = graph.find_all_paths()
        logger.info(f"Found {len(splits)} valid derivation paths.")
        
        for i, split in enumerate(splits[:3]): # Just look at the first 3
            logger.info(f"Path {i+1}: {split}")
            
    except Exception as e:
        logger.error(f"Error checking sanskrit_parser: {e}")

if __name__ == "__main__":
    main()
