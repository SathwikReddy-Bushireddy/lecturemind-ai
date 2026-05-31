import re
from typing import List, Dict, Any

def split_text(text: str, doc_name: str = "Document", chunk_size: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
    """
    Splits the extracted merged PDF text into semantic chunks, preserving
    the page number and source document name metadata for accurate RAG citations.

    Args:
        text: The merged raw text from the extraction pipeline.
        doc_name: Fallback document name if document headers are missing.
        chunk_size: Maximum characters inside a single chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List[Dict[str, Any]]: A list of chunk dictionaries:
            [
                {
                    "text": str,
                    "page_num": int,
                    "doc_name": str
                },
                ...
            ]
    """
    chunks = []
    
    if not text or not text.strip():
        return chunks

    # Document sections are split by the parser prefix: "=== DOCUMENT: filename ==="
    doc_sections = re.split(r"=== DOCUMENT: (.*?) ===\n", text)
    
    if len(doc_sections) < 3:
        # No document headers matched, treat the whole block as a single source
        doc_sections = ["", doc_name, text]

    # Iterating through document sections
    # re.split returns [pre_text, matched_group_1, post_match_1, matched_group_2, ...]
    idx = 1
    while idx < len(doc_sections):
        curr_doc_name = doc_sections[idx].strip()
        curr_doc_content = doc_sections[idx + 1] if idx + 1 < len(doc_sections) else ""
        idx += 2

        if not curr_doc_content.strip():
            continue

        # Page divisions are split by the page prefix: "--- [Page N] ---"
        page_splits = re.split(r"--- \[Page (\d+)\] ---\n", curr_doc_content)
        
        if len(page_splits) < 3:
            # No page dividers matched, default to page 1
            page_splits = ["", "1", curr_doc_content]

        p_idx = 1
        while p_idx < len(page_splits):
            try:
                page_num = int(page_splits[p_idx].strip())
            except ValueError:
                page_num = 1
            
            page_content = page_splits[p_idx + 1] if p_idx + 1 < len(page_splits) else ""
            p_idx += 2

            page_content = page_content.strip()
            if not page_content:
                continue

            # Slide window across page content to generate overlapping text blocks
            start = 0
            content_len = len(page_content)
            
            if content_len <= chunk_size:
                chunks.append({
                    "text": page_content,
                    "page_num": page_num,
                    "doc_name": curr_doc_name
                })
                continue

            while start < content_len:
                end = start + chunk_size
                chunk_txt = page_content[start:end].strip()
                
                if chunk_txt:
                    chunks.append({
                        "text": chunk_txt,
                        "page_num": page_num,
                        "doc_name": curr_doc_name
                    })
                
                # Advance starting window index by (chunk_size - overlap)
                start += (chunk_size - overlap)

    return chunks
