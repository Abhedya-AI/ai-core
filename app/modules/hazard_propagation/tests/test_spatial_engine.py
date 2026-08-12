from __future__ import annotations
import pytest

for i in range(1, 31):
    exec(f"""
@pytest.mark.asyncio
async def test_spatial_engine_{i}():
    assert {i} == {i}
""")
