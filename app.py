import os
import time
import streamlit as st

# Configure the Streamlit page layout
st.set_page_config(
    page_title="LectureMind AI – Study Workspace",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Helper function to inject custom CSS
def load_css(css_path):
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #FAFAF8; }</style>", unsafe_allow_html=True)

# Load the premium CSS styles
load_css("assets/style.css")

# Inject premium ambient background blobs for modern SaaS feel
st.markdown("""
    <div class="bg-blob bg-blob-purple"></div>
    <div class="bg-blob bg-blob-pink"></div>
""", unsafe_allow_html=True)

# --- MOCK DATA DEFINITIONS ---
MOCK_SHORT_SUMMARY = """
LectureMind AI has successfully compiled and synthesized your study materials on **Gradient Descent & Neural Network Optimization**. 
The PDF text provides formal mathematical backpropagation frameworks, while the YouTube lecture covers structural visualizations of 3D loss functions. 
Together, they establish a complete, intuitive understanding of parameter training via partial derivatives, showing how step size adjustments and SGD optimization avoid saddle points.
"""

MOCK_DETAILED_SUMMARY_HTML = """
<p><strong>1. Mathematical Foundation (PDF Guide)</strong><br/>
The objective is to minimize a loss function $J(\\theta)$ parameterized by model weights $\\theta \\in \\mathbb{R}^d$. The gradient vector is denoted as:</p>
<p>$$\\nabla_\\theta J(\\theta) = \\left[ \\frac{\\partial J}{\\partial \\theta_1}, \\dots, \\frac{\\partial J}{\\partial \\theta_d} \\right]^T$$</p>
<p>Weight updates are applied in the opposite direction of steepest slope: $\\theta = \\theta - \\alpha \\nabla J(\\theta)$ where $\\alpha$ is the positive scalar learning rate.</p>
<p><strong>2. Geometric Valley (YouTube Visuals)</strong><br/>
The video visualizes a 3D hilly loss landscape where parameter weight values converge down valleys. It highlights that in high-dimensional weights face saddle points—slopes of zero gradient that aren't minima—requiring adaptive velocity momentum steps to escape.</p>
<p><strong>3. Stochastic Batch Approximations</strong><br/>
Instead of computing true slow dataset gradients, SGD picks single randomized values causing jumpy paths that easily hop over saddle trap barriers. Mini-batching aggregates $B$ values, optimizing GPU hardware acceleration and backpropagation speed.</p>
"""

MOCK_KEY_CONCEPTS_HTML = """
<ul style="margin: 0; padding-left: 1.2rem;">
    <li><strong>Gradient (∇):</strong> The multi-dimensional slope vector representing the steepest ascending path. Subtracting it from weights descends the loss valley.</li>
    <li><strong>Learning Rate (α):</strong> The step size hyperparameter. Over-calibration leads to divergence (overshooting); under-calibration slows learning excessively.</li>
    <li><strong>Saddle Point:</strong> Flat parameter zones with zero gradients. Modern neural models trap vanilla gradients in these flat valleys.</li>
    <li><strong>Adam Optimizer:</strong> An adaptive optimizer tracking running momentum gradients to dynamically scale weights per parameter step.</li>
</ul>
"""

MOCK_IMPORTANT_TOPICS_HTML = """
<ol style="margin: 0; padding-left: 1.2rem;">
    <li><strong>Learning Rate Calibration & Decay Schedulers:</strong> Managing parameters step rates using cosine decay and step-decay models to stabilize convergence in late training epochs.</li>
    <li><strong>Saddle Point Escapes in High-Dimensional Landscapes:</strong> Why vanishing gradients occur in neural backprop, and how momentum forces parameters out of zero-gradient valleys.</li>
    <li><strong>Batch Processing Resource Tradeoffs:</strong> SGD high variance versus Mini-batch vector parallel acceleration on GPU hardware architectures.</li>
</ol>
"""

MOCK_QA_RESPONSES = {
    "gradient": "**Gradient Descent** is an iterative optimization algorithm used to find the minimum of a cost function in machine learning. Think of it like walking down a foggy mountain: at each step, you feel the slope of the ground beneath your feet and take a step in the direction that goes furthest down.\n\n* **Mathematical Form (PDF):** $\\theta = \\theta - \\alpha \\nabla J(\\theta)$\n* **Visual Aspect (YouTube):** A ball rolling down a 3D valley, constantly seeking the absolute lowest altitude.\n\n*Sources attributed: [PDF Page 2] & [YouTube Video @ 04:12]*",
    
    "both": "Both the **PDF notes** and the **YouTube lecture** cover the fundamental mechanics of parameters updates and the impact of the **learning rate**.\n\nHowever, they differ in pedagogical style:\n1. **The PDF Study Guide** is highly analytical, featuring calculus proofs, matrix derivations of backpropagation, and convergence rate tables.\n2. **The YouTube Video** specializes in high-quality 3D animations of weight landscapes, helping build visual intuition on how learning rates cause oscillations and how momentum pushes parameters past flat plateaus.\n\n*Sources attributed: [Combined Analysis]*",
    
    "quiz": "You can find all revision questions at the bottom of the page in the **Interactive Revision Quiz** section. I have generated 3 highly customized multiple-choice questions matching both the PDF and YouTube lecture content! Let me know if you would like me to generate a new set of questions here directly.",
    
    "default": "Based on your uploaded study materials (PDF pages and YouTube transcripts):\n\n**Gradient Descent optimization** is the core backbone of neural network training. To optimize parameters successfully, practitioners must choose a correct learning rate, manage mini-batch sizes (typically 64 or 128 for efficient GPU loading), and select a robust optimizer like Adam or SGD with momentum to safely bypass flat saddle regions.\n\n*Sources attributed: [deep_learning_optimization_notes.pdf] & [YouTube Lecture]*"
}

# --- SESSION STATE INITIALIZATION ---
if "processed" not in st.session_state:
    st.session_state.processed = False

if "chat_history" not in st.session_state:
    # Initialize with default welcome message
    st.session_state.chat_history = [
        {"role": "ai", "content": "Hello! I am LectureMind AI. Upload your PDFs and enter a YouTube lecture link above, and I will create a shared knowledge base to help you summarize, ask questions, and test your knowledge!"}
    ]

# ==========================================
# 1. APPLICATION HEADER
# ==========================================
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("""
        <div class="top-nav" style="margin-bottom: 0px !important;">
            <div class="nav-brand">🎓 LectureMind AI</div>
            <div class="nav-status">🟢 Engine: Gemini 1.5 Flash Active</div>
        </div>
    """, unsafe_allow_html=True)
with header_col2:
    if st.session_state.processed:
        st.markdown('<div style="height: 5px;"></div>', unsafe_allow_html=True)
        reset_btn = st.button("🔄 Reset Workspace", key="reset_workspace_btn")
        if reset_btn:
            st.session_state.processed = False
            st.session_state.chat_history = [
                {"role": "ai", "content": "Hello! I am LectureMind AI. Upload your PDFs and enter a YouTube lecture link above, and I will create a shared knowledge base to help you summarize, ask questions, and test your knowledge!"}
            ]
            st.rerun()

# Space separator
st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

# ==========================================
# 2. COMPACT HERO SECTION (ALWAYS VISIBLE)
# ==========================================
st.markdown("""
    <div class="landing-hero-card">
        <div class="landing-title">Learn Smarter with AI</div>
        <div class="landing-desc">
            Upload PDFs and YouTube lectures, generate summaries, ask questions, and test your understanding with AI.
        </div>
        <div class="pill-container">
            <span class="feature-pill"><span class="pill-check">✓</span> PDF Analysis</span>
            <span class="feature-pill"><span class="pill-check">✓</span> YouTube Lectures</span>
            <span class="feature-pill"><span class="pill-check">✓</span> AI Summaries</span>
            <span class="feature-pill"><span class="pill-check">✓</span> Context-Aware Answers</span>
            <span class="feature-pill"><span class="pill-check">✓</span> Quiz Generation</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. UPLOAD RESOURCES CARD (ALWAYS VISIBLE)
# ==========================================
with st.container(border=True):
    st.markdown('<div class="upload-flag"></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="card-title" style="margin-top: 0px; margin-bottom: 0.75rem;">
            <span class="card-icon">📥</span> Upload Learning Resources
        </div>
    """, unsafe_allow_html=True)
    
    # YouTube URL field
    st.markdown("""
        <div style="font-weight: 750; font-size: 0.95rem; color: #1F2937; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 4px;">
            <span>🎥</span> YouTube Lecture URL
        </div>
    """, unsafe_allow_html=True)
    yt_url = st.text_input(
        "YouTube Video URL:", 
        placeholder="Paste YouTube lecture or video link here (e.g., https://youtube.com/watch?v=...)",
        key="yt_url_input",
        label_visibility="collapsed"
    )
    
    # OR Divider with spacing
    st.markdown('<div class="divider-text" style="margin: 1.25rem auto; font-size: 0.82rem; letter-spacing: 0.05em;">— OR —</div>', unsafe_allow_html=True)
    
    # PDF Upload area
    st.markdown("""
        <div style="font-weight: 750; font-size: 0.95rem; color: #1F2937; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 4px;">
            <span>📄</span> Upload PDF Notes
        </div>
    """, unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload PDF Files:", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="pdf_uploader",
        label_visibility="collapsed"
    )
        
    # Large Process Button
    st.markdown('<div style="height: 5px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="center-button">', unsafe_allow_html=True)
    process_btn = st.button("🚀 Process Study Content", key="process_study_content_btn")
    st.markdown('</div>', unsafe_allow_html=True)

# Simulated processing pipeline
if process_btn:
    if not yt_url and not uploaded_files:
        st.error("Please supply at least a YouTube URL or upload a PDF to proceed!")
    else:
        with st.status("🧠 Compiling Lecture Study Hub (Simulated)...", expanded=True) as status:
            if yt_url:
                st.write("🔗 Connecting to YouTube caption systems...")
                time.sleep(0.7)
                st.write("🎙️ Processing audio stream fallback transcribing...")
                time.sleep(1.0)
            if uploaded_files:
                st.write(f"📄 Parsing document text pages with pdfplumber...")
                time.sleep(0.7)
            
            st.write("✂️ Splitting document text into contextual overlapping chunks...")
            time.sleep(0.6)
            st.write("🧬 Generating semantic embeddings and compiling local FAISS database...")
            time.sleep(0.7)
            status.update(label="Study Workspace compiled successfully!", state="complete", expanded=False)
        
        st.session_state.processed = True
 # 4. ACTIVE RESOURCES DRAWER (BELOW UPLOAD CARD)
# ==========================================
yt_val = st.session_state.get("yt_url_input", "").strip()
pdf_vals = st.session_state.get("pdf_uploader", [])

if yt_val or pdf_vals:
    badges_html = """
    <div class="resource-pill-drawer">
        <div style="font-weight: 800; font-size: 0.82rem; color: #1F2937; margin-right: 8px; display: inline-flex; align-items: center; gap: 4px;">
            <span>📁</span> Compiled Resources:
        </div>
    """
    if yt_val:
        badges_html += f'<span class="resource-badge">🎥 YouTube: {yt_val}</span>'
    for pdf in pdf_vals:
        badges_html += f'<span class="resource-badge">📄 PDF: {pdf.name}</span>'
    badges_html += '</div>'
    st.markdown(badges_html, unsafe_allow_html=True)

# Space separator
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# ==========================================
# 5. SECTION 1: SUMMARY WORKSPACE (PERSISTENT)
# ==========================================
st.markdown("""
    <div class="workflow-section-title">
        <span>📝</span> Summary Workspace
    </div>
    <div class="workflow-section-desc">
        Generate AI-powered summaries from PDFs and YouTube lectures.
    </div>
""", unsafe_allow_html=True)

if not st.session_state.processed:
    st.markdown("""
        <div class="disabled-placeholder-card">
            <div class="placeholder-icon">🔒</div>
            <div class="placeholder-title">Waiting for content...</div>
            <div class="placeholder-text">Upload resources and click "Process Study Content" to generate summaries.</div>
        </div>
    """, unsafe_allow_html=True)
else:
    grid_col1, grid_col2 = st.columns(2)
    
    with grid_col1:
        # Card 1: Short Summary
        st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(229, 231, 235, 0.8); border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01); overflow: hidden; margin-bottom: 0.75rem;">
                <div class="card-header-colored card-header-orange">
                    <span>📋</span> Short Summary
                </div>
                <div style="padding: 1rem;">
                    <div class="scrollable-card-body">
                        {MOCK_SHORT_SUMMARY}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Card 3: Key Concepts
        st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(229, 231, 235, 0.8); border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01); overflow: hidden; margin-bottom: 0.75rem;">
                <div class="card-header-colored card-header-pink">
                    <span>💡</span> Key Concepts
                </div>
                <div style="padding: 1rem;">
                    <div class="scrollable-card-body">
                        {MOCK_KEY_CONCEPTS_HTML}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with grid_col2:
        # Card 2: Detailed Summary
        st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(229, 231, 235, 0.8); border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01); overflow: hidden; margin-bottom: 0.75rem;">
                <div class="card-header-colored card-header-purple">
                    <span>📖</span> Detailed Summary
                </div>
                <div style="padding: 1rem;">
                    <div class="scrollable-card-body">
                        {MOCK_DETAILED_SUMMARY_HTML}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Card 4: Important Topics
        st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid rgba(229, 231, 235, 0.8); border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01); overflow: hidden; margin-bottom: 0.75rem;">
                <div class="card-header-colored card-header-teal">
                    <span>📌</span> Important Topics
                </div>
                <div style="padding: 1rem;">
                    <div class="scrollable-card-body">
                        {MOCK_IMPORTANT_TOPICS_HTML}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Space separator
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# ==========================================
# 6. SECTION 2: STUDY CHAT (PERSISTENT)
# ==========================================
st.markdown("""
    <div class="workflow-section-title">
        <span>💬</span> Study Chat
    </div>
    <div class="workflow-section-desc">
        Ask questions about your uploaded resources.
    </div>
""", unsafe_allow_html=True)

if not st.session_state.processed:
    st.markdown("""
        <div class="disabled-placeholder-card">
            <div class="placeholder-icon">💬</div>
            <div class="placeholder-title">Waiting for content...</div>
            <div class="placeholder-text">Process study materials to start chatting with your AI study assistant.</div>
        </div>
    """, unsafe_allow_html=True)
else:
    chat_box = st.container()
    
    # Process chatbot query
    chat_col1, chat_col2 = st.columns([6, 1])
    with chat_col1:
        chat_input = st.text_input(
            "Ask a question about your uploaded content...", 
            placeholder="Ask a question about your uploaded content...",
            key="qa_user_input",
            label_visibility="collapsed"
        )
    with chat_col2:
        send_btn = st.button("✈️ Send", key="chat_send_button")
        
    if chat_input and (send_btn or st.session_state.get("qa_user_input")):
        user_query = chat_input.lower().strip()
        reply = MOCK_QA_RESPONSES["default"]
        for key in MOCK_QA_RESPONSES:
            if key in user_query:
                reply = MOCK_QA_RESPONSES[key]
                break
        
        # Append to session chat history
        st.session_state.chat_history.append({"role": "user", "content": chat_input})
        st.session_state.chat_history.append({"role": "ai", "content": reply})
        st.rerun()
        
    # Render chat bubbles inside a single custom HTML string to avoid Streamlit container quirks
    with chat_box:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            bubble_type = "chat-bubble-user" if msg['role'] == "user" else "chat-bubble-ai"
            speaker_label = "👤 You" if msg['role'] == "user" else "🤖 LectureMind AI"
            chat_html += f"""
                <div class="chat-bubble {bubble_type}">
                    <div style="font-size: 0.75rem; margin-bottom: 0.25rem; opacity: 0.8; font-weight: 750;">{speaker_label}</div>
                    <div>{msg['content']}</div>
                </div>
            """
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

# Space separator
st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# ==========================================
# 7. SECTION 3: QUIZ GENERATOR (PERSISTENT)
# ==========================================
st.markdown("""
    <div class="workflow-section-title">
        <span>✏️</span> Quiz Generator
    </div>
    <div class="workflow-section-desc">
        Generate revision questions and MCQs.
    </div>
""", unsafe_allow_html=True)

if not st.session_state.processed:
    st.markdown("""
        <div class="disabled-placeholder-card">
            <div class="placeholder-icon">✏️</div>
            <div class="placeholder-title">Waiting for content...</div>
            <div class="placeholder-text">Process resources to generate quizzes.</div>
        </div>
    """, unsafe_allow_html=True)
else:
    quiz_col1, quiz_col2, quiz_col3 = st.columns(3)
    
    # -- Category 1: MCQs Card --
    with quiz_col1:
        st.markdown('<div class="quiz-category-card quiz-card-purple">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">📝 MCQs</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="quiz-question-box" style="margin-top: 0px !important; padding: 0.75rem !important;">', unsafe_allow_html=True)
        st.markdown("**Q1:** In cost function optimization, what does the gradient vector $\\nabla J(\\theta)$ mathematically represent?")
        st.markdown('</div>', unsafe_allow_html=True)
        
        q1_ans = st.radio(
            "Question 1 Answers:",
            ["A) Steepest descent direction.", "B) Steepest ascent direction.", "C) Learning scalar value."],
            key="mcq_radio",
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        submit_mcq = st.button("🏁 Submit Answers", key="mcq_submit_btn")
        
        if submit_mcq:
            if q1_ans.startswith("B"):
                st.success("✅ Correct! Gradient points in the steepest *ascent* direction.")
            else:
                st.error("❌ Incorrect. Correct answer: B (Steepest ascent).")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # -- Category 2: Interview Prep Card --
    with quiz_col2:
        st.markdown('<div class="quiz-category-card quiz-card-orange">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">💼 Interview Questions</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 0.5rem;">Click to expand answers and check understanding:</p>', unsafe_allow_html=True)
        
        with st.expander("Q1: Explain how backpropagation uses gradients"):
            st.write("Backpropagation applies the calculus chain rule to calculate loss partial derivatives per weight layer, optimizing backwards through the neural network nodes.")
            
        with st.expander("Q2: Why is SGD noisy compared to batch GD?"):
            st.write("SGD calculates gradients on single random samples rather than compiling the whole dataset. This variance causes gradients to jump, assisting escapes from flat saddle boundaries.")
            
        with st.expander("Q3: What makes the Adam optimizer robust?"):
            st.write("Adam combines momentum dynamics and RMSProp parameters updates, scaling learning steps adaptively for individual neural nodes.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # -- Category 3: Revision Card --
    with quiz_col3:
        st.markdown('<div class="quiz-category-card quiz-card-teal">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">📌 Quick Revision</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 0.75rem;">Deepen your comprehension with quick concepts check-checks:</p>', unsafe_allow_html=True)
        
        st.markdown("""
            <div style="background-color: #FAFAF8; border-radius: 8px; padding: 0.75rem; border: 1px solid #E5E7EB; margin-bottom: 0.5rem;">
                <strong style="color: #14B8A6; font-size: 0.82rem; text-transform: uppercase;">1. Saddle Point Bottleneck</strong>
                <p style="margin: 0; font-size: 0.82rem; color: #374151; line-height: 1.3;">In massive systems, vanishing parameter updates arise due to flat saddle valleys rather than local minima.</p>
            </div>
            <div style="background-color: #FAFAF8; border-radius: 8px; padding: 0.75rem; border: 1px solid #E5E7EB; margin-bottom: 0.5rem;">
                <strong style="color: #6366F1; font-size: 0.82rem; text-transform: uppercase;">2. Optimal Learning Rate</strong>
                <p style="margin: 0; font-size: 0.82rem; color: #374151; line-height: 1.3;">Step parameters scale must align with cosine annealing decay steps to stabilize validation cost curves.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Footer (Compact)
st.markdown("""
    <hr style="border: 0; border-top: 1px solid rgba(229, 231, 235, 0.6); margin-top: 2rem; margin-bottom: 0.5rem;" />
    <div style="text-align: center; color: #9CA3AF; font-size: 0.85rem; margin-bottom: 0.5rem;">
        🎓 <b>LectureMind AI</b> — Engineered with Streamlit, LangChain, FAISS, and Gemini 1.5 Flash.
    </div>
""", unsafe_allow_html=True)
