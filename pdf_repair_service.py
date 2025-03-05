from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableSequence
from pdf2image import convert_from_path
import pytesseract
import logging
from dotenv import load_dotenv
import os
import subprocess

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFRepairService:
    """
    A service class to extract text from Chinese PDFs using OCR, correct OCR errors using DeepSeek
    with context-aware processing via LangChain runnables, and assemble the corrected text into a coherent document.
    """

    def __init__(self) -> None:
        """
        Initialize the PDFRepairService with OpenRouter API key and Tesseract configuration.
        """
        # Initialize DeepSeek model via LangChain (OpenRouter configuration)
        try:

            # self.llm = ChatDeepSeek(
            #     model="deepseek-chat",
            #     temperature=0,
            # )
            self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base='https://openrouter.ai/api/v1',
            model_name="deepseek/deepseek-r1:free",
            )
            logger.info("DeepSeek model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek model: {e}")
            raise

        # Configure Tesseract for Linux
        self.tesseract_lang = 'chi_sim'  # Use 'chi_tra' for traditional Chinese if needed

        # Check if Poppler is installed
        self._check_poppler_installation()

        # Initialize correction and summarization runnables
        self.correction_runnable = self._create_correction_runnable()
        self.summarization_runnable = self._create_summarization_runnable()

        # Initialize context history (summary)
        self.previous_summary = ""

    def _check_poppler_installation(self) -> None:
        """
        Check if Poppler is installed and accessible in PATH.

        Raises:
            RuntimeError: If Poppler is not installed or not in PATH.
        """
        try:
            subprocess.run(['pdftoppm', '-v'], capture_output=True, check=True)
            logger.info("Poppler is installed and accessible.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Poppler is not installed or not in PATH. Please install poppler-utils "
                "(e.g., `sudo apt install poppler-utils` on Ubuntu/Debian) and ensure it’s accessible."
            )

    def extract_text_from_pdf(self, pdf_path) -> str:
        """
        Extract raw text from a PDF using Tesseract OCR without any cleaning.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Raw extracted text from the PDF.
        """
        try:
            # Convert PDF to images with Poppler
            images = convert_from_path(pdf_path)
            extracted_text = ""

            for i, image in enumerate(images):
                # Perform OCR on each page
                page_text = pytesseract.image_to_string(image, lang=self.tesseract_lang)
                logger.debug(f"Raw OCR text for page {i + 1} length: {len(page_text)}")
                extracted_text += page_text + "\n"

            logger.info(f"Raw text extracted from {pdf_path} using OCR.")
            return extracted_text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _create_correction_runnable(self) -> RunnableSequence:
        """
        Create a LangChain runnable for correcting OCR errors with DeepSeek.

        Returns:
            Runnable: Correction runnable.
        """
        correction_prompt = ChatPromptTemplate.from_template(
            "You are given a section of text from a scanned Chinese PDF, extracted using OCR, "
            "with optional previous summary context to maintain coherence. This text may include "
            "extraneous elements like page numbers, headers, or footers. Your task is to remove "
            "any garbled text, correct typos, fill in any missing words, restore coherence to "
            "the text, and exclude non-content elements (e.g., page numbers, headers, footers). "
            "Please return only the corrected main content text, without any additional "
            "explanations, notes, or commentary. Ensure the corrected text prioritizes "
            "maintaining the original length as closely as possible, but make minor adjustments "
            "if necessary to ensure coherence and consistency with the context. Text: {text_chunk}, "
            "Context: {context}"
        )
        return correction_prompt | self.llm

    def _create_summarization_runnable(self) -> RunnableSequence:
        """
        Create a LangChain runnable for summarizing the history of corrected text.

        Returns:
            Runnable: Summarization runnable.
        """
        summarization_prompt = ChatPromptTemplate.from_template(
            "You are given a section of corrected text from a Chinese story, previously processed "
            "for OCR errors. Your task is to summarize this text into a concise 100-200 character "
            "summary that captures the key narrative elements (e.g., main characters, plot points, "
            "last sentence) for maintaining coherence in subsequent text. Please return only the "
            "summary, without any additional explanations, notes, or commentary. Text: {text}"
        )
        return summarization_prompt | self.llm

    def correct_text_with_runnables(self, text_chunk, context="") -> str:
        """
        Correct OCR errors in a text chunk using the correction runnable, with summarized context.

        Args:
            text_chunk (str): Text chunk to correct.
            context (str): Summarized previous context.

        Returns:
            str: Corrected text, with updated summary for the next chunk.
        """
        try:
            # Correct the chunk using the correction runnable
            correction_input = {"text_chunk": text_chunk, "context": context}
            correction_result = self.correction_runnable.invoke(correction_input)
            corrected_text = correction_result.content if hasattr(correction_result, 'content') else str(correction_result)
            logger.debug(f"Corrected chunk length: {len(corrected_text)}")

            # Summarize the corrected text for the next chunk's context
            summarization_input = {"text": corrected_text}
            summarization_result = self.summarization_runnable.invoke(summarization_input)
            new_summary = summarization_result.content if hasattr(summarization_result, 'content') else str(summarization_result)
            logger.debug(f"Summary length: {len(new_summary)}")

            # Update context (summary) for the next chunk, ensuring it’s 100-200 characters
            self.previous_summary = new_summary[:200] if len(new_summary) > 200 else new_summary
            logger.info("Text chunk corrected and summarized successfully with DeepSeek runnables.")
            return corrected_text
        except Exception as e:
            logger.error(f"Error correcting text with DeepSeek runnables: {e}")
            raise

    def split_and_correct_text_with_runnables(self, text, chunk_size=2000, chunk_overlap=200) -> list[str]:
        """
        Split text into chunks, correct each chunk using DeepSeek runnables with context awareness, and return corrected chunks.

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

            # Correct each chunk with summarized context
            corrected_chunks = []
            for i, chunk in enumerate(chunks):
                context = self.previous_summary if i > 0 else ""
                corrected_chunk = self.correct_text_with_runnables(chunk, context)
                corrected_chunks.append(corrected_chunk)

            logger.info(f"Processed {len(chunks)} chunks with DeepSeek using runnables and context awareness.")
            return corrected_chunks
        except Exception as e:
            logger.error(f"Error splitting and correcting text: {e}")
            raise

    def reassemble_text(self, corrected_chunks, original_text_length=None) -> str:
        """
        Reassemble corrected chunks into a coherent document, assuming overlaps were handled during correction.

        Args:
            corrected_chunks (list): List of corrected text chunks.
            original_text_length (int, optional): Original text length for padding/truncation.

        Returns:
            str: Reassembled coherent text.
        """
        try:
            # Since overlaps were handled during correction with context, concatenate chunks directly
            final_text = "".join(corrected_chunks)

            # Optionally adjust length to match original if specified
            if original_text_length and len(final_text) != original_text_length:
                logger.warning(f"Reassembled text length ({len(final_text)}) does not match original length ({original_text_length}). Adjusting...")
                if len(final_text) > original_text_length:
                    final_text = final_text[:original_text_length]
                else:
                    final_text += " " * (original_text_length - len(final_text))

            logger.info("Text reassembled successfully.")
            return final_text
        except Exception as e:
            logger.error(f"Error reassembling text: {e}")
            raise

    def process_pdf(self, pdf_path) -> str:
        """
        Process a PDF: extract raw text with OCR, correct errors with DeepSeek runnables using context awareness, and reassemble.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Corrected and reassembled text.
        """
        try:
            # Extract raw text using OCR
            extracted_text = self.extract_text_from_pdf(pdf_path)
            original_length = len(extracted_text)
            logger.debug(f"Extracted text length: {original_length}")

            # Reset context (summary) for a new PDF
            self.previous_summary = ""

            # Split, correct with runnables and context, and reassemble text
            corrected_chunks = self.split_and_correct_text_with_runnables(extracted_text)
            logger.debug(f"Number of corrected chunks: {len(corrected_chunks)}")
            final_text = self.reassemble_text(corrected_chunks, original_length)

            logger.debug(f"Final text length: {len(final_text)}")
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