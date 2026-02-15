import spacy
from spacy_layout import spaCyLayout

nlp = spacy.blank("en")
layout = spaCyLayout(nlp)

def extract_text(file_path):
    doc = layout(file_path)
    return doc._.markdown