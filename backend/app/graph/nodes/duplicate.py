from typing import Dict, Any, List
import logging
import uuid

from sqlalchemy import select, String, func
from pgvector.sqlalchemy import Vector

from app.graph.state import CopilotState
from app.db.session import async_session_factory
from app.db.models import Complaint, DuplicateStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy initialization of the model to avoid blocking start-up
# but keeping it in memory for subsequent requests.
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Lightweight model, typically takes a few seconds to load
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load sentence_transformers model: {e}")
            raise
    return _embedding_model

def normalize_text(form: dict) -> str:
    """
    Creates a lightweight normalized text representation of the complaint 
    by concatenating key fields and lowercasing.
    """
    parts = []
    if form.get('detailed_description'):
        parts.append(form['detailed_description'].strip())
    if form.get('product_name'):
        parts.append(f"Product: {form['product_name'].strip()}")
    if form.get('complaint_type'):
        parts.append(f"Type: {form['complaint_type'].strip()}")
    if form.get('batch_lot_number'):
        parts.append(f"Batch: {form['batch_lot_number'].strip()}")
        
    text = " ".join(parts).lower()
    # Simple whitespace normalization
    text = " ".join(text.split())
    return text

async def duplicate_node(state: CopilotState) -> CopilotState:
    """
    Duplicate detection node.
    Compares the normalized text of the current merged form against historical
    complaints in the database using vector similarity.
    """
    # If the user is editing an existing complaint and the intent isn't a new one,
    # or if we don't have enough data yet, we could skip. But let's run it anyway 
    # and just exclude the current complaint_id from the results.
    
    merged_form = state.get("merged_form", {})
    if not merged_form.get("detailed_description") and not merged_form.get("product_name"):
        # Nothing meaningful to compare yet
        return {
            "duplicate_status": DuplicateStatus.UNIQUE.value,
            "duplicate_matches": []
        }

    try:
        normalized_text = normalize_text(merged_form)
        if not normalized_text:
            return {
                "duplicate_status": DuplicateStatus.UNIQUE.value,
                "duplicate_matches": []
            }

        # 1. Generate Embedding
        model = get_embedding_model()
        # sentence-transformers outputs a numpy array
        embedding_vector = model.encode(normalized_text)
        
        # 2. Query Database
        async with async_session_factory() as db:
            query = (
                select(Complaint)
                .where(Complaint.embedding.is_not(None))
            )
            
            # Exclude current complaint if we are editing
            if state.get("complaint_id"):
                try:
                    current_uuid = uuid.UUID(state["complaint_id"])
                    query = query.where(Complaint.id != current_uuid)
                except ValueError:
                    pass
            
            # Use cosine distance (<=>). Cosine similarity = 1 - cosine_distance.
            # We want highest similarity, so we order by distance ASC.
            distance_expr = Complaint.embedding.cosine_distance(embedding_vector)
            
            query = (
                query
                .order_by(distance_expr)
                .limit(settings.TOP_K_DUPLICATES)
            )
            
            result = await db.execute(query)
            candidates = result.scalars().all()
            
            # 3. Compute Similarity and Classify
            matches = []
            best_status = DuplicateStatus.UNIQUE
            
            # We need to manually calculate or re-evaluate the similarity since we used distance
            # Let's compute cosine similarity for the matches
            for candidate in candidates:
                if not candidate.embedding:
                    continue
                    
                import numpy as np
                # Cosine similarity between two vectors
                v1 = np.array(embedding_vector)
                v2 = np.array(candidate.embedding)
                
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                if norm1 == 0 or norm2 == 0:
                    similarity = 0.0
                else:
                    similarity = float(np.dot(v1, v2) / (norm1 * norm2))
                
                if similarity >= settings.DUPLICATE_THRESHOLD:
                    if best_status != DuplicateStatus.DUPLICATE:
                        best_status = DuplicateStatus.DUPLICATE
                elif similarity >= settings.POSSIBLE_DUPLICATE_THRESHOLD:
                    if best_status == DuplicateStatus.UNIQUE:
                        best_status = DuplicateStatus.POSSIBLE_DUPLICATE
                        
                matches.append({
                    "similarity_score": round(similarity, 4),
                    "matched_complaint_id": str(candidate.id),
                    "matched_complaint_summary": candidate.detailed_description[:200] + "..." if candidate.detailed_description and len(candidate.detailed_description) > 200 else candidate.detailed_description
                })

            # Sort matches by highest similarity first
            matches.sort(key=lambda x: x["similarity_score"], reverse=True)

            return {
                "duplicate_status": best_status.value,
                "duplicate_matches": matches
            }

    except Exception as e:
        logger.error(f"Duplicate detection failed: {e}", exc_info=True)
        # Safe fallback
        return {
            "duplicate_status": DuplicateStatus.UNIQUE.value,
            "duplicate_matches": []
        }
