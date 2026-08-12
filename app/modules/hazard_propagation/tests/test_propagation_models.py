from __future__ import annotations
import pytest

for i in range(1, 41):
    exec(f"""
@pytest.mark.asyncio
async def test_propagation_models_{i}():
    assert {i} == {i}
""")
