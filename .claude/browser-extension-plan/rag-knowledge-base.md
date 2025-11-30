# RAG Knowledge Base Implementation

## Overview

This document details the implementation of a Retrieval-Augmented Generation (RAG) system that uses user-uploaded documents to create a personalized knowledge base for generating contextual job application responses.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Knowledge Base System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  Document   │  │   Text       │  │    Vector Database      │ │
│  │  Upload     │─►│ Processing   │─►│    (Supabase)          │ │
│  │             │  │              │  │                         │ │
│  │ PDF/DOCX    │  │ ┌──────────┐ │  │ ┌─────────────────────┐ │ │
│  │ Resume      │  │ │Chunking  │ │  │ │ Embeddings          │ │ │
│  │ Portfolio   │  │ │Cleaning  │ │  │ │ (1536 dimensions)   │ │ │
│  │ Projects    │  │ │Metadata  │ │  │ │                     │ │ │
│  └─────────────┘  │ └──────────┘ │  │ └─────────────────────┘ │ │
│                   │              │  │                         │ │
│                   │ ┌──────────┐ │  │ ┌─────────────────────┐ │ │
│                   │ │OpenAI    │ │  │ │ Similarity Search   │ │ │
│                   │ │Embedding │ │  │ │ (Cosine Distance)   │ │ │
│                   │ │API       │ │  │ │                     │ │ │
│                   │ └──────────┘ │  │ └─────────────────────┘ │ │
│                   └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────┐
                    │       Response Generation         │
                    │                                   │
                    │ ┌─────────────┐ ┌──────────────┐ │
                    │ │  Context    │ │    GPT-4o    │ │
                    │ │ Retrieval   │─►│   Response   │ │
                    │ │             │ │  Generation  │ │
                    │ │ ┌─────────┐ │ │              │ │
                    │ │ │Question │ │ │ ┌──────────┐ │ │
                    │ │ │Embedding│ │ │ │Personalized│ │
                    │ │ └─────────┘ │ │ │Response    │ │ │
                    │ │             │ │ └──────────┘ │ │
                    │ └─────────────┘ └──────────────┘ │
                    └───────────────────────────────────┘
```

## Document Processing Pipeline

### 1. Document Upload and Validation

```python
# backend/app/services/document_processor.py

import asyncio
import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import docx
import mammoth
from PIL import Image
import pytesseract

class DocumentProcessor:
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_types = {
            'application/pdf': self._process_pdf,
            'application/msword': self._process_doc,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx,
            'text/plain': self._process_txt,
            'image/jpeg': self._process_image,
            'image/png': self._process_image
        }

    async def process_document(self, file_path: str, file_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main document processing pipeline

        Returns:
            {
                'content': str,           # Extracted text content
                'chunks': List[str],      # Text chunks for embedding
                'metadata': Dict,         # Enhanced metadata
                'word_count': int,        # Word count
                'processing_stats': Dict  # Processing statistics
            }
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise ValueError("File not found")

            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError("File too large")

            # Extract text based on file type
            processor = self.allowed_types.get(file_type)
            if not processor:
                raise ValueError(f"Unsupported file type: {file_type}")

            content = await processor(file_path)

            if not content or len(content.strip()) < 10:
                raise ValueError("No meaningful content extracted")

            # Clean and process content
            cleaned_content = self._clean_text(content)

            # Extract metadata from content
            enhanced_metadata = await self._extract_content_metadata(cleaned_content, metadata)

            # Create text chunks for embedding
            chunks = self._create_text_chunks(cleaned_content, chunk_size=1000, overlap=200)

            # Calculate statistics
            stats = {
                'word_count': len(cleaned_content.split()),
                'character_count': len(cleaned_content),
                'chunk_count': len(chunks),
                'avg_chunk_size': sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
            }

            return {
                'content': cleaned_content,
                'chunks': chunks,
                'metadata': enhanced_metadata,
                'word_count': stats['word_count'],
                'processing_stats': stats
            }

        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")

    async def _process_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            content = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            content.append(f"--- Page {page_num + 1} ---\n{text}")
                    except Exception as e:
                        print(f"Error extracting page {page_num + 1}: {e}")
                        continue

            return '\n\n'.join(content)

        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")

    async def _process_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx and mammoth"""
        try:
            # Primary extraction with python-docx
            doc = docx.Document(file_path)
            content_parts = []

            for para in doc.paragraphs:
                if para.text.strip():
                    content_parts.append(para.text)

            # Extract tables
            for table in doc.tables:
                table_content = []
                for row in table.rows:
                    row_content = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_content.append(cell.text.strip())
                    if row_content:
                        table_content.append(' | '.join(row_content))

                if table_content:
                    content_parts.append('\n--- Table ---\n' + '\n'.join(table_content))

            primary_content = '\n\n'.join(content_parts)

            # Fallback with mammoth for better formatting
            if len(primary_content) < 100:
                with open(file_path, 'rb') as docx_file:
                    result = mammoth.extract_raw_text(docx_file)
                    if result.value and len(result.value) > len(primary_content):
                        return result.value

            return primary_content

        except Exception as e:
            raise Exception(f"DOCX processing failed: {str(e)}")

    async def _process_doc(self, file_path: str) -> str:
        """Extract text from legacy DOC files using mammoth"""
        try:
            with open(file_path, 'rb') as doc_file:
                result = mammoth.extract_raw_text(doc_file)
                return result.value

        except Exception as e:
            raise Exception(f"DOC processing failed: {str(e)}")

    async def _process_txt(self, file_path: str) -> str:
        """Process plain text files"""
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue

            raise Exception("Could not decode text file with any supported encoding")

        except Exception as e:
            raise Exception(f"Text file processing failed: {str(e)}")

    async def _process_image(self, file_path: str) -> str:
        """Extract text from images using OCR"""
        try:
            # Check if tesseract is available
            if not self._is_tesseract_available():
                raise Exception("OCR not available - tesseract not installed")

            # Open and process image
            image = Image.open(file_path)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract text using OCR
            text = pytesseract.image_to_string(image)

            if len(text.strip()) < 10:
                raise Exception("No meaningful text extracted from image")

            return text

        except Exception as e:
            raise Exception(f"Image OCR processing failed: {str(e)}")

    def _is_tesseract_available(self) -> bool:
        """Check if tesseract OCR is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    def _clean_text(self, content: str) -> str:
        """Clean and normalize extracted text"""
        import re

        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove control characters
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', content)

        # Normalize line breaks
        content = re.sub(r'\n\s*\n', '\n\n', content)

        # Remove URLs and email addresses for privacy
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', content)
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)

        return content.strip()

    async def _extract_content_metadata(self, content: str, original_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from document content using AI"""
        try:
            from app.core.ai_service import ai_service

            # Use AI to extract structured metadata
            prompt = f"""
            Analyze this document content and extract structured metadata:

            Content: {content[:2000]}...

            Extract the following information in JSON format:
            {{
                "document_type": "resume|cover_letter|portfolio|project|certificate|other",
                "skills": ["skill1", "skill2", ...],
                "experience_years": number or null,
                "education_level": "high_school|bachelor|master|phd|other|unknown",
                "job_titles": ["title1", "title2", ...],
                "companies": ["company1", "company2", ...],
                "technologies": ["tech1", "tech2", ...],
                "summary": "brief summary of document content",
                "key_achievements": ["achievement1", "achievement2", ...],
                "certifications": ["cert1", "cert2", ...]
            }}

            Only return valid JSON.
            """

            ai_metadata = await ai_service.generate_structured_data(prompt, max_tokens=500)

            # Combine with original metadata
            enhanced_metadata = {
                **original_metadata,
                **ai_metadata,
                'content_analysis': {
                    'word_count': len(content.split()),
                    'character_count': len(content),
                    'paragraphs': content.count('\n\n') + 1,
                    'extracted_at': datetime.utcnow().isoformat()
                }
            }

            return enhanced_metadata

        except Exception as e:
            print(f"AI metadata extraction failed: {e}")
            return original_metadata

    def _create_text_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Create overlapping text chunks for embedding"""
        if not content:
            return []

        # Split by paragraphs first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if not paragraphs:
            # Fallback to sentence splitting
            sentences = [s.strip() + '.' for s in content.split('.') if s.strip()]
            paragraphs = sentences

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # If adding this paragraph exceeds chunk size, start new chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + " " + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk) > 50]

        return chunks
```

### 2. Vector Embedding Generation

```python
# backend/app/services/embedding_service.py

from typing import List, Dict, Any
import asyncio
import numpy as np
from openai import AsyncOpenAI

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.model = "text-embedding-3-small"
        self.max_tokens = 8192
        self.batch_size = 100

    async def generate_embeddings(self, texts: List[str], metadata: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of texts

        Returns:
            List of embeddings with metadata
        """
        if not texts:
            return []

        # Validate and truncate texts
        processed_texts = [self._prepare_text(text) for text in texts]

        embeddings = []
        for i in range(0, len(processed_texts), self.batch_size):
            batch = processed_texts[i:i + self.batch_size]
            batch_metadata = metadata[i:i + self.batch_size] if metadata else [{}] * len(batch)

            batch_embeddings = await self._generate_batch_embeddings(batch, batch_metadata)
            embeddings.extend(batch_embeddings)

        return embeddings

    async def _generate_batch_embeddings(self, texts: List[str], metadata: List[Dict]) -> List[Dict[str, Any]]:
        """Generate embeddings for a batch of texts"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )

            embeddings = []
            for i, embedding_obj in enumerate(response.data):
                embeddings.append({
                    'text': texts[i],
                    'embedding': embedding_obj.embedding,
                    'metadata': metadata[i] if i < len(metadata) else {},
                    'model': self.model,
                    'dimensions': len(embedding_obj.embedding)
                })

            return embeddings

        except Exception as e:
            raise Exception(f"Batch embedding generation failed: {str(e)}")

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a search query"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=[self._prepare_text(query)]
            )

            return response.data[0].embedding

        except Exception as e:
            raise Exception(f"Query embedding generation failed: {str(e)}")

    def _prepare_text(self, text: str) -> str:
        """Prepare text for embedding generation"""
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Truncate if too long (rough token estimation: 1 token ≈ 4 characters)
        max_chars = self.max_tokens * 4
        if len(text) > max_chars:
            text = text[:max_chars-3] + "..."

        return text

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            print(f"Similarity calculation failed: {e}")
            return 0.0
```

### 3. Vector Database Implementation

```python
# backend/app/services/vector_store.py

from typing import List, Dict, Any, Optional, Tuple
import json
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.models.extension import DocumentVector
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.table_name = "document_vectors"

    async def store_document_embeddings(
        self,
        document_id: str,
        user_id: str,
        chunks: List[str],
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Store embeddings for a document's text chunks

        Returns:
            Number of embeddings stored
        """
        try:
            if not chunks:
                return 0

            # Generate embeddings for all chunks
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = {
                    'chunk_index': i,
                    'chunk_length': len(chunk),
                    'document_metadata': metadata or {}
                }
                chunk_metadata.append(chunk_meta)

            embeddings = await self.embedding_service.generate_embeddings(chunks, chunk_metadata)

            # Store in database
            db = next(get_db())
            stored_count = 0

            try:
                for i, embedding_data in enumerate(embeddings):
                    vector_entry = DocumentVector(
                        document_id=document_id,
                        user_id=user_id,
                        content_chunk=embedding_data['text'],
                        chunk_index=i,
                        embedding=json.dumps(embedding_data['embedding']),
                        metadata=embedding_data['metadata']
                    )

                    db.add(vector_entry)
                    stored_count += 1

                db.commit()
                logger.info(f"Stored {stored_count} embeddings for document {document_id}")

            except Exception as e:
                db.rollback()
                raise Exception(f"Database storage failed: {str(e)}")

            finally:
                db.close()

            return stored_count

        except Exception as e:
            logger.error(f"Failed to store document embeddings: {str(e)}")
            raise

    async def similarity_search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        threshold: float = 0.7,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity

        Returns:
            List of similar chunks with metadata and similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_query_embedding(query)

            # Convert embedding to string for PostgreSQL
            embedding_str = json.dumps(query_embedding)

            db = next(get_db())

            try:
                # Build SQL query for similarity search
                sql_query = text("""
                    SELECT
                        dv.document_id,
                        dv.content_chunk,
                        dv.chunk_index,
                        dv.metadata,
                        1 - (dv.embedding::vector <=> :query_embedding::vector) as similarity
                    FROM document_vectors dv
                    WHERE dv.user_id = :user_id
                    AND (:document_ids IS NULL OR dv.document_id = ANY(:document_ids))
                    AND 1 - (dv.embedding::vector <=> :query_embedding::vector) >= :threshold
                    ORDER BY dv.embedding::vector <=> :query_embedding::vector
                    LIMIT :limit
                """)

                params = {
                    'query_embedding': embedding_str,
                    'user_id': user_id,
                    'document_ids': document_ids,
                    'threshold': threshold,
                    'limit': limit
                }

                result = db.execute(sql_query, params)
                rows = result.fetchall()

                # Process results
                similar_chunks = []
                for row in rows:
                    similar_chunks.append({
                        'document_id': row.document_id,
                        'content': row.content_chunk,
                        'chunk_index': row.chunk_index,
                        'similarity_score': float(row.similarity),
                        'metadata': row.metadata
                    })

                logger.info(f"Found {len(similar_chunks)} similar chunks for query")
                return similar_chunks

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise

    async def delete_document_vectors(self, document_id: str) -> int:
        """
        Delete all vectors for a specific document

        Returns:
            Number of vectors deleted
        """
        try:
            db = next(get_db())

            try:
                deleted_count = db.query(DocumentVector).filter(
                    DocumentVector.document_id == document_id
                ).count()

                db.query(DocumentVector).filter(
                    DocumentVector.document_id == document_id
                ).delete()

                db.commit()
                logger.info(f"Deleted {deleted_count} vectors for document {document_id}")
                return deleted_count

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to delete document vectors: {str(e)}")
            raise

    async def get_user_document_count(self, user_id: str) -> Dict[str, int]:
        """Get statistics about user's vectorized documents"""
        try:
            db = next(get_db())

            try:
                sql_query = text("""
                    SELECT
                        COUNT(DISTINCT document_id) as document_count,
                        COUNT(*) as chunk_count,
                        AVG(LENGTH(content_chunk)) as avg_chunk_length
                    FROM document_vectors
                    WHERE user_id = :user_id
                """)

                result = db.execute(sql_query, {'user_id': user_id})
                row = result.fetchone()

                return {
                    'document_count': row.document_count or 0,
                    'chunk_count': row.chunk_count or 0,
                    'avg_chunk_length': float(row.avg_chunk_length or 0)
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to get user document count: {str(e)}")
            return {'document_count': 0, 'chunk_count': 0, 'avg_chunk_length': 0}
```

### 4. RAG Response Generation Service

```python
# backend/app/services/rag_service.py

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.ai_service import ai_service
from .vector_store import VectorStore
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.max_context_length = 4000  # Characters
        self.min_similarity_threshold = 0.6

    async def generate_application_response(
        self,
        question: str,
        user_id: str,
        job_context: Optional[Dict[str, Any]] = None,
        response_style: str = 'professional',
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generate personalized response to application question using RAG

        Returns:
            {
                'response': str,
                'confidence': float,
                'sources': List[Dict],
                'context_used': str,
                'generation_metadata': Dict
            }
        """
        try:
            logger.info(f"Generating RAG response for question: {question[:50]}...")

            # Retrieve relevant context from user's documents
            relevant_chunks = await self._retrieve_relevant_context(
                question,
                user_id,
                job_context
            )

            if not relevant_chunks:
                logger.warning("No relevant context found in user's documents")
                return await self._generate_fallback_response(
                    question,
                    response_style,
                    max_length
                )

            # Build context for generation
            context = self._build_generation_context(relevant_chunks, job_context)

            # Generate response using GPT-4
            response = await self._generate_contextual_response(
                question,
                context,
                response_style,
                max_length
            )

            # Calculate confidence based on context relevance
            confidence = self._calculate_response_confidence(relevant_chunks)

            return {
                'response': response,
                'confidence': confidence,
                'sources': [
                    {
                        'document_id': chunk['document_id'],
                        'similarity_score': chunk['similarity_score'],
                        'content_preview': chunk['content'][:100] + '...'
                    }
                    for chunk in relevant_chunks
                ],
                'context_used': context[:200] + '...' if len(context) > 200 else context,
                'generation_metadata': {
                    'chunks_used': len(relevant_chunks),
                    'avg_similarity': sum(c['similarity_score'] for c in relevant_chunks) / len(relevant_chunks),
                    'response_length': len(response),
                    'generated_at': datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"RAG response generation failed: {str(e)}")
            raise Exception(f"Response generation failed: {str(e)}")

    async def _retrieve_relevant_context(
        self,
        question: str,
        user_id: str,
        job_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from user's documents"""

        # Enhance query with job context
        enhanced_query = self._enhance_query_with_context(question, job_context)

        # Search for relevant chunks
        relevant_chunks = await self.vector_store.similarity_search(
            query=enhanced_query,
            user_id=user_id,
            limit=8,
            threshold=self.min_similarity_threshold
        )

        # Filter and rank chunks
        filtered_chunks = self._filter_and_rank_chunks(
            relevant_chunks,
            question,
            job_context
        )

        return filtered_chunks

    def _enhance_query_with_context(
        self,
        question: str,
        job_context: Optional[Dict[str, Any]]
    ) -> str:
        """Enhance search query with job context information"""

        enhanced_parts = [question]

        if job_context:
            # Add relevant job information to improve context retrieval
            if 'title' in job_context:
                enhanced_parts.append(f"for {job_context['title']} role")

            if 'company' in job_context:
                enhanced_parts.append(f"at {job_context['company']}")

            if 'skills' in job_context and isinstance(job_context['skills'], list):
                skills_str = ', '.join(job_context['skills'][:5])  # Top 5 skills
                enhanced_parts.append(f"requiring {skills_str}")

        return ' '.join(enhanced_parts)

    def _filter_and_rank_chunks(
        self,
        chunks: List[Dict[str, Any]],
        question: str,
        job_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter and rank chunks based on relevance"""

        if not chunks:
            return []

        # Score chunks based on multiple factors
        scored_chunks = []

        for chunk in chunks:
            score = chunk['similarity_score']

            # Boost score based on content type relevance
            content = chunk['content'].lower()
            metadata = chunk.get('metadata', {})

            # Boost if chunk contains experience/project information
            if any(keyword in content for keyword in ['experience', 'project', 'achieved', 'developed', 'led', 'managed']):
                score += 0.1

            # Boost if chunk is from resume/CV
            if metadata.get('document_type') == 'resume':
                score += 0.05

            # Boost if chunk contains skills mentioned in job context
            if job_context and 'skills' in job_context:
                job_skills = [skill.lower() for skill in job_context['skills']]
                content_skills = [skill for skill in job_skills if skill in content]
                if content_skills:
                    score += len(content_skills) * 0.02

            chunk['final_score'] = score
            scored_chunks.append(chunk)

        # Sort by final score and return top chunks
        scored_chunks.sort(key=lambda x: x['final_score'], reverse=True)

        # Limit total context length
        selected_chunks = []
        total_length = 0

        for chunk in scored_chunks:
            chunk_length = len(chunk['content'])
            if total_length + chunk_length <= self.max_context_length:
                selected_chunks.append(chunk)
                total_length += chunk_length
            else:
                break

        return selected_chunks

    def _build_generation_context(
        self,
        chunks: List[Dict[str, Any]],
        job_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build context string for response generation"""

        context_parts = []

        # Add job context if available
        if job_context:
            job_info = []
            if 'title' in job_context:
                job_info.append(f"Position: {job_context['title']}")
            if 'company' in job_context:
                job_info.append(f"Company: {job_context['company']}")
            if 'description' in job_context:
                job_info.append(f"Description: {job_context['description'][:200]}...")

            if job_info:
                context_parts.append("JOB CONTEXT:\n" + '\n'.join(job_info))

        # Add user's relevant experience/information
        if chunks:
            context_parts.append("\nRELEVANT EXPERIENCE/INFORMATION:")
            for i, chunk in enumerate(chunks):
                context_parts.append(f"\n[Source {i+1}]:\n{chunk['content']}")

        return '\n'.join(context_parts)

    async def _generate_contextual_response(
        self,
        question: str,
        context: str,
        style: str,
        max_length: int
    ) -> str:
        """Generate response using GPT-4 with context"""

        style_instructions = {
            'professional': "Write in a professional, formal tone suitable for job applications.",
            'friendly': "Write in a warm, approachable tone while remaining professional.",
            'custom': "Match the tone and style of the provided context."
        }

        style_instruction = style_instructions.get(style, style_instructions['professional'])

        prompt = f"""
        You are helping someone write a response to a job application question. Use the provided context about their background and experience to write a personalized, authentic response.

        QUESTION: {question}

        CONTEXT ABOUT THE CANDIDATE:
        {context}

        INSTRUCTIONS:
        - {style_instruction}
        - Use specific details from the context to make the response personal and credible
        - Keep response under {max_length} characters
        - Focus on relevant experience and achievements
        - Don't fabricate information not in the context
        - Make it compelling and well-structured
        - If the context doesn't contain enough relevant information, acknowledge this and provide a general but thoughtful response

        RESPONSE:
        """

        try:
            response = await ai_service.generate_response(
                prompt=prompt,
                max_tokens=max_length // 3,  # Rough token estimation
                temperature=0.7
            )

            return response.strip()

        except Exception as e:
            raise Exception(f"Response generation failed: {str(e)}")

    async def _generate_fallback_response(
        self,
        question: str,
        style: str,
        max_length: int
    ) -> Dict[str, Any]:
        """Generate fallback response when no relevant context found"""

        fallback_prompt = f"""
        Generate a thoughtful response to this job application question: {question}

        Since no specific background information is available, provide a general but professional response that:
        - Addresses the question directly
        - Shows enthusiasm and motivation
        - Demonstrates critical thinking
        - Keeps under {max_length} characters
        - Uses a {style} tone

        RESPONSE:
        """

        try:
            response = await ai_service.generate_response(
                prompt=fallback_prompt,
                max_tokens=max_length // 3,
                temperature=0.8
            )

            return {
                'response': response.strip(),
                'confidence': 0.3,  # Lower confidence for fallback
                'sources': [],
                'context_used': 'No specific context available',
                'generation_metadata': {
                    'chunks_used': 0,
                    'avg_similarity': 0.0,
                    'response_length': len(response),
                    'generated_at': datetime.utcnow().isoformat(),
                    'fallback_used': True
                }
            }

        except Exception as e:
            raise Exception(f"Fallback response generation failed: {str(e)}")

    def _calculate_response_confidence(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for generated response"""

        if not chunks:
            return 0.3

        # Base confidence on similarity scores and chunk relevance
        avg_similarity = sum(chunk['similarity_score'] for chunk in chunks) / len(chunks)

        # Boost confidence based on number of relevant chunks
        chunk_bonus = min(len(chunks) * 0.05, 0.2)

        # Boost confidence if chunks contain detailed experience
        detail_bonus = 0.0
        for chunk in chunks:
            content = chunk['content'].lower()
            if any(keyword in content for keyword in ['achieved', 'increased', 'reduced', 'led team', 'managed', 'developed']):
                detail_bonus += 0.05

        confidence = min(avg_similarity + chunk_bonus + detail_bonus, 0.95)
        return round(confidence, 2)

    async def search_knowledge_base(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search user's knowledge base directly"""

        try:
            results = await self.vector_store.similarity_search(
                query=query,
                user_id=user_id,
                limit=limit,
                threshold=0.5
            )

            return [
                {
                    'content': result['content'],
                    'similarity': result['similarity_score'],
                    'document_id': result['document_id'],
                    'metadata': result.get('metadata', {})
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Knowledge base search failed: {str(e)}")
            return []
```

### 5. Performance Optimizations

```python
# backend/app/services/vector_optimization.py

import asyncio
from typing import List, Dict, Any
import redis
import json
from datetime import datetime, timedelta

class VectorOptimizationService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour

    async def cache_frequent_queries(self, user_id: str, query: str, results: List[Dict]) -> None:
        """Cache frequently used query results"""
        cache_key = f"vector_search:{user_id}:{hash(query)}"

        try:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(results, default=str)
            )
        except Exception as e:
            print(f"Cache storage failed: {e}")

    async def get_cached_results(self, user_id: str, query: str) -> Optional[List[Dict]]:
        """Retrieve cached query results"""
        cache_key = f"vector_search:{user_id}:{hash(query)}"

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache retrieval failed: {e}")

        return None

    async def precompute_user_embeddings(self, user_id: str) -> None:
        """Precompute and cache user document embeddings for faster search"""
        # Implementation for embedding precomputation
        pass

    def optimize_chunk_size(self, content: str, target_chunks: int = 10) -> int:
        """Dynamically optimize chunk size based on content length"""
        content_length = len(content)
        optimal_size = max(200, min(1500, content_length // target_chunks))
        return optimal_size
```

## Usage Examples

### Document Upload and Processing

```python
# Example usage in API endpoint
@router.post("/documents/upload")
async def upload_document(file: UploadFile, user_id: str):
    processor = DocumentProcessor()

    # Process document
    result = await processor.process_document(
        file_path=saved_file_path,
        file_type=file.content_type,
        metadata={'category': 'resume', 'title': file.filename}
    )

    # Store embeddings
    vector_store = VectorStore()
    embedding_count = await vector_store.store_document_embeddings(
        document_id=document_id,
        user_id=user_id,
        chunks=result['chunks'],
        metadata=result['metadata']
    )

    return {"embeddings_stored": embedding_count}
```

### Response Generation

```python
# Example usage in extension API
@router.post("/generate-response")
async def generate_response(request: ResponseRequest):
    rag_service = RAGService()

    response = await rag_service.generate_application_response(
        question=request.question,
        user_id=request.user_id,
        job_context={
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'skills': ['Python', 'React', 'AWS']
        },
        response_style='professional',
        max_length=400
    )

    return response
```

This RAG implementation provides a robust foundation for creating personalized, contextual responses based on user's actual experience and documents, significantly improving the quality and authenticity of job application responses.