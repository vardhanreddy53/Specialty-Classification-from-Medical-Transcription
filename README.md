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

## Running the Application

Once your dependencies are installed, you never have to run setup again! 
To start the models and launch the beautiful web interface, simply run the universal launcher from the root folder:

```bash
python launch.py
```

*(Alternatively, you can manually double-click `scripts/start.bat` on Windows or run `scripts/start.sh` on Mac).*
