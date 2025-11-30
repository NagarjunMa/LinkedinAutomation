# Backend API Specifications

## Overview

This document outlines the new backend API endpoints required to support the browser extension functionality, building upon the existing JobFlow Pro FastAPI infrastructure.

## New API Endpoints

### Extension Management

```python
# backend/app/api/v1/endpoints/extension.py

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.extension import ExtensionDocument, ExtensionActivity, ExtensionSettings
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.services.vector_store import VectorStore
from app.core.security import get_current_user
from app.schemas.extension import *

router = APIRouter()

@router.post("/auth/verify")
async def verify_extension_auth(
    request: ExtensionAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Verify extension authentication token and return user details
    """
    try:
        # Verify JWT token
        user = await verify_jwt_token(request.token)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check extension permissions
        permissions = await get_extension_permissions(user.id)

        return ExtensionAuthResponse(
            valid=True,
            user_id=user.id,
            permissions=permissions,
            refresh_token=await generate_refresh_token(user.id)
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process document for knowledge base
    """
    try:
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large")

        allowed_types = ['application/pdf', 'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain', 'image/jpeg', 'image/png']

        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save file
        document_id = str(uuid.uuid4())
        file_path = await save_uploaded_file(file, user_id, document_id)

        # Create database record
        document = ExtensionDocument(
            id=document_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file.content_type,
            category=category,
            processed_status='pending',
            vector_status='not_indexed',
            metadata={
                'title': title,
                'description': description,
                'tags': tags.split(',') if tags else [],
                'upload_date': datetime.utcnow().isoformat()
            }
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Process document asynchronously
        await process_document_background(document_id)

        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            message="Document uploaded successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents")
async def list_documents(
    user_id: str = Depends(get_current_user),
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List user's documents with optional filtering
    """
    query = db.query(ExtensionDocument).filter(ExtensionDocument.user_id == user_id)

    if category:
        query = query.filter(ExtensionDocument.category == category)

    if status:
        query = query.filter(ExtensionDocument.processed_status == status)

    documents = query.order_by(ExtensionDocument.created_at.desc()).all()

    return DocumentListResponse(
        documents=[DocumentSchema.from_orm(doc) for doc in documents],
        total=len(documents)
    )

@router.post("/documents/{document_id}/vectorize")
async def vectorize_document(
    document_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger document vectorization
    """
    document = db.query(ExtensionDocument).filter(
        ExtensionDocument.id == document_id,
        ExtensionDocument.user_id == user_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processed_status != 'completed':
        raise HTTPException(status_code=400, detail="Document not yet processed")

    # Update status
    document.vector_status = 'indexing'
    db.commit()

    # Vectorize asynchronously
    await vectorize_document_background(document_id)

    return {"success": True, "message": "Vectorization started"}

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete document and associated vectors
    """
    document = db.query(ExtensionDocument).filter(
        ExtensionDocument.id == document_id,
        ExtensionDocument.user_id == user_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    await delete_file(document.file_path)

    # Delete vectors
    await VectorStore().delete_document_vectors(document_id)

    # Delete database record
    db.delete(document)
    db.commit()

    return {"success": True, "message": "Document deleted"}

@router.post("/knowledge/search")
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search user's knowledge base using vector similarity
    """
    vector_store = VectorStore()
    rag_service = RAGService()

    # Generate query embedding
    query_embedding = await rag_service.generate_embedding(request.query)

    # Search vectors
    results = await vector_store.similarity_search(
        embedding=query_embedding,
        user_id=user_id,
        limit=request.limit or 5,
        threshold=request.threshold or 0.7
    )

    return KnowledgeSearchResponse(
        query=request.query,
        results=results,
        total=len(results)
    )

@router.post("/knowledge/generate-response")
async def generate_application_response(
    request: ResponseGenerationRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate response for application question using RAG
    """
    rag_service = RAGService()

    try:
        # Generate response using RAG
        response = await rag_service.generate_application_response(
            question=request.question,
            job_context=request.job_context,
            user_id=user_id,
            response_style=request.response_style or 'professional',
            max_length=request.max_length or 500
        )

        # Log activity
        activity = ExtensionActivity(
            user_id=user_id,
            type='application_response',
            title=f'Response generated: {request.question[:50]}...',
            description=f'Generated {len(response)} character response',
            metadata={
                'question': request.question,
                'response_length': len(response),
                'job_context': request.job_context
            }
        )

        db.add(activity)
        db.commit()

        return ResponseGenerationResponse(
            question=request.question,
            response=response,
            confidence=0.85,  # Calculate actual confidence
            word_count=len(response.split()),
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")

@router.post("/analyze-page")
async def analyze_page(
    request: PageAnalysisRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze page content - either job posting or application form
    """
    try:
        if request.page_type == "job_posting":
            # Use existing job extraction service
            from app.services.job_extraction_strategy import job_extraction_strategy

            job_data = await job_extraction_strategy.extract_job_with_fallback(
                request.url,
                user_context={'user_id': user_id}
            )

            # Log activity
            activity = ExtensionActivity(
                user_id=user_id,
                type='job_analysis',
                title=f'Job analyzed: {job_data.get("title", "Unknown")}',
                description=f'Company: {job_data.get("company", "Unknown")}',
                url=request.url,
                metadata={
                    'job_data': job_data,
                    'extraction_method': job_data.get('extraction_method'),
                    'confidence': job_data.get('confidence', 0)
                }
            )

            db.add(activity)
            db.commit()

            return PageAnalysisResponse(
                page_type="job_posting",
                data=job_data,
                confidence=job_data.get('confidence', 0.8)
            )

        elif request.page_type == "application_form":
            # Generate responses for application questions
            responses = []

            for question_data in request.questions:
                response = await rag_service.generate_application_response(
                    question=question_data['question'],
                    job_context=request.job_context or {},
                    user_id=user_id
                )

                responses.append({
                    'question_id': question_data.get('id'),
                    'question': question_data['question'],
                    'response': response,
                    'field_type': question_data.get('type', 'text')
                })

            # Log activity
            activity = ExtensionActivity(
                user_id=user_id,
                type='application_response',
                title=f'Generated responses for {len(responses)} questions',
                description=f'Application form analysis completed',
                metadata={
                    'questions_count': len(responses),
                    'job_context': request.job_context
                }
            )

            db.add(activity)
            db.commit()

            return PageAnalysisResponse(
                page_type="application_form",
                data={'responses': responses},
                confidence=0.9
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported page type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page analysis failed: {str(e)}")

@router.get("/activity")
async def get_extension_activity(
    user_id: str = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get user's extension activity history
    """
    query = db.query(ExtensionActivity).filter(ExtensionActivity.user_id == user_id)

    if activity_type:
        query = query.filter(ExtensionActivity.type == activity_type)

    activities = query.order_by(
        ExtensionActivity.created_at.desc()
    ).offset(offset).limit(limit).all()

    total = query.count()

    return ExtensionActivityResponse(
        activities=[ActivitySchema.from_orm(activity) for activity in activities],
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/stats")
async def get_extension_stats(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get extension usage statistics
    """
    # Count activities by type
    job_analyses = db.query(ExtensionActivity).filter(
        ExtensionActivity.user_id == user_id,
        ExtensionActivity.type == 'job_analysis'
    ).count()

    responses_generated = db.query(ExtensionActivity).filter(
        ExtensionActivity.user_id == user_id,
        ExtensionActivity.type == 'application_response'
    ).count()

    documents_processed = db.query(ExtensionDocument).filter(
        ExtensionDocument.user_id == user_id,
        ExtensionDocument.processed_status == 'completed'
    ).count()

    # Calculate average compatibility score
    # This would require storing compatibility scores in activities
    avg_compatibility = 75.0  # Placeholder

    return ExtensionStatsResponse(
        total_job_analyses=job_analyses,
        total_responses_generated=responses_generated,
        documents_processed=documents_processed,
        avg_compatibility_score=avg_compatibility,
        last_30_days={
            'job_analyses': job_analyses,  # Would filter by date
            'responses_generated': responses_generated
        }
    )

@router.post("/sync")
async def force_sync(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force sync extension data
    """
    try:
        # Trigger any pending background tasks
        await sync_extension_data(user_id)

        return {"success": True, "message": "Sync completed", "synced_at": datetime.utcnow()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/settings")
async def get_extension_settings(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's extension settings
    """
    settings = db.query(ExtensionSettings).filter(
        ExtensionSettings.user_id == user_id
    ).first()

    if not settings:
        # Create default settings
        settings = ExtensionSettings(
            user_id=user_id,
            auto_sync=True,
            notifications_enabled=True,
            response_style='professional',
            max_applications_per_day=10,
            supported_platforms=['linkedin', 'indeed', 'glassdoor'],
            ai_model_preference='gpt-4o-mini'
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return ExtensionSettingsSchema.from_orm(settings)

@router.post("/settings")
async def update_extension_settings(
    settings_update: ExtensionSettingsUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's extension settings
    """
    settings = db.query(ExtensionSettings).filter(
        ExtensionSettings.user_id == user_id
    ).first()

    if not settings:
        settings = ExtensionSettings(user_id=user_id)
        db.add(settings)

    # Update settings
    for key, value in settings_update.dict(exclude_unset=True).items():
        setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)

    return ExtensionSettingsSchema.from_orm(settings)
```

## Database Models

```python
# backend/app/models/extension.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class ExtensionDocument(Base):
    __tablename__ = "extension_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    category = Column(String, nullable=False)  # resume, portfolio, project, certificate, other

    processed_status = Column(String, default='pending')  # pending, processing, completed, error
    vector_status = Column(String, default='not_indexed')  # not_indexed, indexing, indexed, failed

    content_preview = Column(Text)
    metadata = Column(JSON, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExtensionActivity(Base):
    __tablename__ = "extension_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # job_analysis, application_response, document_upload
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String)

    metadata = Column(JSON, default={})
    status = Column(String, default='success')  # success, error, pending

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExtensionSettings(Base):
    __tablename__ = "extension_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False, index=True)

    auto_sync = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    response_style = Column(String, default='professional')  # professional, friendly, custom
    custom_response_template = Column(Text)

    max_applications_per_day = Column(Integer, default=10)
    supported_platforms = Column(JSON, default=['linkedin', 'indeed', 'glassdoor'])
    ai_model_preference = Column(String, default='gpt-4o-mini')
    sync_frequency = Column(String, default='real-time')  # real-time, hourly, daily, manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DocumentVector(Base):
    __tablename__ = "document_vectors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)

    content_chunk = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(String, nullable=False)  # JSON serialized vector

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Pydantic Schemas

```python
# backend/app/schemas/extension.py

from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class ExtensionAuthRequest(BaseModel):
    token: str
    extension_id: str
    version: str

class ExtensionAuthResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    permissions: List[str] = []
    refresh_token: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: str
    message: str

class DocumentSchema(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    category: str
    processed_status: str
    vector_status: str
    content_preview: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentSchema]
    total: int

class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    threshold: Optional[float] = 0.7

class KnowledgeSearchResult(BaseModel):
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeSearchResult]
    total: int

class ResponseGenerationRequest(BaseModel):
    question: str
    job_context: Optional[Dict[str, Any]] = {}
    response_style: Optional[str] = 'professional'
    max_length: Optional[int] = 500

class ResponseGenerationResponse(BaseModel):
    question: str
    response: str
    confidence: float
    word_count: int
    generated_at: datetime

class PageAnalysisRequest(BaseModel):
    page_type: str  # 'job_posting' or 'application_form'
    url: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = []
    job_context: Optional[Dict[str, Any]] = {}

class PageAnalysisResponse(BaseModel):
    page_type: str
    data: Dict[str, Any]
    confidence: float

class ActivitySchema(BaseModel):
    id: str
    type: str
    title: str
    description: Optional[str]
    url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ExtensionActivityResponse(BaseModel):
    activities: List[ActivitySchema]
    total: int
    limit: int
    offset: int

class ExtensionStatsResponse(BaseModel):
    total_job_analyses: int
    total_responses_generated: int
    documents_processed: int
    avg_compatibility_score: float
    last_30_days: Dict[str, int]

class ExtensionSettingsSchema(BaseModel):
    auto_sync: bool
    notifications_enabled: bool
    response_style: str
    custom_response_template: Optional[str]
    max_applications_per_day: int
    supported_platforms: List[str]
    ai_model_preference: str
    sync_frequency: str

    class Config:
        from_attributes = True

class ExtensionSettingsUpdate(BaseModel):
    auto_sync: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    response_style: Optional[str] = None
    custom_response_template: Optional[str] = None
    max_applications_per_day: Optional[int] = None
    supported_platforms: Optional[List[str]] = None
    ai_model_preference: Optional[str] = None
    sync_frequency: Optional[str] = None
```

## WebSocket Implementation

```python
# backend/app/api/v1/websocket/extension.py

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
import logging

from app.core.security import get_current_user_websocket

logger = logging.getLogger(__name__)

class ExtensionConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Extension WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Extension WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_to_user(self, user_id: str, data: dict):
        await self.send_personal_message(data, user_id)

extension_manager = ExtensionConnectionManager()

async def extension_websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    try:
        # Verify user authentication
        user = await get_current_user_websocket(websocket, user_id)
        if not user:
            await websocket.close(code=1008)
            return

        await extension_manager.connect(websocket, user_id)

        # Send initial connection message
        await extension_manager.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

        try:
            while True:
                # Listen for messages from extension
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await handle_extension_message(message, user_id)

        except WebSocketDisconnect:
            extension_manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        extension_manager.disconnect(user_id)

async def handle_extension_message(message: dict, user_id: str):
    """Handle messages from extension"""
    message_type = message.get("type")

    if message_type == "ping":
        await extension_manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    elif message_type == "job_analyzed":
        # Handle job analysis notification
        await extension_manager.send_personal_message({
            "type": "job_analysis_complete",
            "data": message.get("data"),
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    elif message_type == "extension_error":
        # Handle extension error
        logger.error(f"Extension error for user {user_id}: {message.get('error')}")

# Function to send notifications to extension
async def notify_extension_user(user_id: str, notification_type: str, data: dict):
    """Send notification to extension user if connected"""
    await extension_manager.send_personal_message({
        "type": notification_type,
        "payload": data,
        "timestamp": datetime.utcnow().isoformat()
    }, user_id)
```

## Service Integrations

### Integration with Existing Services

```python
# Update existing job extraction to notify extension
# backend/app/api/v1/endpoints/job_extraction.py

@router.post("/extract-from-url", response_model=JobExtractionResponse)
async def extract_job_from_url(
    request: JobExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # ... existing extraction logic ...

    # Add extension notification
    background_tasks.add_task(
        notify_extension_user,
        request.user_id,
        "job_analyzed",
        {
            "id": job_listing.id,
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "compatibility_score": compatibility_score,
            "url": str(request.url)
        }
    )

    return job_extraction_response
```

## Required Dependencies

```bash
# Add to requirements.txt
pypdf2==3.0.1          # PDF processing
python-docx==0.8.11    # DOCX processing
mammoth==1.6.0         # Advanced DOCX processing
pgvector==0.2.4        # PostgreSQL vector extension
websockets==11.0       # WebSocket support
asyncpg==0.28.0        # Async PostgreSQL driver
sentence-transformers==2.2.2  # Alternative embeddings
```

## Database Migrations

```python
# Create Alembic migration
alembic revision --autogenerate -m "Add extension tables"

# Migration content
def upgrade():
    # Create extension tables
    op.create_table('extension_documents', ...)
    op.create_table('extension_activities', ...)
    op.create_table('extension_settings', ...)
    op.create_table('document_vectors', ...)

    # Create indexes
    op.create_index('ix_extension_documents_user_id', 'extension_documents', ['user_id'])
    op.create_index('ix_extension_activities_user_id', 'extension_activities', ['user_id'])

    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
```

This backend API specification provides a complete foundation for supporting the browser extension functionality while leveraging the existing JobFlow Pro infrastructure and maintaining consistency with current patterns.