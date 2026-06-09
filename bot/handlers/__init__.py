from aiogram.filters import Command
"""Хендлеры бота"""
from . import start
from . import tarot
from . import payment
from . import referral
from . import history

__all__ = ['start', 'tarot', 'payment', 'referral', 'history']
