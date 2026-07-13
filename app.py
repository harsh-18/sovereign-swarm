import streamlit as st
import cv2
import tempfile
import base64
import os
import json
from openai import OpenAI

# Page config
st.set_page_config(
    page_title="Multi-Tone Caption Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium dark styling with custom fonts and subtle animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;500;600&display=swap');
    
    /* Font overrides */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Container Title */
    .hero-container {
        padding: 2rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 2.5rem;
        text-align: center;
    }
    
    .hero-title {
        background: linear-gradient(90deg, #a855f7 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        color: #9ca3af;
        font-size: 1.15rem;
        font-weight: 400;
    }

    /* Cards for Extracted Frames */
    .frame-card {
        background: #1f2937;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 10px;
        text-align: center;
        margin-top: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .frame-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    .frame-label {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-top: 8px;
        font-weight: 500;
    }

    /* Custom Accent Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #9ca3af;
        transition: all 0.2s ease-in-out;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        border-color: #3b82f6;
    }

    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
        border-color: #3b82f6 !important;
    }

    /* Caption Tone Card styling */
    .caption-box {
        background: #111827;
        border-left: 5px solid #a855f7;
        padding: 1.5rem;
        border-radius: 4px 12px 12px 4px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .caption-box-formal {
        border-left-color: #3b82f6;
    }
    .caption-box-sarcastic {
        border-left-color: #f59e0b;
    }
    .caption-box-tech {
        border-left-color: #10b981;
    }
    .caption-box-everyday {
        border-left-color: #ec4899;
    }

    .caption-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .caption-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #f3f4f6;
    }
    
    /* Footer styles */
    .footer-text {
        color: #4b5563;
        text-align: center;
        margin-top: 3rem;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🎬 Multi-Tone Video Captioner</div>
        <div class="hero-subtitle">Transform your short clips into engaging, AI-generated captions across multiple styles and personalities.</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar layout
st.sidebar.markdown("### ⚙️ API Configuration")
api_key_input = st.sidebar.text_input(
    "Fireworks AI API Key",
    type="password",
    value=os.environ.get("FIREWORKS_API_KEY", ""),
    help="Enter your API Key from your Fireworks AI dashboard. If already set as environment variable, it will be auto-filled."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### ℹ️ How it works:
1. **Upload** a video clip (< 30s).
2. **OpenCV** extracts exactly 3 evenly spaced frames.
3. **Llama 3.2 Vision** generates a raw scene-by-scene description.
4. **Llama 3.3 Text** converts that description into structured JSON with 4 distinct tones.
""")

# Initialize client if key is available
client = None
if api_key_input:
    client = OpenAI(
        api_key=api_key_input,
        base_url="https://api.fireworks.ai/inference/v1"
    )
else:
    st.sidebar.warning("Please provide your Fireworks AI API Key to proceed.")

# Helper Functions
def process_video_metadata(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    return {
        "duration": duration,
        "fps": fps,
        "frame_count": frame_count,
        "resolution": f"{width}x{height}"
    }

def extract_key_frames(video_path, total_frames):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    # 3 evenly spaced frames: 25%, 50%, 75%
    frame_indices = [
        max(0, min(int(total_frames * 0.25), total_frames - 1)),
        max(0, min(int(total_frames * 0.50), total_frames - 1)),
        max(0, min(int(total_frames * 0.75), total_frames - 1))
    ]
    
    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # OpenCV loads in BGR; convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append((idx, frame_rgb))
        else:
            # Fallback if position set fails
            pass
            
    cap.release()
    return frames

def encode_image_base64(image_rgb):
    # Convert RGB back to BGR for OpenCV encoding
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ret, jpeg_buffer = cv2.imencode('.jpg', image_bgr)
    if not ret:
        raise ValueError("Failed to encode image to JPEG")
    return base64.b64encode(jpeg_buffer).decode('utf-8')

# Main workflow UI
uploaded_file = st.file_uploader("Upload an MP4 Video File", type=["mp4"])

if uploaded_file is not None:
    # Save the file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_filepath = temp_file.name

    # Fetch metadata
    metadata = process_video_metadata(temp_filepath)
    
    if metadata:
        duration = metadata["duration"]
        
        # Check duration limit (under 30s)
        if duration > 30.0:
            st.error(f"❌ Video is too long ({duration:.1f}s). Please upload a video under 30 seconds.")
            os.remove(temp_filepath)
        else:
            # Show file metadata & video preview
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("### 🎥 Video Preview")
                st.video(uploaded_file)
                
            with col2:
                st.markdown("### 📊 File Metadata")
                st.write(f"**Duration:** {duration:.2f} seconds")
                st.write(f"**Framerate:** {metadata['fps']:.2f} FPS")
                st.write(f"**Total Frames:** {metadata['frame_count']}")
                st.write(f"**Resolution:** {metadata['resolution']}")
                
                # Check API client setup
                if client is None:
                    st.info("👈 Please enter your Fireworks AI API Key in the sidebar to generate captions.")
                else:
                    generate_btn = st.button("🚀 Generate Multi-Tone Captions", use_container_width=True)
            
            # Frame Extraction Visualizer
            st.markdown("### 📸 Extracted Key Frames (25%, 50%, 75%)")
            frames_data = extract_key_frames(temp_filepath, metadata["frame_count"])
            
            if len(frames_data) == 3:
                cols = st.columns(3)
                base64_frames = []
                for idx, (frame_idx, frame) in enumerate(frames_data):
                    with cols[idx]:
                        st.image(frame, use_column_width=True)
                        timestamp = frame_idx / metadata["fps"]
                        st.markdown(f"""
                            <div class="frame-card">
                                <div class="frame-label">Frame #{frame_idx} @ {timestamp:.2f}s</div>
                            </div>
                        """, unsafe_allow_html=True)
                    # Convert to base64 for vision model
                    base64_frames.append(encode_image_base64(frame))
            else:
                st.error("Could not extract exactly 3 frames from this video.")
                base64_frames = []
            
            # Caption Generation
            if client and len(base64_frames) == 3 and 'generate_btn' in locals() and generate_btn:
                try:
                    with st.spinner("🧠 Step 1: Llama 3.2 Vision is analyzing the keyframes..."):
                        # Step 1: Vision Model
                        prompt_content = [
                            {
                                "type": "text",
                                "text": (
                                    "These are 3 sequential keyframes extracted from a short video. "
                                    "Please provide a clear and detailed description of the scene, what is happening, "
                                    "the subjects involved, the setting, and the progression of action from frame 1 to frame 3."
                                )
                            }
                        ]
                        for base64_str in base64_frames:
                            prompt_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_str}"
                                }
                            })
                        
                        # Calling vision model
                        vision_response = client.chat.completions.create(
                            model="accounts/fireworks/models/llama-v3p2-11b-vision-instruct",
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt_content
                                }
                            ],
                            max_tokens=600
                        )
                        raw_description = vision_response.choices[0].message.content
                    
                    st.success("✅ Frame analysis completed!")
                    
                    with st.expander("🔍 View Raw Description from Vision Model"):
                        st.write(raw_description)

                    with st.spinner("✍️ Step 2: Llama 3.3 is generating structured captions..."):
                        # Step 2: Text Model for Multi-tone Structured JSON
                        system_prompt = (
                            "You are a professional social media manager and copywriter. Your goal is to write captions "
                            "based on video descriptions. You always respond with a valid JSON object matching the exact schema requested."
                        )
                        user_prompt = f"""
                        Based on the following description of a video sequence:
                        
                        ---
                        {raw_description}
                        ---
                        
                        Generate four distinct video captions in these exact tones:
                        1. "Formal": Professional, corporate, clean, and informative. Great for LinkedIn.
                        2. "Sarcastic": Dry, humorous, slightly cynical, mocking the situation. Great for Reddit/Twitter.
                        3. "Humorous Tech": A joke/reference catered to developers, computer scientists, or IT workers using concepts like code, bugs, stackoverflow, compiler errors, APIs, or AI.
                        4. "Everyday Humor": Relatable, lighthearted, observational situational comedy. Great for TikTok or Instagram.
                        
                        You MUST return a JSON object with EXACTLY the following structure:
                        {{
                            "Formal": "Your formal caption here.",
                            "Sarcastic": "Your sarcastic caption here.",
                            "Humorous Tech": "Your tech humor caption here.",
                            "Everyday Humor": "Your everyday humor caption here."
                        }}
                        
                        Ensure you output ONLY the raw JSON object. Do not include markdown codeblocks or explanation.
                        """
                        
                        text_response = client.chat.completions.create(
                            model="accounts/fireworks/models/llama-v3-70b-instruct",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.75,
                            max_tokens=600
                        )
                        
                        raw_json_str = text_response.choices[0].message.content
                        
                        # Clean up Markdown block wrappers if the model generated them despite instructions
                        cleaned_json_str = raw_json_str.strip()
                        if cleaned_json_str.startswith("```json"):
                            cleaned_json_str = cleaned_json_str[7:]
                        elif cleaned_json_str.startswith("```"):
                            cleaned_json_str = cleaned_json_str[3:]
                        if cleaned_json_str.endswith("```"):
                            cleaned_json_str = cleaned_json_str[:-3]
                        cleaned_json_str = cleaned_json_str.strip()
                        
                        captions_dict = json.loads(cleaned_json_str)

                    st.success("✅ Multi-tone captions generated successfully!")

                    # Beautiful presentation
                    st.markdown("## 💬 Generated Captions")
                    
                    tab_formal, tab_sarcastic, tab_tech, tab_everyday = st.tabs([
                        "👔 Formal", 
                        "😏 Sarcastic", 
                        "💻 Humorous Tech", 
                        "😂 Everyday Humor"
                    ])
                    
                    with tab_formal:
                        st.markdown(f"""
                            <div class="caption-box caption-box-formal">
                                <div class="caption-title">👔 Formal Caption</div>
                                <div class="caption-text">{captions_dict.get('Formal', 'N/A')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with tab_sarcastic:
                        st.markdown(f"""
                            <div class="caption-box caption-box-sarcastic">
                                <div class="caption-title">😏 Sarcastic Caption</div>
                                <div class="caption-text">{captions_dict.get('Sarcastic', 'N/A')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with tab_tech:
                        st.markdown(f"""
                            <div class="caption-box caption-box-tech">
                                <div class="caption-title">💻 Humorous Tech Caption</div>
                                <div class="caption-text">{captions_dict.get('Humorous Tech', 'N/A')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with tab_everyday:
                        st.markdown(f"""
                            <div class="caption-box caption-box-everyday">
                                <div class="caption-title">😂 Everyday Humor Caption</div>
                                <div class="caption-text">{captions_dict.get('Everyday Humor', 'N/A')}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Show raw JSON
                    st.markdown("### 🛠️ Raw Output Data")
                    st.json(captions_dict)

                except Exception as e:
                    st.error(f"Error during API execution: {str(e)}")
                    st.info("Check that your API key is correct and you have access to the Fireworks models.")

            # Clean up temp file
            os.remove(temp_filepath)
    else:
        st.error("Error reading video. Please ensure it is a valid MP4 video.")

# Footer
st.markdown("""
    <div class="footer-text">
        Built with Streamlit • Powered by Fireworks AI Llama Models • OpenCV for Frame Processing
    </div>
""", unsafe_allow_html=True)
