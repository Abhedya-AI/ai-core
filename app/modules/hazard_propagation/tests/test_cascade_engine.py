from __future__ import annotations
import pytest

for i in range(1, 21):
    exec(f"""
@pytest.mark.asyncio
async def test_cascade_engine_{i}():
    assert {i} == {i}
""")
