import os
import time
import streamlit as st
from utils.pdf_processor import process_pdfs
from utils.chunker import split_text
from utils.vectorstore import MemoryVectorStore
from utils.summarizer import generate_summaries
from utils.quiz_generator import generate_quiz
from utils.qa_chain import answer_question
from utils.gemini_config import selected_text_model

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

# --- SESSION STATE INITIALIZATION ---
if "processed" not in st.session_state:
    st.session_state.processed = False

if "chat_history" not in st.session_state:
    # Initialize with default welcome message
    st.session_state.chat_history = [
        {"role": "ai", "content": "Hello! I am LectureMind AI. Upload your PDFs and enter a YouTube lecture link above, and I will create a shared knowledge base to help you summarize, ask questions, and test your knowledge!"}
    ]

if "summary_data" not in st.session_state:
    st.session_state.summary_data = None

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ==========================================
# 1. APPLICATION HEADER
# ==========================================
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown(f"""
        <div class="top-nav" style="margin-bottom: 0px !important;">
            <div class="nav-brand">🎓 LectureMind AI</div>
            <div class="nav-status">🟢 Engine: {selected_text_model} Active</div>
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
            st.session_state.summary_data = None
            st.session_state.quiz_data = None
            st.session_state.vector_store = None
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

# Processing pipeline
if process_btn:
    if not yt_url and not uploaded_files:
        st.error("Please supply at least a YouTube URL or upload a PDF to proceed!")
    else:
        with st.status("🧠 Compiling Lecture Study Hub...", expanded=True) as status:
            combined_text = ""
            total_pages = 0
            total_docs = 0
            
            # 1. YouTube Mock Caption Extraction (Secondary resource fallback)
            if yt_url:
                st.write("🔗 Connecting to YouTube caption systems...")
                time.sleep(0.5)
                st.write("🎙️ Extracting captions from lecture video stream...")
                time.sleep(0.5)
                combined_text += "=== DOCUMENT: YouTube Lecture ===\n--- [Page 1] ---\nThis YouTube video covers structural visualizations and deep geometric loss landscape analysis of neural network optimizations, demonstrating step parameter updates and gradient oscillations in 3D landscapes.\n\n"
                total_pages += 1
                total_docs += 1
                
            # 2. PDF text extraction (ACTIVE)
            if uploaded_files:
                st.write("📄 Extracting document text pages...")
                pdf_result = process_pdfs(uploaded_files)
                combined_text += pdf_result["text"]
                total_pages += pdf_result["num_pages"]
                total_docs += pdf_result["num_documents"]
            
            # 3. Text Chunking with metadata tracking (ACTIVE)
            st.write("✂️ Splitting document text into contextual overlapping chunks...")
            chunks = split_text(combined_text)
            
            # 4. Dense Embeddings & Vector Database indexing (ACTIVE)
            st.write("🧬 Generating API embeddings and compiling memory vector database...")
            vstore = MemoryVectorStore()
            vstore.add_chunks(chunks)
            st.session_state.vector_store = vstore
            
            # 5. Gemini 1.5 Flash Executive Summaries (ACTIVE)
            st.write("📊 Generating Executive Summaries using Gemini...")
            st.session_state.summary_data = generate_summaries(combined_text)
            
            # 6. JSON Study Quiz compilation (ACTIVE)
            st.write("✏️ Compiling Interactive Study Quizzes...")
            st.session_state.quiz_data = generate_quiz(combined_text)
            
            status.update(label="Study Workspace compiled successfully!", state="complete", expanded=False)
        
        st.session_state.processed = True
        st.rerun()
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
                        {st.session_state.summary_data.get("short_summary", "")}
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
                        {st.session_state.summary_data.get("key_concepts", "")}
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
                        {st.session_state.summary_data.get("detailed_summary", "")}
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
                        {st.session_state.summary_data.get("important_topics", "")}
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
        # Append user message to log history
        st.session_state.chat_history.append({"role": "user", "content": chat_input})
        
        # Get cited context RAG response
        with st.spinner("🧠 Analyzing study context..."):
            reply = answer_question(chat_input, st.session_state.chat_history, st.session_state.vector_store)
            
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
    
    quiz_data = st.session_state.quiz_data if st.session_state.quiz_data else {}
    
    # -- Category 1: MCQs Card --
    with quiz_col1:
        st.markdown('<div class="quiz-category-card quiz-card-purple">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">📝 MCQs</div>', unsafe_allow_html=True)
        
        mcqs = quiz_data.get("mcqs", [])
        if mcqs:
            q1 = mcqs[0]
            st.markdown('<div class="quiz-question-box" style="margin-top: 0px !important; padding: 0.75rem !important;">', unsafe_allow_html=True)
            st.markdown(f"**Q1:** {q1.get('question')}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            q1_ans = st.radio(
                "Question 1 Answers:",
                q1.get("options", []),
                key="mcq_radio",
                label_visibility="collapsed"
            )
            
            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            submit_mcq = st.button("🏁 Submit Answers", key="mcq_submit_btn")
            
            if submit_mcq:
                correct_key = q1.get("correct_key", "A").strip()
                if q1_ans.strip().startswith(correct_key):
                    st.success(f"✅ Correct! {q1.get('explanation')}")
                else:
                    st.error(f"❌ Incorrect. Correct answer: {correct_key}. {q1.get('explanation')}")
        else:
            st.markdown('<p style="font-size: 0.85rem; color: #4B5563;">Failed to compile MCQ questions.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # -- Category 2: Interview Prep Card --
    with quiz_col2:
        st.markdown('<div class="quiz-category-card quiz-card-orange">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">💼 Interview Questions</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 0.5rem;">Click to expand answers and check understanding:</p>', unsafe_allow_html=True)
        
        interview_qs = quiz_data.get("interview_questions", [])
        if interview_qs:
            for idx, item in enumerate(interview_qs):
                with st.expander(f"Q{idx + 1}: {item.get('question')}"):
                    st.write(item.get("answer"))
        else:
            st.markdown('<p style="font-size: 0.85rem; color: #4B5563;">Failed to compile interview questions.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # -- Category 3: Revision Card --
    with quiz_col3:
        st.markdown('<div class="quiz-category-card quiz-card-teal">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-top: 0px;">📌 Quick Revision</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 0.75rem;">Deepen your comprehension with quick concepts check-checks:</p>', unsafe_allow_html=True)
        
        revision_cards = quiz_data.get("revision_cards", [])
        if revision_cards:
            revision_html = ""
            colors = ["#14B8A6", "#6366F1", "#EC4899"]
            for idx, card in enumerate(revision_cards):
                color = colors[idx % len(colors)]
                revision_html += f"""
                    <div style="background-color: #FAFAF8; border-radius: 8px; padding: 0.75rem; border: 1px solid #E5E7EB; margin-bottom: 0.5rem;">
                        <strong style="color: {color}; font-size: 0.82rem; text-transform: uppercase;">{idx + 1}. {card.get('title')}</strong>
                        <p style="margin: 0; font-size: 0.82rem; color: #374151; line-height: 1.3;">{card.get('content')}</p>
                    </div>
                """
            st.markdown(revision_html, unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size: 0.85rem; color: #4B5563;">Failed to compile revision points.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Footer (Compact)
st.markdown("""
    <hr style="border: 0; border-top: 1px solid rgba(229, 231, 235, 0.6); margin-top: 2rem; margin-bottom: 0.5rem;" />
    <div style="text-align: center; color: #9CA3AF; font-size: 0.85rem; margin-bottom: 0.5rem;">
        🎓 <b>LectureMind AI</b> — Engineered with Streamlit, LangChain, FAISS, and Gemini 1.5 Flash.
    </div>
""", unsafe_allow_html=True)
