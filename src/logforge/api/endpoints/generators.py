from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from logforge.core.engine import GenerationEngine

router = APIRouter(prefix="/api/generators", tags=["generators"])


def get_engine(request: Request) -> GenerationEngine:
    return request.app.state.generation_engine


@router.get("", response_model=List[Dict[str, object]])
def list_generators(engine: GenerationEngine = Depends(get_engine)) -> List[Dict[str, object]]:
    return engine.list_generators()


@router.get("/{name}", response_model=Dict[str, object])
def get_generator(name: str = Path(...), engine: GenerationEngine = Depends(get_engine)) -> Dict[str, object]:
    try:
        return engine.get_generator(name).snapshot()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generator not found")


@router.post("/{name}/start", response_model=Dict[str, object])
def start_generator(name: str, engine: GenerationEngine = Depends(get_engine)) -> Dict[str, object]:
    try:
        return engine.start_generator(name)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generator not found")


@router.post("/{name}/stop", response_model=Dict[str, object])
def stop_generator(name: str, engine: GenerationEngine = Depends(get_engine)) -> Dict[str, object]:
    try:
        return engine.stop_generator(name)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generator not found")


@router.post("/{name}/restart", response_model=Dict[str, object])
def restart_generator(name: str, engine: GenerationEngine = Depends(get_engine)) -> Dict[str, object]:
    try:
        return engine.restart_generator(name)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generator not found")
