import os
import webbrowser
from threading import Timer
from flask import Flask, request, jsonify
from flask_cors import CORS
from predict_specialty import BioBertModel, RobertaModel, EnsembleSoftVoting

# Tell Flask where to look for the HTML/CSS/JS files
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

print("Initializing models globally (this might take a few seconds)...")
try:
    biobert = BioBertModel()
    roberta = RobertaModel()
    ensemble = EnsembleSoftVoting(biobert, roberta)
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")
    ensemble = None

# Serve the frontend UI
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    if not ensemble:
        return jsonify({"error": "Models failed to load."}), 500
        
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
        
    text = data['text']
    try:
        (bio_preds, rob_preds), ens_preds = ensemble.predict(text)
        
        # Sort them to return highest probability first
        def sort_dict(d):
            return [{"label": k, "score": v} for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)]
            
        return jsonify({
            "biobert": sort_dict(bio_preds),
            "roberta": sort_dict(rob_preds),
            "ensemble": sort_dict(ens_preds)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    # Cloud Run expects the app to listen on the PORT environment variable (default 8080)
    port = int(os.environ.get("PORT", 5000))
    
    if os.environ.get("FLASK_ENV") == "development" or os.environ.get("PORT") is None:
        # Give the server a brief second to start, then pop open the web browser!
        Timer(1, open_browser).start()
    
    # Use threaded=False if models run into PyTorch multithreading issues
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
