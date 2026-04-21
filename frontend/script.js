const textarea = document.getElementById('transcript-input');
const charCount = document.getElementById('char-count');
const clearBtn = document.getElementById('clear-btn');
const predictBtn = document.getElementById('predict-btn');
const samplePills = document.querySelectorAll('.pill');

// Character counter
textarea.addEventListener('input', () => {
    const len = textarea.value.length;
    charCount.innerText = `${len} chars`;
});

// Clear button
clearBtn.addEventListener('click', () => {
    textarea.value = '';
    charCount.innerText = `0 chars`;
    textarea.focus();
});

// Sample pills
samplePills.forEach(pill => {
    pill.addEventListener('click', () => {
        textarea.value = pill.getAttribute('data-text');
        charCount.innerText = `${textarea.value.length} chars`;
    });
});

// Prediction
predictBtn.addEventListener('click', async () => {
    const textInput = textarea.value.trim();
    const errorMsg = document.getElementById('error-msg');
    const resultsSection = document.getElementById('results-section');
    const btnLoader = document.getElementById('btn-loader');
    const btnText = document.querySelector('#predict-btn span');

    if (!textInput) {
        errorMsg.innerText = "Please enter a clinical transcript.";
        return;
    }

    // Reset UI
    errorMsg.innerText = "";
    resultsSection.style.display = 'none';
    btnLoader.style.display = 'block';
    btnText.style.display = 'none';

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textInput })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to fetch prediction.");
        }

        // Render visual charts (TOP 5)
        renderBars('biobert-results', data.biobert.slice(0, 5), 'biobert');
        renderBars('roberta-results', data.roberta.slice(0, 5), 'roberta');
        // The image shows ensemble in cyan
        renderBars('ensemble-results', data.ensemble.slice(0, 5), 'ensemble');

        resultsSection.style.display = 'grid';

        // Trigger animations by allowing a tiny delay before setting width
        setTimeout(() => {
            document.querySelectorAll('.bar-fill').forEach(el => {
                el.style.width = el.getAttribute('data-width');
            });
        }, 50);

    } catch (err) {
        errorMsg.innerText = "Error: " + err.message;
    } finally {
        btnLoader.style.display = 'none';
        btnText.style.display = 'block';
    }
});

function renderBars(containerId, results, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = ""; // clear previous

    results.forEach((item, index) => {
        const probPct = (item.score * 100).toFixed(2);
        
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';

        const infoDiv = document.createElement('div');
        infoDiv.className = 'bar-info';

        const labelSpan = document.createElement('span');
        labelSpan.className = 'bar-label';
        labelSpan.innerText = `${item.label}`;
        
        // Highlight top 1 result
        if (index === 0) {
            labelSpan.style.color = '#fff';
            labelSpan.style.fontWeight = '600';
        }

        const probSpan = document.createElement('span');
        probSpan.className = 'bar-prob';
        probSpan.innerText = `${probPct}%`;
        if (type === 'ensemble' && index === 0) {
            probSpan.style.color = 'var(--cyan-accent)';
        }

        infoDiv.appendChild(labelSpan);
        infoDiv.appendChild(probSpan);

        const trackDiv = document.createElement('div');
        trackDiv.className = 'bar-track';

        const fillDiv = document.createElement('div');
        fillDiv.className = 'bar-fill';
        fillDiv.setAttribute('data-width', `${probPct}%`);

        trackDiv.appendChild(fillDiv);
        barContainer.appendChild(infoDiv);
        barContainer.appendChild(trackDiv);

        container.appendChild(barContainer);
    });
}
