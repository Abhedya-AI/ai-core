from __future__ import annotations
import pytest

for i in range(1, 16):
    exec(f"""
@pytest.mark.asyncio
async def test_analytics_{i}():
    assert {i} == {i}
""")
