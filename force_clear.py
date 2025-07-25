#!/usr/bin/env python3
"""
Мощный скрипт для принудительной очистки webhook и updates
"""

import asyncio
import aiohttp
from aiogram import Bot
from config import Config

async def force_clear():
    """Принудительная очистка всех webhook и updates"""
    bot = Bot(Config.BOT_TOKEN)
    
    print("🧹 Начинаю принудительную очистку...")
    
    try:
        # 1. Удаляем webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удален")
        
        # 2. Очищаем все pending updates
        updates = await bot.get_updates(offset=-1, limit=100)
        if updates:
            print(f"✅ Очищено {len(updates)} pending updates")
        else:
            print("✅ Pending updates не найдены")
        
        # 3. Дополнительная очистка через прямые API вызовы
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/deleteWebhook"
            params = {"drop_pending_updates": True}
            
            async with session.post(url, params=params) as response:
                if response.status == 200:
                    print("✅ Дополнительная очистка webhook выполнена")
                else:
                    print(f"⚠️ Дополнительная очистка webhook: {response.status}")
        
        print("🎉 Очистка завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(force_clear()) 