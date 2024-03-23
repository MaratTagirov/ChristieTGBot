__all__ = ("router", )

from aiogram import Router

from .commands_routers import router as commands_router
from .notes_routers import router as notes_router
from .game_routers import router as game_router

router = Router(name=__name__)

router.include_router(commands_router)
router.include_router(notes_router)
router.include_router(game_router)
