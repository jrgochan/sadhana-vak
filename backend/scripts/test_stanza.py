import stanza
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_stanza")

def main():
    logger.info("Downloading stanza Sanskrit model if missing...")
    try:
        stanza.download('sa')
        nlp = stanza.Pipeline('sa', processors='tokenize,pos,lemma')
        text = "विद्वान् पुरुषः सत्यं जानति"
        doc = nlp(text)
        for sentence in doc.sentences:
            for word in sentence.words:
                logger.info(f"Word: {word.text}\tLemma: {word.lemma}\tUPOS: {word.upos} \tFeatures: {word.feats}")
    except Exception as e:
        logger.error(f"Error loading Stanza sa model: {e}")

if __name__ == "__main__":
    main()
