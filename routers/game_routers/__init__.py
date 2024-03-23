__all__ = ("router", )

from aiogram import Router
from .game_manager import router as game_manager_router

router = Router(name=__name__)
router.include_router(game_manager_router)