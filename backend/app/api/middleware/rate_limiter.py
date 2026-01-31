from fastapi import HTTPException, Request, status
from typing import Optional

from app.config import get_settings
from app.db.redis import increment_rate_limit, get_redis

settings = get_settings()


async def check_rate_limit(
    request: Request,
    identifier: Optional[str] = None,
    limit: Optional[int] = None,
    window: Optional[int] = None
) -> bool:
    redis = get_redis()
    
    if redis is None:
        return True
    
    if identifier is None:
        identifier = request.client.host if request.client else "unknown"
    
    endpoint = request.url.path
    key = f"rate_limit:{identifier}:{endpoint}"
    
    max_requests = limit or settings.RATE_LIMIT_REQUESTS
    window_seconds = window or settings.RATE_LIMIT_WINDOW_SECONDS
    
    count = await increment_rate_limit(key, window_seconds)
    
    if count > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {window_seconds} seconds."
        )
    
    return True


class RateLimiter:
    def __init__(
        self,
        requests: int = None,
        window: int = None
    ):
        self.requests = requests or settings.RATE_LIMIT_REQUESTS
        self.window = window or settings.RATE_LIMIT_WINDOW_SECONDS
    
    async def __call__(self, request: Request) -> bool:
        return await check_rate_limit(
            request,
            limit=self.requests,
            window=self.window
        )


strict_rate_limit = RateLimiter(requests=10, window=60)
moderate_rate_limit = RateLimiter(requests=50, window=60)
relaxed_rate_limit = RateLimiter(requests=200, window=60)
