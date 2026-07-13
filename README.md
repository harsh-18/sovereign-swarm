# Sovereign Swarm - Multi-Tone Video Captioner

A sleek, premium Streamlit application that processes short video clips (under 30 seconds), extracts keyframes, and uses Fireworks AI model endpoints to generate captions in multiple distinct styles (Formal, Sarcastic, Humorous Tech, and Everyday Humor).

## 🚀 Features

- **High-Quality UI:** Built with custom dark styling, CSS-based cards for frame previews, and modern tabs for exploring different caption tones.
- **Auto Frame Extraction:** Uses OpenCV to extract exactly three evenly spaced frames (at 25%, 50%, and 75% progression) from the video.
- **Fireworks AI Vision Model:** Utilizes `llama-v3p2-11b-vision-instruct` to process the extracted frames and generate a detailed scene-by-scene description.
- **Fireworks AI Text Model:** Leverages `llama-v3-70b-instruct` to convert raw descriptions into a structured JSON payload containing 4 specialized caption tones.
- **Local API Config:** Easily configure your Fireworks AI API Key dynamically via the sidebar or load it from environment variables.

---

## 🛠️ Installation

Ensure you have Python 3.8+ installed. Then, follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/harsh-18/sovereign-swarm.git
   cd sovereign-swarm
   ```

2. **Install Dependencies:**
   ```bash
   pip install streamlit opencv-python openai
   ```

---

## ⚡ Quick Start

1. **Run the Streamlit Application:**
   ```bash
   streamlit run app.py
   ```

2. **Access in Browser:**
   Open [http://localhost:8501](http://localhost:8501) in your browser.

3. **Configure API Key:**
   - Enter your Fireworks AI API Key in the sidebar input, **OR**
   - Export it in your environment:
     ```bash
     export FIREWORKS_API_KEY="your_api_key_here"
     ```

4. **Upload and Caption:**
   - Upload an MP4 video clip under 30 seconds.
   - Review metadata and extracted keyframes.
   - Click **Generate Multi-Tone Captions** to see the results.

---

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
