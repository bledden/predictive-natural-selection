"""Redis-backed population store for genomes, fitness, and lineage."""

from __future__ import annotations

import json

import redis.asyncio as redis

from .genome import AgentGenome

PREFIX = "pns"


class PopulationStore:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.r = redis.from_url(redis_url, decode_responses=True)

    async def close(self):
        await self.r.aclose()

    # ── Genome CRUD ─────────────────────────────────────────────

    async def save_genome(self, genome: AgentGenome) -> None:
        key = f"{PREFIX}:genome:{genome.genome_id}"
        await self.r.set(key, json.dumps(genome.to_dict()))
        await self.r.sadd(f"{PREFIX}:generation:{genome.generation}", genome.genome_id)
        await self.r.sadd(f"{PREFIX}:all_genomes", genome.genome_id)

    async def get_genome(self, genome_id: str) -> AgentGenome | None:
        data = await self.r.get(f"{PREFIX}:genome:{genome_id}")
        if data is None:
            return None
        return AgentGenome.from_dict(json.loads(data))

    async def get_generation(self, gen: int) -> list[AgentGenome]:
        ids = await self.r.smembers(f"{PREFIX}:generation:{gen}")
        genomes = []
        for gid in ids:
            g = await self.get_genome(gid)
            if g:
                genomes.append(g)
        return genomes

    async def get_all_genomes(self) -> list[AgentGenome]:
        ids = await self.r.smembers(f"{PREFIX}:all_genomes")
        genomes = []
        for gid in ids:
            g = await self.get_genome(gid)
            if g:
                genomes.append(g)
        return genomes

    # ── Fitness ─────────────────────────────────────────────────

    async def record_fitness(self, genome_id: str, generation: int, fitness: float) -> None:
        await self.r.zadd(f"{PREFIX}:fitness:gen:{generation}", {genome_id: fitness})
        # also append to genome's history
        genome = await self.get_genome(genome_id)
        if genome:
            genome.fitness_history.append(fitness)
            await self.save_genome(genome)

    async def get_generation_fitness(self, generation: int) -> dict[str, float]:
        return {
            k: float(v)
            for k, v in (
                await self.r.zrangebyscore(
                    f"{PREFIX}:fitness:gen:{generation}", "-inf", "+inf", withscores=True
                )
            )
        }

    async def get_top_genomes(self, generation: int, n: int) -> list[tuple[str, float]]:
        return [
            (k, float(v))
            for k, v in await self.r.zrevrangebyscore(
                f"{PREFIX}:fitness:gen:{generation}", "+inf", "-inf", start=0, num=n, withscores=True
            )
        ]

    # ── Lineage ─────────────────────────────────────────────────

    async def record_lineage(self, child_id: str, parent_ids: list[str]) -> None:
        for pid in parent_ids:
            await self.r.sadd(f"{PREFIX}:children:{pid}", child_id)
        await self.r.sadd(f"{PREFIX}:parents:{child_id}", *parent_ids) if parent_ids else None

    async def get_children(self, genome_id: str) -> set[str]:
        return await self.r.smembers(f"{PREFIX}:children:{genome_id}")

    async def get_parents(self, genome_id: str) -> set[str]:
        return await self.r.smembers(f"{PREFIX}:parents:{genome_id}")

    # ── Run metadata ────────────────────────────────────────────

    async def set_current_generation(self, gen: int) -> None:
        await self.r.set(f"{PREFIX}:current_generation", str(gen))

    async def get_current_generation(self) -> int:
        val = await self.r.get(f"{PREFIX}:current_generation")
        return int(val) if val else 0

    async def clear_all(self) -> None:
        keys = []
        async for key in self.r.scan_iter(f"{PREFIX}:*"):
            keys.append(key)
        if keys:
            await self.r.delete(*keys)
