import pytest

@pytest.fixture(
    params=[
        pytest.param("asyncio"),
    ]
)
def anyio_backend(request):
    return request.param
