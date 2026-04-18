"""
FastAPI routes for Copy Generation operations
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from generate.infer import CopyGenerator, Evaluator, GenerationConfig
from api.database import GenerationRecord, LoRAModel, init_db, get_default_db_path

router = APIRouter(prefix="/api/generate", tags=["generate"])

_engine, _Session = None, None

# Model cache
_model_cache = {}


def get_session():
    global _engine, _Session
    if _Session is None:
        db_path = get_default_db_path()
        _engine, _Session = init_db(db_path)
    return _Session()


def get_generator(model_id: int) -> CopyGenerator:
    """Get or load generator for model_id"""
    if model_id in _model_cache:
        return _model_cache[model_id]

    session = get_session()
    model = session.query(LoRAModel).filter(LoRAModel.id == model_id).first()

    if not model or model.status != "completed":
        raise HTTPException(400, "Model not ready")

    generator = CopyGenerator(
        model_path=model.base_model,
        lora_path=model.lora_path
    )
    generator.load_model()

    _model_cache[model_id] = generator
    return generator


# Request/Response models
class GenerateRequest(BaseModel):
    model_id: int
    source_content: str
    industry_tag: Optional[str] = None
    copy_type: Optional[str] = None


class BatchGenerateRequest(BaseModel):
    model_id: int
    records: List[dict]
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9


class GenerateResponse(BaseModel):
    source_content: str
    generated_content: str
    industry_tag: Optional[str]
    copy_type: Optional[str]
    record_id: Optional[int] = None


@router.post("/text", response_model=GenerateResponse)
async def generate_single(request: GenerateRequest):
    """Generate a single ad copy"""
    try:
        generator = get_generator(request.model_id)
    except Exception as e:
        raise HTTPException(400, f"Failed to load model: {str(e)}")

    # Generate
    config = GenerationConfig(
        max_new_tokens=256,
        temperature=request.temperature if hasattr(request, 'temperature') else 0.7
    ) if hasattr(request, 'temperature') else None

    result = generator.generate_single(
        source_content=request.source_content,
        industry_tag=request.industry_tag,
        copy_type=request.copy_type,
        config=config
    )

    # Save to history
    session = get_session()
    record = GenerationRecord(
        model_id=request.model_id,
        source_content=request.source_content,
        generated_content=result["generated_content"],
        industry_tag=request.industry_tag,
        copy_type=request.copy_type
    )
    session.add(record)
    session.commit()

    return GenerateResponse(
        source_content=request.source_content,
        generated_content=result["generated_content"],
        industry_tag=request.industry_tag,
        copy_type=request.copy_type,
        record_id=record.id
    )


@router.post("/batch")
async def generate_batch(request: BatchGenerateRequest):
    """Generate multiple ad copies"""
    try:
        generator = get_generator(request.model_id)
    except Exception as e:
        raise HTTPException(400, f"Failed to load model: {str(e)}")

    # Override generation config
    if request.max_new_tokens or request.temperature:
        config = GenerationConfig(
            max_new_tokens=request.max_new_tokens or 256,
            temperature=request.temperature or 0.7,
            top_p=request.top_p or 0.9
        )
    else:
        config = None

    # Generate
    results = generator.generate_batch(
        records=request.records,
        config=config
    )

    # Save to history
    session = get_session()
    saved_records = []
    for i, result in enumerate(results):
        record = GenerationRecord(
            model_id=request.model_id,
            source_content=result["source_content"],
            generated_content=result["generated_content"],
            industry_tag=result.get("industry_tag"),
            copy_type=result.get("copy_type")
        )
        session.add(record)
        saved_records.append(record.id)

    session.commit()

    return {
        "results": results,
        "record_ids": saved_records,
        "count": len(results)
    }


@router.get("/history")
async def get_history(
    model_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get generation history"""
    session = get_session()

    query = session.query(GenerationRecord)
    if model_id:
        query = query.filter(GenerationRecord.model_id == model_id)

    total = query.count()
    records = query.order_by(GenerationRecord.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "model_id": r.model_id,
                "source_content": r.source_content,
                "generated_content": r.generated_content,
                "is_edited": r.is_edited,
                "bleu_score": r.bleu_score,
                "rouge_score": r.rouge_score,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]
    }


@router.put("/{record_id}")
async def update_record(record_id: int, edited_content: str):
    """Update an edited generation record"""
    session = get_session()
    record = session.query(GenerationRecord).filter(GenerationRecord.id == record_id).first()

    if not record:
        raise HTTPException(404, "Record not found")

    record.generated_content = record.generated_content  # Keep original
    record.edited_content = edited_content
    record.is_edited = True
    session.commit()

    return {"message": "Record updated", "id": record_id}


@router.post("/evaluate")
async def evaluate_records(record_ids: List[int]):
    """Evaluate generation quality for records"""
    session = get_session()
    records = session.query(GenerationRecord).filter(GenerationRecord.id.in_(record_ids)).all()

    if not records:
        raise HTTPException(404, "No records found")

    # Collect results
    results_dict = {}
    for r in records:
        results_dict[r.id] = {
            "source_content": r.source_content,
            "generated_content": r.generated_content,
            "target_content": r.edited_content or r.generated_content,
            "industry_tag": r.industry_tag
        }

    # Evaluate
    evaluator = Evaluator()
    eval_results = evaluator.evaluate_batch(list(results_dict.values()))

    # Update records with scores
    for i, r in enumerate(records):
        r.bleu_score = eval_results["bleu"]["scores"][i]
        r.rouge_score = eval_results["rouge_l"]["scores"][i]

    session.commit()

    return {
        "bleu_mean": eval_results["bleu"]["mean"],
        "rouge_l_mean": eval_results["rouge_l"]["mean"],
        "count": len(records)
    }


@router.get("/stats")
async def get_generation_stats():
    """Get generation statistics"""
    session = get_session()

    total = session.query(GenerationRecord).count()
    edited = session.query(GenerationRecord).filter(GenerationRecord.is_edited == True).count()

    avg_bleu = session.query(GenerationRecord).filter(
        GenerationRecord.bleu_score.isnot(None)
    ).all()

    avg_bleu_val = sum(r.bleu_score for r in avg_bleu) / len(avg_bleu) if avg_bleu else 0

    avg_rouge = session.query(GenerationRecord).filter(
        GenerationRecord.rouge_score.isnot(None)
    ).all()

    avg_rouge_val = sum(r.rouge_score for r in avg_rouge) / len(avg_rouge) if avg_rouge else 0

    return {
        "total_generations": total,
        "edited_count": edited,
        "avg_bleu": avg_bleu_val,
        "avg_rouge_l": avg_rouge_val
    }
