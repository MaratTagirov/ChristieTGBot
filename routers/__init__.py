__all__ = ("router", )

from aiogram import Router

from .commands_routers import router as commands_router
from .xo_routers import router as xo_router
router = Router(name=__name__)

router.include_router(commands_router)
router.include_router(xo_router)

