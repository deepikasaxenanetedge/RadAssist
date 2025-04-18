import spacy
import sys

def process_medical_transcription(transcription_text):
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Error: Model not found. Please install the required dependencies.")
        return None
    
    # Process the text
    doc = nlp(transcription_text)
    
    # Extract information
    results = {
        "sentences": [sent.text for sent in doc.sents],
        "entities": [{"text": ent.text, "label": ent.label_} for ent in doc.ents],
        "tokens": [{"text": token.text, "lemma": token.lemma_, "pos": token.pos_} for token in doc]
    }
    
    return results

def print_results(results):
    """Print the processed results in a readable format"""
    if not results:
        return
    
    print("\n=== PROCESSED MEDICAL TRANSCRIPTION ===\n")
    
    print("SENTENCES:")
    for i, sent in enumerate(results["sentences"], 1):
        print(f"{i}. {sent}")
    
    print("\nENTITIES:")
    if results["entities"]:
        for i, ent in enumerate(results["entities"], 1):
            print(f"{i}. {ent['text']} ({ent['label']})")
    else:
        print("No entities detected.")
    
    print("\nTOKEN ANALYSIS (first 10):")
    for i, token in enumerate(results["tokens"][:10], 1):
        print(f"{i}. '{token['text']}' - Lemma: {token['lemma']}, POS: {token['pos']}")
    
    if len(results["tokens"]) > 10:
        print(f"...and {len(results['tokens']) - 10} more tokens")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file if provided as argument
        with open(sys.argv[1], 'r') as file:
            transcription = file.read()
    else:
        # Otherwise, prompt for input
        print("Please enter your medical transcription text (press Ctrl+D or Ctrl+Z when done):")
        transcription_lines = []
        try:
            while True:
                line = input()
                transcription_lines.append(line)
        except EOFError:
            pass
        transcription = "\n".join(transcription_lines)
    
    # Process the transcription
    if transcription.strip():
        results = process_medical_transcription(transcription)
        print_results(results)
    else:
        print("No transcription provided.")