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

# --- The "Engine" Setup ---
# We instantiate MarkItDown. 
# Note: The prompt requested User-Agent/Timeouts for web requests. 
# While this specific app focuses on file uploads, MarkItDown can handle URLs.
# If extending to URLs, specific requests sessions would be passed here.
md_engine = MarkItDown()

# --- helper function: Process File ---
def process_file(uploaded_file):
    """
    Saves uploaded file to a temporary path, converts it using MarkItDown,
    and returns the text content. Handles cleanup automatically.
    """
    # Create a temporary file to save the upload so MarkItDown can read the path
    # We use delete=False so we can close it before reading, then manually remove it.
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name

        # Convert using the Engine
        result = md_engine.convert(tmp_path)
        converted_text = result.text_content

        # Clean up the temp file
        os.remove(tmp_path)
        
        return converted_text

    except Exception as e:
        # If temp file exists but crashed, try to clean up
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

# --- The Interface ---

# 1. Upload Area
uploaded_files = st.file_uploader(
    "Drag and drop your files here", 
    accept_multiple_files=True,
    type=['docx', 'xlsx', 'pptx', 'pdf', 'html', 'htm']
)

if uploaded_files:
    st.markdown("---")
    
    for uploaded_file in uploaded_files:
        with st.expander(f"Processing: {uploaded_file.name}", expanded=True):
            
            try:
                # Processing
                with st.spinner("Converting..."):
                    text_content = process_file(uploaded_file)

                # 2. Instant Preview
                st.subheader("Preview")
                st.text_area(
                    label="Converted Text",
                    value=text_content,
                    height=300,
                    label_visibility="collapsed"
                )

                # Prepare Filenames
                # e.g., Project_Notes.docx -> Project_Notes_converted
                base_name = os.path.splitext(uploaded_file.name)[0]
                download_name = f"{base_name}_converted"

                # 3. Download Options
                col1, col2 = st.columns(2)
                
                # Download as Markdown (.md)
                with col1:
                    st.download_button(
                        label="⬇️ Download Markdown (.md)",
                        data=text_content,
                        file_name=f"{download_name}.md",
                        mime="text/markdown"
                    )
                
                # Download as Text (.txt)
                with col2:
                    st.download_button(
                        label="⬇️ Download Text (.txt)",
                        data=text_content,
                        file_name=f"{download_name}.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                # 4. Resilience (Error Handling)
                # We log the specific error to console for debugging, but show polite msg to user
                print(f"Error processing {uploaded_file.name}: {e}")
                st.error(f"⚠️ Could not read {uploaded_file.name}. Please check the format.")
