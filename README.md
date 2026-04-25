# MedClassify - Medical Specialty Ensembler

This repository contains two fine-tuned LLMs (BioBert and RoBERTa) designed to parse medical transcriptions and predict their associated clinical specialty using a soft voting ensemble algorithm.

## Setup Instructions for First-Time Users

Whenever someone downloads this project to their local machine for the first time, they must install the environment dependencies so their computer knows how to run the AI!

1. Open a terminal directly inside this folder.
2. If you don't already have one, create a Python virtual environment:
   `python -m venv venv`
3. Activate the environment:
   - **Windows:** `.\venv\Scripts\activate`
   - **Mac/Linux:** `source venv/bin/activate`
4. Install all the required machine learning modules by running:
   `pip install -r requirements.txt`

## Running the Application (Web Interface)

Once your dependencies are installed, you never have to run setup again! 
To start the models and launch the beautiful web interface, simply run the universal launcher from the root folder:

```bash
python launch.py
```

*(Alternatively, you can manually double-click `scripts/start.bat` on Windows or run `scripts/start.sh` on Mac).*



https://github.com/user-attachments/assets/9ea9ef15-b60a-40a0-9ba4-d64c97f3c81e





## Running the Command Line Interface (CLI)

If you prefer to run the predictions directly in your terminal without the web interface, you can use the underlying Python script! 

It features an **Interactive Mode** that will ask you to supply a transcript directly inside the console.

To run it, type:
```bash
python predict_specialty.py
```

The script will say `Transcript >>>` and wait for you to paste your medical transcription. Once entered, it will instantly generate the Top 5 predictions for BioBert, RoBERTa, and the Final Ensemble!

*(Advanced edge-case: You can also optionally bypass the interactive prompt by providing your text inside quotes directly inline: `python predict_specialty.py "patient has chest pain..."`)*

<img width="3764" height="1509" alt="image" src="https://github.com/user-attachments/assets/17d22fe1-fcfb-4286-8e08-20cba469577c" />


## File Structure

```text
├── predict_specialty.py     # CLI entry-point
├── launch.py                # Web interface launcher
├── requirements.txt         # Python dependencies
├── scripts/
│   ├── start.bat            # Windows launcher
│   └── start.sh             # Mac/Linux launcher
├── BioBertModern/
│   └── bioclinical_modernbert_specialty/
│       ├── config.json              # Model configuration
│       ├── model.safetensors        # Model weights (Safetensors)
│       ├── pytorch_model.bin        # Model weights (PyTorch)
│       └── tokenizer files          # Tokenizer files
├── roberta_best/
│   └── hf_model/
│       ├── config.json              # Model configuration
│       ├── model.safetensors        # Model weights (Safetensors)
│       ├── pytorch_model.bin        # Model weights (PyTorch)
│       ├── label_mappings.json      # Label mappings
│       └── tokenizer files          # Tokenizer files
├── BioBertTraining.ipynb            # BioBERT training
├── Roberta_finetuning.ipynb         # RoBERTa training
└── ensembled_model_metric.ipynb     # Ensembled model metrics evaluation
```
