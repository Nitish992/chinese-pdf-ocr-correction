import streamlit as st
from pdf_repair_service import PDFRepairService
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Set page configuration for full-screen width
    st.set_page_config(page_title="Chinese PDF OCR and Error Correction PoC", layout="wide")
    st.title("Chinese PDF OCR and Error Correction PoC")
    st.write("Upload a Chinese PDF, and this app will extract text using OCR, correct errors with DeepSeek, and display the results for comparison.")

    # Initialize the PDF repair service
    try:
        repair_service = PDFRepairService()
        logger.info("PDFRepairService initialized successfully.")
    except Exception as e:
        st.error(f"Failed to initialize the service: {e}")
        return

    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdf_uploader")

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("Processing the PDF...")

        # Create a progress bar and status container
        progress_bar = st.progress(0)
        status_container = st.empty()

        try:
            # Step 1: Extract text using OCR
            status_container.write("Step 1: Extracting text from PDF using OCR...")
            extracted_text = repair_service.extract_text_from_pdf("temp.pdf")
            original_length = len(extracted_text)
            logger.debug(f"Extracted text length: {original_length}")
            progress_bar.progress(20)
            time.sleep(0.5)  # Simulate processing time

            # Step 2: Split, correct with chains, and reassemble text
            status_container.write("Step 2: Correcting OCR errors with DeepSeek chains and summarizing context...")
            corrected_chunks = repair_service.split_and_correct_text_with_runnables(extracted_text)
            corrected_text = repair_service.reassemble_text(corrected_chunks, original_length)
            logger.debug(f"Number of corrected chunks: {len(corrected_chunks)}")
            logger.debug(f"Final corrected text length: {len(corrected_text)}")
            progress_bar.progress(90)
            time.sleep(0.5)  # Simulate processing time

            # Step 3: Finalize and clean up
            status_container.write("Step 3: Finalizing and cleaning up...")
            progress_bar.progress(100)
            time.sleep(0.5)  # Simulate processing time

            st.success("PDF processed successfully!")
            st.subheader("Text Comparison (Extracted vs. Corrected)")

            # Display extracted and corrected text side by side with full width
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Extracted Text (OCR Output)")
                st.text_area("OCR Extracted Text", extracted_text, height=300, disabled=True)

            with col2:
                st.subheader("Corrected Text (DeepSeek Output)")
                st.text_area("Corrected Text", corrected_text, height=300, disabled=True)

        except Exception as e:
            st.error(f"Error processing the PDF: {e}")
            logger.error(f"Error processing PDF: {e}")
        
        # Clean up temporary file
        import os
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")
            logger.info("Temporary PDF file removed.")

        # Clear progress and status after processing
        progress_bar.empty()
        status_container.empty()

if __name__ == "__main__":
    main()