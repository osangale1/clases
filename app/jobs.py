from typing import Optional

from app import config
from app.schemas import EstadoTarea


class JobStore:
    def __init__(self, cliente):
        self.cliente = cliente

    async def guardar(self, estado: EstadoTarea) -> None:
        await self.cliente.set(f"job:{estado.job_id}", estado.model_dump_json(), ex=config.JOB_TTL_SEGUNDOS)

    async def obtener(self, job_id: str) -> Optional[EstadoTarea]:
        data = await self.cliente.get(f"job:{job_id}")
        return EstadoTarea.model_validate_json(data) if data else None
