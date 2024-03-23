__all__ = ("router", )

from aiogram import Router
from .xo import router as xo_router

router = Router(name=__name__)
router.include_router(xo_router)
router.pre_checkout_query()
