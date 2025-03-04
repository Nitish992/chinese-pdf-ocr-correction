from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from os import getenv
from langchain_openai import ChatOpenAI
from pdf2image import convert_from_path
import pytesseract
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFRepairService:
    """
    A service class to extract text from Chinese PDFs using OCR, correct OCR errors using DeepSeek,
    and reassemble the corrected text into a coherent document.
    """

    def __init__(self):
        """
        Initialize the PDFRepairService with OpenRouter API key and Tesseract configuration.
        """

        # Initialize DeepSeek model via LangChain
        try:
            self.llm = ChatOpenAI(
                openai_api_key=getenv("OPENROUTER_API_KEY"),
                openai_api_base=getenv("OPENROUTER_BASE_URL"),
                model_name="deepseek/deepseek-r1:free",
              )
            logger.info("DeepSeek model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek model: {e}")
            raise

        # Configure Tesseract for Linux
        self.tesseract_lang = 'chi_sim'  # Use 'chi_tra' for traditional Chinese if needed

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF using Tesseract OCR.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Extracted text from the PDF.
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            extracted_text = ""
            for image in images:
                text = pytesseract.image_to_string(image, lang=self.tesseract_lang)
                extracted_text += text + "\n"
            logger.info(f"Text extracted from {pdf_path} using OCR.")
            return extracted_text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def correct_text_with_deepseek(self, text_chunk):
        """
        Correct OCR errors in a text chunk using DeepSeek via LangChain.

        Args:
            text_chunk (str): Text chunk to correct.

        Returns:
            str: Corrected text.
        """
        try:
            prompt = (
               "You are given a text that has been extracted from a scanned PDF using OCR in Chinese. "
                "Your task is to remove any garbled text, correct typos, fill in any missing words, "
                "and restore coherence to the text. Please return only the corrected text, without any "
                "additional explanations, notes, or commentary. Ensure the corrected text prioritizes "
                "maintaining the original length as closely as possible, but make minor adjustments "
                "if necessary to ensure coherence and accuracy: {text_chunk}"
            ).format(text_chunk=text_chunk)
            
            response = self.llm.invoke(prompt)
            corrected_text = response.content if hasattr(response, 'content') else str(response)
            logger.info("Text chunk corrected successfully with DeepSeek.")
            return corrected_text
        except Exception as e:
            logger.error(f"Error correcting text with DeepSeek: {e}")
            raise

    def split_and_correct_text(self, text, chunk_size=2000, chunk_overlap=200):
        """
        Split text into chunks, correct each chunk using DeepSeek, and return corrected chunks.

        Args:
            text (str): Text to process.
            chunk_size (int): Size of each chunk in characters.
            chunk_overlap (int): Overlap between chunks in characters.

        Returns:
            list: List of corrected text chunks.
        """
        try:
            # Initialize text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_text(text)

            # Correct each chunk
            corrected_chunks = []
            for chunk in chunks:
                corrected_chunk = self.correct_text_with_deepseek(chunk)
                corrected_chunks.append(corrected_chunk)

            logger.info(f"Processed {len(chunks)} chunks with DeepSeek.")
            return corrected_chunks
        except Exception as e:
            logger.error(f"Error splitting and correcting text: {e}")
            raise

    def reassemble_text(self, corrected_chunks, original_text_length=None):
        """
        Reassemble corrected chunks into a coherent document, handling overlaps.

        Args:
            corrected_chunks (list): List of corrected text chunks.
            original_text_length (int, optional): Original text length for padding/truncation.

        Returns:
            str: Reassembled coherent text.
        """
        try:
            final_text = ""
            current_pos = 0
            
            for chunk in corrected_chunks:
                # Find the position to insert or overwrite
                if current_pos < len(final_text):
                    # Overlap: later chunk overwrites earlier content
                    final_text = final_text[:current_pos] + chunk + final_text[current_pos + len(chunk):]
                else:
                    # Append if no overlap
                    final_text += chunk
                current_pos += len(chunk) - 200  # Adjust for overlap (200 chars)

            # Optionally adjust length to match original if specified
            if original_text_length and len(final_text) != original_text_length:
                if len(final_text) > original_text_length:
                    final_text = final_text[:original_text_length]
                else:
                    final_text += " " * (original_text_length - len(final_text))

            logger.info("Text reassembled successfully.")
            return final_text
        except Exception as e:
            logger.error(f"Error reassembling text: {e}")
            raise

    def process_pdf(self, pdf_path):
        """
        Process a PDF: extract text with OCR, correct errors with DeepSeek, and reassemble.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Corrected and reassembled text.
        """
        try:
            # Extract text using OCR
            extracted_text = self.extract_text_from_pdf(pdf_path)
            original_length = len(extracted_text)

            # Split, correct, and reassemble text
            corrected_chunks = self.split_and_correct_text(extracted_text)
            final_text = self.reassemble_text(corrected_chunks, original_length)

            logger.info(f"PDF processed successfully: {pdf_path}")
            return final_text
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise

# Example usage
if __name__ == "__main__":

    pdf_path = "page2chinese.pdf"
    
    try:
        # Initialize the service
        service = PDFRepairService()
        
        # Process the PDF and get corrected text
        corrected_text = service.process_pdf(pdf_path)
        print("Corrected text:")
        print(corrected_text)
    except Exception as e:
        logger.error(f"Failed to process PDF: {e}")