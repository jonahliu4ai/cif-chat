import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import tempfile
import os

from services.cif_parser import CIFParser
from services.llm_client import LLMClient
from services.prompt_templates import STRUCTURE_DESCRIPTION
from config import get_llm_config

app = FastAPI(title="CIF-Chat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    structure_text: str


class ChatRequest(BaseModel):
    structure_data: str
    question: str


def get_llm():
    provider, config = get_llm_config()
    api_key = config.get("api_key", "")
    if not api_key:
        raise HTTPException(500, f"{provider.upper()}_API_KEY not set")
    return LLMClient(
        api_key=api_key,
        base_url=config.get("base_url"),
        model=config.get("model"),
    )


@app.get("/api/config")
async def get_config():
    provider, config = get_llm_config()
    return {
        "provider": provider,
        "model": config.get("model"),
        "base_url": config.get("base_url"),
        "api_key_set": bool(config.get("api_key")),
    }


@app.post("/api/parse")
async def parse_cif(file: UploadFile = File(...)):
    if not file.filename.endswith(".cif"):
        raise HTTPException(400, "Only .cif files accepted")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".cif") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    try:
        parser = CIFParser(tmp_path)
        return {
            "filename": file.filename,
            "basic_info": parser.get_basic_info(),
            "structure_text": parser.export_for_llm(),
        }
    finally:
        os.unlink(tmp_path)


@app.post("/api/analyze")
async def analyze_structure(req: AnalyzeRequest):
    llm = get_llm()
    try:
        analysis = await asyncio.to_thread(
            llm.chat,
            system_prompt="You are a helpful crystallography assistant.",
            user_prompt=STRUCTURE_DESCRIPTION.format(structure_data=req.structure_text),
            timeout=120,
        )
        return {"analysis": analysis}
    except Exception as e:
        return {
            "analysis": f"**AI 分析超时或失败**: {type(e).__name__}\n\n"
                        f"可能原因：\n"
                        f"1. LLM 服务响应慢，请稍后重试\n"
                        f"2. 当前模型负载高，可尝试更换模型\n\n"
                        f"原始结构数据已在上方显示，可基于数据手动分析。"
        }


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """真正的异步流式：首字符一到达就立即推送到前端"""
    import time
    llm = get_llm()
    
    prompt = STRUCTURE_DESCRIPTION.format(structure_data=req.structure_text)
    print(f"[API /analyze/stream] prompt 长度: {len(prompt)} 字")
    
    async def generate():
        try:
            async for text in llm.chat_stream_async(
                system_prompt="You are a helpful crystallography assistant.",
                user_prompt=prompt,
                timeout=120,
            ):
                yield text
        except Exception as e:
            yield f"\n\n[错误: {type(e).__name__}]"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


@app.post("/api/chat")
async def chat_about_structure(req: ChatRequest):
    prompt = f"""Based on the following crystal structure data, answer the user's question.

Structure Data:
{req.structure_data}

User Question: {req.question}
"""
    llm = get_llm()
    try:
        answer = await asyncio.to_thread(
            llm.chat,
            system_prompt="You are a crystallography expert. Answer concisely and accurately.",
            user_prompt=prompt,
            timeout=120,
        )
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"回答生成失败 ({type(e).__name__})，请稍后重试。"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
