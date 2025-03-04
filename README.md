# Chinese PDF OCR and Error Correction PoC

This project is a proof of concept (PoC) for extracting text from Chinese PDFs using Optical Character Recognition (OCR) with Tesseract, correcting OCR errors using the DeepSeek large language model (LLM) via LangChain, and displaying the results in a user-friendly Streamlit web application. The app provides a full-screen interface to upload Chinese PDFs, process them, and compare the extracted (OCR) and corrected (DeepSeek) text side by side, with real-time progress updates.

## Features

- Extracts text from Chinese PDFs using Tesseract OCR (supports Simplified and Traditional Chinese).
- Corrects OCR errors (garbled text, typos, missing words) using DeepSeek, integrated via LangChain.
- Displays extracted and corrected text side by side for comparison in a Streamlit app.
- Full-screen width layout with progress bars and status updates during processing.
- Dockerized for easy deployment and portability on Linux systems.


## Installation

### Clone the Repository


```bash
git clone https://github.com/Nitish992/chinese-pdf-ocr-correction
cd chinese-pdf-ocr-correction
```

### Set Up Environment Variables

An example `env.example` file is provided in the repository. To set up your environment, rename it to `.env`:

```bash
cp .env.example .env
```

This `.env` file already contains a placeholder API key that you can use to test the application.

### Docker Installation

1. Ensure Docker is installed on your Linux system. Follow [Docker’s official installation guide](https://docs.docker.com/engine/install/ubuntu/) for Ubuntu/Debian.
2. Build the Docker image using a lightweight Python 3.12 base:

```bash
docker build -t chinese-pdf-ocr-poc .
```

3. Run the Docker container:

```bash
docker run -d -p 8501:8501 --name ocr-container chinese-pdf-ocr-poc
```

## Usage

After building and running the Docker container (as described above), access the app at [http://localhost:8501](http://localhost:8501) in your web browser.
Upload a Chinese PDF file to process it within the Dockerized environment.

## Project Structure

- `app.py`: The Streamlit web application for the PoC.
- `pdf_repair_service.py`: The Python class (`PDFRepairService`) handling OCR extraction, DeepSeek correction, and text reassembly.
- `Dockerfile`: Configuration for dockerizing the app.
- `requirements.txt`: List of Python dependencies.
- `README.md`: This file.
- `.env`: Environment file containing API keys and configurations.

## Configuration
- **Chinese Variant**: By default, the app uses Simplified Chinese (`chi_sim`). To use Traditional Chinese, modify the `tesseract_lang` in `pdf_repair_service.py` to `'chi_tra'`.
### Notes

- **File Paths**: Ensure `app.py`, `pdf_repair_service.py`, `Dockerfile`, `requirements.txt`, and `.env` are in the same directory.
- **Testing**: Test with small Chinese PDFs to verify functionality before processing larger files.
- **Performance**: Processing large PDFs may take time due to OCR and API calls; the app includes progress updates to manage user expectations.
