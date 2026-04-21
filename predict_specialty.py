import sys
import os
import json
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class BioBertModel:
    def __init__(self, path="BioBertModern/bioclinical_modernbert_specialty"):
        print("Loading BioBert tokenizer and model...")
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForSequenceClassification.from_pretrained(path)
        
    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=8192)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        
        predictions = {}
        for i, p in enumerate(probs):
            # Safe access if id2label holds keys as strings or ints
            label = self.model.config.id2label.get(i) or self.model.config.id2label.get(str(i))
            predictions[label] = p.item()
        return predictions

class RobertaModel:
    def __init__(self, path="roberta_best/hf_model"):
        print("Loading RoBERTa tokenizer and model...")
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForSequenceClassification.from_pretrained(path)
        
        with open(os.path.join(path, "label_mappings.json"), "r") as f:
            self.mapping = json.load(f)["id2label"]
            
    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
            
        predictions = {}
        for i, p in enumerate(probs):
            label = self.mapping[str(i)]
            predictions[label] = p.item()
        return predictions

class EnsembleSoftVoting:
    """Takes predictions from multiple models and averages their probabilities."""
    def __init__(self, *models):
        self.models = models

    def predict(self, text):
        all_model_preds = []
        for model in self.models:
            all_model_preds.append(model.predict(text))
            
        ensemble_scores = {}
        # Union of all distinct labels across all models
        all_labels = set()
        for preds in all_model_preds:
            all_labels.update(preds.keys())
            
        # Calculate Soft Voting (average of probabilities)
        for label in all_labels:
            total_prob = sum(preds.get(label, 0.0) for preds in all_model_preds)
            ensemble_scores[label] = total_prob / len(self.models)
            
        # Return individual model predictions and the final ensemble score
        return all_model_preds, ensemble_scores

def print_all(title, scores_dict):
    sorted_scores = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    print(f"\n[ {title} All Predictions ]")
    for i, (label, prob) in enumerate(sorted_scores, 1):
        print(f"{i}. {label} ({prob:.2%})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = "Patient is a 55-year-old male presenting with chest pain, shortness of breath, and diaphoresis. EKG shows STEMI."
        
    print("-" * 50)
    biobert = BioBertModel()
    roberta = RobertaModel()
    
    # Initialize the soft voting ensemble with both models
    ensemble = EnsembleSoftVoting(biobert, roberta)
    
    print("-" * 50)
    print(f"\nInput text: {text}")
    print("-" * 50)
    
    # Get predictions
    (bio_preds, rob_preds), ens_preds = ensemble.predict(text)
    
    # Print results
    print_all("BioBert", bio_preds)
    print_all("RoBERTa", rob_preds)
    print_all("Final ENSEMBLE Soft Voting", ens_preds)
