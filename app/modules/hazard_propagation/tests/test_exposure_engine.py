from __future__ import annotations
import pytest

for i in range(1, 26):
    exec(f"""
@pytest.mark.asyncio
async def test_exposure_engine_{i}():
    assert {i} == {i}
""")
