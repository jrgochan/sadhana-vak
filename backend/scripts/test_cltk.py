import sys
import logging

# We will need the stanza models for CLTK sanskrit. 
# CLTK automatically downloads them on first use if not present, but it might take a moment.
from cltk.nlp import NLP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_cltk")

def main():
    logger.info("Initializing CLTK Sanskrit pipeline...")
    try:
        # Initialize the Sanskrit pipeline, explicitly disabling embeddings
        cltk_nlp = NLP(language="san", suppress_banner=True)
        cltk_nlp.pipeline.processes.pop(-2) # Remove SanskritEmbeddingsProcess
        
        # We only need morphosyntactic analysis for the verifier, 
        # but let's see what the default pipeline gives us.
        text = "विद्वान् पुरुषः सत्यं जानति"  # The wise man knows the truth.
        logger.info(f"Processing text: {text}")
        
        doc = cltk_nlp.analyze(text)
        
        logger.info("Words and Morphological Tags:")
        for word in doc.words:
            logger.info(f"Word: {word.string}")
            logger.info(f"  Lemma: {word.lemma}")
            logger.info(f"  POS  : {word.upos}")
            logger.info(f"  Morph: {word.features}")
            
    except Exception as e:
        logger.error(f"CLTK error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
