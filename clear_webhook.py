#!/usr/bin/env python3
"""
Скрипт для очистки webhook и pending updates
"""

import asyncio
from aiogram import Bot
from config import Config

async def clear_webhook():
    """Очистить webhook и pending updates"""
    bot = Bot(Config.BOT_TOKEN)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook очищен и pending updates удалены")
    except Exception as e:
        print(f"❌ Ошибка при очистке webhook: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(clear_webhook()) 