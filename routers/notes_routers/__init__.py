__all__ = ("router", )

from aiogram import Router
from .notes import router as notes_router

router = Router(name=__name__)
router.include_router(notes_router)
