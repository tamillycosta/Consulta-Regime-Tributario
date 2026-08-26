import uuid
import asyncio
import httpx
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response

from app.services.excel_service import parse_excel_or_csv, generate_export_excel
from app.services.cnpj_service import query_single_cnpj

router = APIRouter(prefix="/api", tags=["consulta"])

# In-memory store for active jobs (in production can use Redis/DB)
JOBS: Dict[str, Dict[str, Any]] = {}

async def process_job_background(job_id: str, items: List[Dict[str, str]]):
    job = JOBS.get(job_id)
    if not job:
        return

    results = []
    total = len(items)

    async with httpx.AsyncClient(headers={"User-Agent": "ConsultaRegimeTributario/1.0"}) as client:
        for idx, item in enumerate(items):
            res = await query_single_cnpj(client, item["cnpj"], item.get("nome", ""))
            results.append(res)
            job["processed"] = idx + 1
            job["results"] = results
            # Small non-blocking yield for async loop
            await asyncio.sleep(0.01)

    job["status"] = "completed"
    job["results"] = results
    # Cache generated excel bytes for instant download
    job["excel_bytes"] = generate_export_excel(results)

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    content = await file.read()
    try:
        items = parse_excel_or_csv(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler a planilha: {str(e)}")

    if not items:
        raise HTTPException(status_code=400, detail="Nenhum CNPJ válido foi encontrado na planilha.")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "total": len(items),
        "processed": 0,
        "results": [],
        "excel_bytes": None,
        "filename": file.filename
    }

    asyncio.create_task(process_job_background(job_id, items))

    return {
        "job_id": job_id,
        "total": len(items),
        "filename": file.filename,
        "message": f"Planilha recebida com sucesso! {len(items)} CNPJs identificados."
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    total = job["total"]
    processed = job["processed"]
    percentage = round((processed / total) * 100) if total > 0 else 0

    return {
        "job_id": job_id,
        "status": job["status"],
        "total": total,
        "processed": processed,
        "percentage": percentage
    }

@router.get("/export/{job_id}")
async def export_job_results(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    if job["status"] != "completed" or not job.get("excel_bytes"):
        raise HTTPException(status_code=400, detail="O processamento ainda não foi concluído.")

    return Response(
        content=job["excel_bytes"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=Resumo_Regime_Tributario_{job_id[:8]}.xlsx"
        }
    )
