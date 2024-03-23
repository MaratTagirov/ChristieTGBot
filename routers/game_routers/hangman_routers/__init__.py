__all__ = ("router", )

from aiogram import Router

from .hangman import router as hagman_router

router = Router(name=__name__)

router.include_router(hagman_router)
