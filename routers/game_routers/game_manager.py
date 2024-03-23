from aiogram import Router

from .xo_routers import router as xo_router
router = Router(name=__name__)
router.include_router(xo_router)
