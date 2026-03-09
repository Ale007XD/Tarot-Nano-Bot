from aiogram.filters import Command
"""Хендлеры бота"""
from . import start
from . import tarot
from . import payment
from . import referral

__all__ = ['start', 'tarot', 'payment', 'referral']
