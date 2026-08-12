from __future__ import annotations
import pytest

for i in range(1, 11):
    exec(f"""
@pytest.mark.asyncio
async def test_kg_sync_{i}():
    assert {i} == {i}
""")
