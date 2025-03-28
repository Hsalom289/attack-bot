import os
import csv
import asyncio
import random
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest

# Sozlamalar
API_ID = 16072756  # my.telegram.org dan olingan API ID
API_HASH = '5fc7839a0d020c256e5c901cebd21bb7'  # my.telegram.org dan olingan API HASH
BOT_USERNAME = '@ZarReklama_bot'

class TelegramAttackBot:
    def __init__(self):
        self.clients = {}
        self.last_message_id = {}  # Har bir telefon uchun oxirgi xabar ID sini saqlash

    def _get_accounts(self):
        """phone.csv dan raqamlarni olish"""
        accounts = []
        try:
            with open('phone.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or 'phone' not in reader.fieldnames:
                    print("Xatolik: phone.csv da kerakli ustunlar yo'q")
                    return accounts
                
                for row in reader:
                    if row.get('phone', '').strip():
                        accounts.append({'phone': row['phone'].strip()})
        except FileNotFoundError:
            print("phone.csv topilmadi")
        except Exception as e:
            print(f"phone.csv o'qishda xatolik: {str(e)}")
        return accounts

    async def _check_sessions(self):
        """Barcha sessiyalarni tekshirish"""
        print("\n=== Sessiyalarni Tekshirish ===\n")
        accounts = self._get_accounts()
        valid_accounts = []
        
        for account in accounts:
            phone = account['phone']
            session_file = f'sessions/{phone}'
            client = None
            
            if not os.path.exists(f"{session_file}.session"):
                print(f"{phone} uchun sessiya mavjud emas")
                continue
            
            try:
                client = TelegramClient(session_file, API_ID, API_HASH)
                await client.connect()
                
                if await client.is_user_authorized():
                    print(f"✅ {phone} sessiyasi faol")
                    valid_accounts.append(account)
                    self.clients[phone] = client
                    # Oxirgi xabar ID sini boshlang‘ich qiymat sifatida olish
                    async for msg in client.iter_messages(BOT_USERNAME, limit=1):
                        self.last_message_id[phone] = msg.id if msg else 0
                else:
                    print(f"❌ {phone} sessiyasi chiqib ketgan")
            except Exception as e:
                print(f"{phone} sessiyasini tekshirishda xatolik: {str(e)}")
            finally:
                if client and client.is_connected():
                    await client.disconnect()
        
        return valid_accounts

    async def _wait_for_bot_response(self, client, phone):
        """Botdan yangi javobni kutish"""
        while True:
            try:
                async for message in client.iter_messages(BOT_USERNAME, limit=1, min_id=self.last_message_id[phone]):
                    if message and message.id > self.last_message_id[phone]:
                        self.last_message_id[phone] = message.id  # Yangi xabar ID sini yangilash
                        print(f"{phone}: Bot javob berdi - {message.text[:50] if message.text else 'Media'}...")
                        return True
                print(f"{phone}: Bot javobini kutmoqda...")
                await asyncio.sleep(5)  # 5 soniya kutib, qayta tekshiradi
            except Exception as e:
                print(f"{phone}: Bot javobini kutishda xatolik - {str(e)}")
                await asyncio.sleep(5)

    async def attack_bot(self, phone):
        """Botga hujum qilish jarayoni"""
        session_file = f'sessions/{phone}'
        client = None
        
        try:
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"{phone} hisobi avtorizatsiyadan o'tmagan")
                return
            
            print(f"\n{phone} bilan {BOT_USERNAME} ga hujum boshlandi")
            
            # 1-qadam: Botga /start yuborish
            await client.send_message(BOT_USERNAME, '/start')
            if not await self._wait_for_bot_response(client, phone):
                return  # Bot javob bermasa, davom etmaydi
            
            # 2-qadam: Kanallarga obuna bo'lish
            channels = ['@Zarafshon_Yangiliklar24', '@Zarafshon_Reklama']
            for channel in channels:
                try:
                    channel_entity = await client.get_entity(channel)
                    await client(JoinChannelRequest(channel_entity))
                    print(f"{phone}: {channel} ga obuna bo‘lindi")
                    await asyncio.sleep(random.uniform(1, 2))
                except Exception as e:
                    print(f"{phone}: {channel} ga obuna bo‘lishda xatolik - {str(e)}")
            
            # 3-qadam: "✅A'zo bo'ldim✅" tugmasini bosish
            async for message in client.iter_messages(BOT_USERNAME, limit=1):
                if message.reply_markup and "✅A'zo bo'ldim✅" in str(message.reply_markup):
                    try:
                        await client(GetBotCallbackAnswerRequest(
                            peer=BOT_USERNAME,
                            msg_id=message.id,
                            data=b'am9pbmVk'
                        ))
                        print(f"{phone}: ✅A'zo bo'ldim✅ bosildi")
                    except Exception as e:
                        print(f"{phone}: ✅A'zo bo'ldim✅ bosishda xatolik - {str(e)}")
                    break
                else:
                    print(f"{phone}: ✅A'zo bo'ldim✅ tugmasi topilmadi")
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 4-qadam: /start qayta yuborish
            await client.send_message(BOT_USERNAME, '/start')
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 5-qadam: Birinchi callback tugmasini bosish
            async for message in client.iter_messages(BOT_USERNAME, limit=1):
                if message.reply_markup:
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if button.__class__.__name__ == "KeyboardButtonCallback":
                                try:
                                    await client(GetBotCallbackAnswerRequest(
                                        peer=BOT_USERNAME,
                                        msg_id=message.id,
                                        data=button.data
                                    ))
                                    print(f"{phone}: Birinchi callback tugmasi bosildi")
                                except Exception as e:
                                    print(f"{phone}: Callback tugmasini bosishda xatolik - {str(e)}")
                                break
                        else:
                            continue
                        break
                    break
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 6-qadam: "📢 E'lon berish" knopkasini bosish
            await client.send_message(BOT_USERNAME, '📢 E\'lon berish')
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 7-qadam: "📝 Boshqa e'lonlar" knopkasini bosish
            await client.send_message(BOT_USERNAME, '📝 Boshqa e\'lonlar')
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 8-qadam: @zarafshan_uy guruhidan rasmlarni olish va yuborish
            group = await client.get_entity('@zarafshan_uy')
            print(f"{phone}: @zarafshan_uy guruhiga ulandi")
            messages = [msg async for msg in client.iter_messages(group, limit=50) if msg.photo]
            
            if messages:
                # Birinchi rasmni yuborish
                random_photo = random.choice(messages)
                await client.send_file(BOT_USERNAME, random_photo.photo)
                print(f"{phone}: {BOT_USERNAME} ga rasm yuborildi")
                if not await self._wait_for_bot_response(client, phone):
                    return
                
                # Ikkinchi rasmni yuborish
                random_photo = random.choice(messages)
                await client.send_file(BOT_USERNAME, random_photo.photo)
                print(f"{phone}: {BOT_USERNAME} ga yana rasm yuborildi")
                if not await self._wait_for_bot_response(client, phone):
                    return
            else:
                print(f"{phone}: @zarafshan_uy da rasm topilmadi")
            
            # 9-qadam: "✅ Rasmlarni tasdiqlash" bosish
            await client.send_message(BOT_USERNAME, '✅ Rasmlarni tasdiqlash')
            if not await self._wait_for_bot_response(client, phone):
                return
            
            # 10-qadam: Har bir javobdan keyin bitta harakat
            while True:
                await client.send_message(BOT_USERNAME, '📝 Boshqa e\'lonlar')
                print(f"{phone}: 📝 Boshqa e'lonlar bosildi")
                if not await self._wait_for_bot_response(client, phone):
                    return
                
                if messages:
                    random_photo = random.choice(messages)
                    await client.send_file(BOT_USERNAME, random_photo.photo)
                    print(f"{phone}: {BOT_USERNAME} ga rasm yuborildi")
                    if not await self._wait_for_bot_response(client, phone):
                        return
                
                if messages:
                    random_photo = random.choice(messages)
                    await client.send_file(BOT_USERNAME, random_photo.photo)
                    print(f"{phone}: {BOT_USERNAME} ga yana rasm yuborildi")
                    if not await self._wait_for_bot_response(client, phone):
                        return
                
        except errors.FloodWaitError as e:
            print(f"{phone}: Flood chegarasi - {e.seconds} soniya kutish kerak")
            await asyncio.sleep(min(e.seconds, 10))
        except Exception as e:
            print(f"{phone}: Hujum jarayonida xatolik - {str(e)}")
        finally:
            if client and client.is_connected():
                await client.disconnect()

    async def start_attack(self):
        """Barcha akkauntlar bilan parallel hujum boshlash"""
        print("\n=== Botga Hujum ===\n")
        
        valid_accounts = await self._check_sessions()
        if not valid_accounts:
            print("Hech qanday faol sessiya yo'q")
            return
        
        tasks = []
        for account in valid_accounts:
            phone = account['phone']
            task = asyncio.create_task(self.attack_bot(phone))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

async def main():
    bot = TelegramAttackBot()
    await bot.start_attack()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDastur foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        print(f"Jiddiy xatolik: {str(e)}")
