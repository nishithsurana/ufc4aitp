import streamlit as st
import os
import tempfile
from markitdown import MarkItDown

# --- Configuration & UI Setup ---
st.set_page_config(
    page_title="Universal Document Reader",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Universal Document Reader")
st.markdown("""
**Convert your files to clean Text/Markdown instantly.**
*Supports: Word (.docx), Excel (.xlsx), PowerPoint (.pptx), PDF, and HTML.*
""")

# Initialize tabs
tab1, tab2 = st.tabs(["📤 Upload & Convert", "📊 File Size Comparison"])

# --- The "Engine" Setup ---
@st.cache_resource
def get_engine():
    return MarkItDown()

md_engine = get_engine()

# --- Helper Functions ---
def format_size(size_in_bytes):
    """Converts bytes to readable KB/MB string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

def process_file(uploaded_file):
    """
    Saves uploaded file to temp path, converts, and returns text + path cleanup.
    """
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name

        # Convert
        result = md_engine.convert(tmp_path)
        converted_text = result.text_content

        # Cleanup
        os.remove(tmp_path)
        
        return converted_text

    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

# --- Main App Logic ---

# Initialize session state for stats if not present
if 'file_stats' not in st.session_state:
    st.session_state['file_stats'] = []

with tab1:
    uploaded_files = st.file_uploader(
        "Drag and drop your files here", 
        accept_multiple_files=True,
        type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'htm']
    )

    if uploaded_files:
        st.markdown("---")
        
        # Clear old stats when new upload happens to avoid duplicates
        current_stats = []
        
        for uploaded_file in uploaded_files:
            with st.expander(f"Processing: {uploaded_file.name}", expanded=True):
                try:
                    with st.spinner("Converting..."):
                        text_content = process_file(uploaded_file)
                        
                        # --- Logic for File Size Stats ---
                        original_size = uploaded_file.size
                        # Estimate text size in bytes (UTF-8)
                        converted_size = len(text_content.encode('utf-8'))
                        
                        # Calculate reduction
                        if original_size > 0:
                            reduction = (1 - (converted_size / original_size)) * 100
                        else:
                            reduction = 0
                            
                        stat_entry = {
                            "File Name": uploaded_file.name,
                            "Original Size": format_size(original_size),
                            "Converted Size": format_size(converted_size),
                            "Reduction": f"{reduction:.1f}% smaller"
                        }
                        current_stats.append(stat_entry)

                    # --- Preview ---
                    st.subheader("Preview")
                    st.text_area(
                        label="Converted Text",
                        value=text_content,
                        height=300,
                        label_visibility="collapsed"
                    )

                    # --- Download Options ---
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    download_name = f"{base_name}_converted"
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="⬇️ Download Markdown (.md)",
                            data=text_content,
                            file_name=f"{download_name}.md",
                            mime="text/markdown"
                        )
                    
                    with col2:
                        st.download_button(
                            label="⬇️ Download Text (.txt)",
                            data=text_content,
                            file_name=f"{download_name}.txt",
                            mime="text/plain"
                        )
                        
                except Exception as e:
                    st.error(f"⚠️ Could not read {uploaded_file.name}. Please check the format.")
                    
        # Update session state with new stats
        st.session_state['file_stats'] = current_stats

# --- Tab 2: Comparison ---
with tab2:
    st.header("File Size Savings")
    
    if st.session_state['file_stats']:
        for stat in st.session_state['file_stats']:
            # Create a clean UI for each file
            st.markdown(f"### 📄 {stat['File Name']}")
            
            # Create columns for the metrics
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Original File Size", stat['Original Size'])
            
            with col_b:
                st.metric("Converted .txt Size", stat['Converted Size'])
                
            with col_c:
                st.metric("Efficiency", stat['Reduction'], delta_color="normal")
            
            st.divider()
    else:
        st.info("Upload and convert files in the first tab to see size comparisons here.")
