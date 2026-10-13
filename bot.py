import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# ⚙️ معلومات البوت (تم وضع التوكن مالتك هنا)
# ==========================================
BOT_TOKEN = "8633899845:AAFlw0qze2Zp6DyLLcX42eGZTbCcuYMZe7Y"      # توكن بوتك
ADMIN_ID = 123456789                # الآيدي مالتك من userinfobot
SIM5_API_KEY = "حط_مفتاح_API_5sim"   # مفتاح الـ API من موقع 5sim

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

HEADERS = {
    'Authorization': f'Bearer {SIM5_API_KEY}',
    'Accept': 'application/json',
}

def get_balance():
    try:
        res = requests.get('https://5sim.net/v1/user/profile', headers=HEADERS)
        if res.status_code == 200:
            return res.json().get('balance', '0')
        return "خطأ بالاتصال"
    except Exception as e:
        return str(e)

def buy_number(country="usa", product="whatsapp"):
    url = f'https://5sim.net/v1/user/buy/activation/{country}/any/{product}'
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            return {"success": True, "id": data.get("id"), "phone": data.get("phone")}
        return {"success": False, "msg": res.text}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def check_sms(order_id):
    url = f'https://5sim.net/v1/user/check/{order_id}'
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            sms_list = res.json().get("sms", [])
            if sms_list:
                return {"received": True, "code": sms_list[-1].get("code")}
            return {"received": False, "msg": "الكود بعده ما واصل"}
        return {"received": False, "msg": "خطأ بالطلب"}
    except Exception as e:
        return {"received": False, "msg": str(e)}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📱 رقم واتساب (أمريكي)", callback_data="buy_wa_usa"),
        types.InlineKeyboardButton(text="✈️ رقم تليجرام (أمريكي)", callback_data="buy_tg_usa")
    )
    if message.from_user.id == ADMIN_ID:
        builder.row(
            types.InlineKeyboardButton(text="⚙️ فحص رصيد الموقع", callback_data="check_admin_balance")
        )

    msg = (
        f"أهلاً بيك يا {message.from_user.first_name} ببوت الأرقام!\n\n"
        "اختر التطبيق والخدمة من الأزرار الجوة:"
    )
    await message.answer(msg, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "check_admin_balance")
async def admin_balance(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("هذا الزر للأدمن فقط!", show_alert=True)
        return
    bal = get_balance()
    await callback.message.answer(f"💰 **رصيدك الحالي بالموقع:** `{bal}`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "buy_wa_usa")
async def buy_wa(callback: types.CallbackQuery):
    await callback.message.answer("⏳ جاري سحب الرقم من السيرفر...")
    result = buy_number(country="usa", product="whatsapp")
    if result["success"]:
        order_id = result["id"]
        phone = result["phone"]
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📩 جلب كود التفعيل (OTP)", callback_data=f"otp_{order_id}"))
        await callback.message.answer(
            f"✅ **تم جلب الرقم بنجاح!**\n\n"
            f"📞 **الرقم:** `{phone}`\n\n"
            "دخله بالواتساب وبعدين اضغط جلب الكود:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.answer(f"❌ لم يتم جلب الرقم:\n`{result['msg']}`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg_usa")
async def buy_tg(callback: types.CallbackQuery):
    await callback.message.answer("⏳ جاري سحب الرقم من السيرفر...")
    result = buy_number(country="usa", product="telegram")
    if result["success"]:
        order_id = result["id"]
        phone_num = result["phone"]
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📩 جلب كود التفعيل (OTP)", callback_data=f"otp_{order_id}"))
        await callback.message.answer(
            f"✅ **تم جلب الرقم بنجاح!**\n\n"
            f"📞 **الرقم:** `{phone_num}`\n\n"
            "دخله بالتليجرام وبعدين اضغط جلب الكود:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.answer(f"❌ لم يتم جلب الرقم:\n`{result['msg']}`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("otp_"))
async def check_otp(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    res = check_sms(order_id)
    if res["received"]:
        await callback.message.answer(f"🎉 **وصل الكود!**\n\n🔑 الرمز: `{res['code']}`", parse_mode="Markdown")
    else:
        await callback.message.answer(f"⏳ الكود بعده ما وصل.. انتظر ثواني واضغط مرة ثانية.\n({res['msg']})")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
