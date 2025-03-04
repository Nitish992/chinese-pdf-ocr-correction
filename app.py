import streamlit as st
from pdf_repair_service import PDFRepairService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Setting the layout to wide
    st.set_page_config(page_title="Job Search App", layout="wide")
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
    uploaded_file = st.file_uploader("Upload a Chinese PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("Processing the PDF...")
        
        # Process the PDF
        try:
            # Extract text using OCR
            extracted_text = repair_service.extract_text_from_pdf("temp.pdf")
            original_length = len(extracted_text)

            # Split, correct, and reassemble text
            corrected_chunks = repair_service.split_and_correct_text(extracted_text)
            corrected_text = repair_service.reassemble_text(corrected_chunks, original_length)

            st.success("PDF processed successfully!")
            st.subheader("Text Comparison (Extracted vs. Corrected)")

            # Display extracted and corrected text side by side
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

if __name__ == "__main__":
    main()