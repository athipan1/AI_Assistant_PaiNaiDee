"""
Model Download Script
Pre-downloads HuggingFace models for faster startup
"""

import os
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
import torch

def download_models():
    """Download and cache the models used by the application"""
    models_to_download = [
        ("tiiuae/falcon-7b-instruct", "causal"),
        ("facebook/bart-large-cnn", "seq2seq")
    ]
    
    print("Starting model downloads...")
    
    for model_name, model_type in models_to_download:
        try:
            print(f"Downloading {model_name}...")
            
            # Download tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"✓ Tokenizer downloaded for {model_name}")
            
            # Download model based on type
            if model_type == "causal":
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            else:  # seq2seq
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            print(f"✓ Model downloaded for {model_name}")
            
        except Exception as e:
            print(f"✗ Failed to download {model_name}: {e}")
    
    print("Model downloads completed!")

if __name__ == "__main__":
    download_models()