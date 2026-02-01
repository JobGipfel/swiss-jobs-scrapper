"""
Health check endpoints.
"""

from fastapi import APIRouter

from swiss_jobs_scraper.providers import list_providers, get_provider


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Check overall API health.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "swiss-jobs-scraper",
        "version": "1.0.0",
    }


@router.get("/health/providers")
async def providers_health():
    """
    Check health of all job providers.
    
    Returns:
        Health status for each provider
    """
    results = []
    
    for name in list_providers():
        provider_cls = get_provider(name)
        try:
            async with provider_cls() as provider:
                health = await provider.health_check()
                results.append({
                    "provider": health.provider,
                    "status": health.status.value,
                    "latency_ms": health.latency_ms,
                    "message": health.message,
                })
        except Exception as e:
            results.append({
                "provider": name,
                "status": "error",
                "message": str(e),
            })
    
    return {"providers": results}
