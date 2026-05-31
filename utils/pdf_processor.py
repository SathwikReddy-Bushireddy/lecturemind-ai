import io
import os
import logging
from typing import Union, List, Dict, Any, IO

# Suppress noisy PyPDF2 messages
logging.getLogger("PyPDF2").setLevel(logging.ERROR)

# Initialize module logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def extract_single_pdf(pdf_input: Union[str, bytes, IO[bytes]]) -> tuple[str, int]:
    """
    Extracts text and page count from a single PDF input (file path, raw bytes, 
    or file-like stream) using pdfplumber, falling back to PyPDF2 on failure.

    Args:
        pdf_input: The PDF input to parse. Can be a string path, raw bytes, or stream.

    Returns:
        tuple[str, int]: A tuple containing (extracted_clean_text, total_page_count).
    """
    import pdfplumber
    from PyPDF2 import PdfReader

    stream = None
    opened_locally = False
    text_content = []
    page_count = 0
    parsed_with_plumber = False

    try:
        # Normalize various input formats into a standard binary reader stream
        if isinstance(pdf_input, str):
            if not os.path.exists(pdf_input):
                logger.error(f"Filesystem path does not exist: {pdf_input}")
                return "", 0
            stream = open(pdf_input, "rb")
            opened_locally = True
        elif isinstance(pdf_input, bytes):
            stream = io.BytesIO(pdf_input)
        elif hasattr(pdf_input, "read"):
            stream = pdf_input
            # Reset stream position to start if seekable
            if hasattr(stream, "seek"):
                try:
                    stream.seek(0)
                except Exception:
                    pass
        else:
            logger.error(f"Unsupported PDF input type: {type(pdf_input)}")
            return "", 0

        # --- PRIMARY EXTRACTION: pdfplumber ---
        try:
            logger.info("Attempting PDF text extraction using pdfplumber...")
            with pdfplumber.open(stream) as pdf:
                page_count = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        # Clean layout whitespace page by page
                        cleaned_page = "\n".join(
                            line.strip() for line in page_text.splitlines() if line.strip()
                        )
                        if cleaned_page:
                            text_content.append(f"--- [Page {i + 1}] ---\n{cleaned_page}")
                parsed_with_plumber = True
                logger.info(f"Successfully extracted {page_count} pages using pdfplumber.")
        except Exception as plumber_err:
            logger.warning(f"pdfplumber extraction failed: {str(plumber_err)}. Swapping to PyPDF2 fallback...")

        # --- FALLBACK EXTRACTION: PyPDF2 ---
        if not parsed_with_plumber or not any(text_content):
            # Reset stream position to start if seekable
            if hasattr(stream, "seek"):
                try:
                    stream.seek(0)
                except Exception:
                    pass
            
            try:
                logger.info("Attempting PDF text extraction using PyPDF2 fallback...")
                reader = PdfReader(stream)
                page_count = len(reader.pages)
                text_content = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        cleaned_page = "\n".join(
                            line.strip() for line in page_text.splitlines() if line.strip()
                        )
                        if cleaned_page:
                            text_content.append(f"--- [Page {i + 1}] ---\n{cleaned_page}")
                logger.info(f"Successfully extracted {page_count} pages using PyPDF2 fallback.")
            except Exception as pypdf_err:
                logger.error(f"PyPDF2 fallback also failed: {str(pypdf_err)}")

        extracted_text = "\n\n".join(text_content).strip()
        return extracted_text, page_count

    except Exception as e:
        logger.error(f"Unexpected error during single PDF extraction: {str(e)}")
        return "", 0

    finally:
        # Guarantee closure of streams opened locally inside this execution block
        if opened_locally and stream is not None:
            try:
                stream.close()
            except Exception as close_err:
                logger.warning(f"Failed to close local PDF file stream: {str(close_err)}")

def process_pdfs(
    pdf_inputs: Union[str, bytes, IO[bytes], List[Union[str, bytes, IO[bytes]]]]
) -> Dict[str, Any]:
    """
    Parses one or multiple PDF inputs (file paths, raw bytes, or streams),
    extracts clean text, preserves document order, and merges them.

    Args:
        pdf_inputs: A single PDF path/bytes/stream, or a List containing multiple PDFs.

    Returns:
        Dict[str, Any]: A dictionary matching the requested schema:
            {
                "text": str,              # Extracted, merged text contents
                "num_pages": int,         # Total page count processed
                "num_documents": int      # Total documents successfully loaded
            }
    """
    logger.info("Initializing PDF text extraction pipeline...")

    if pdf_inputs is None:
        logger.warning("PDF extraction pipeline received None input.")
        return {"text": "", "num_pages": 0, "num_documents": 0}

    # Standardize input parameters to a flat list
    if not isinstance(pdf_inputs, list):
        inputs_list = [pdf_inputs]
    else:
        inputs_list = pdf_inputs

    total_pages = 0
    total_documents = 0
    extracted_texts = []

    for idx, pdf_input in enumerate(inputs_list):
        # Resolve a descriptive name for log outputs and text headers
        doc_name = "Document"
        if isinstance(pdf_input, str):
            doc_name = os.path.basename(pdf_input)
        elif hasattr(pdf_input, "name"):
            doc_name = getattr(pdf_input, "name")
        else:
            doc_name = f"Uploaded PDF {idx + 1}"

        logger.info(f"Processing PDF document {idx + 1}/{len(inputs_list)}: '{doc_name}'")
        
        try:
            text, pages = extract_single_pdf(pdf_input)
            
            if pages > 0:
                header = f"=== DOCUMENT: {doc_name} ==="
                if text:
                    extracted_texts.append(f"{header}\n{text}\n")
                else:
                    extracted_texts.append(f"{header}\n[Empty text or scanned document pages detected]\n")
                total_pages += pages
                total_documents += 1
            else:
                logger.warning(f"Document '{doc_name}' resulted in 0 pages.")

        except Exception as err:
            logger.error(f"Critical error parsing document '{doc_name}' at index {idx}: {str(err)}")

    # Merge extracted strings preserving order
    merged_text = "\n".join(extracted_texts).strip()

    result = {
        "text": merged_text,
        "num_pages": total_pages,
        "num_documents": total_documents
    }

    logger.info(
        f"PDF pipeline execution complete. Merged {total_documents}/{len(inputs_list)} documents. "
        f"Combined Page Count: {total_pages}."
    )
    return result
