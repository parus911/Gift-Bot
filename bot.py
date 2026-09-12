import os
import math
import random
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.environ["8295184346:AAHG7eArQwaG1TJWGFaeWl4DjBU76DGtyXo"]

GIF_DURATION = 80

# Подарки на колесе
GIFTS = [
    "🎁 Подарок №1",
    "🎮 Steam",
    "🍕 Пицца",
    "💰 50 €",
    "🍺 Вечеринка",
    "🎧 Наушники",
    "🎁 Сюрприз",
    "💵 100 €",
]

# Если хочешь гарантированно получить определённый подарок:
# укажи здесь его название.
#
# Например:
# FORCED_GIFT = "💰 50 €"
#
# Если хочешь обычное случайное колесо:
# FORCED_GIFT = None

FORCED_GIFT = "🎁 Сюрприз"


# =========================
# ШРИФТ
# =========================

def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass

    return ImageFont.load_default()


# =========================
# СОЗДАНИЕ КОЛЕСА
# =========================

def create_wheel(angle, selected_index=None):
    size = 800
    center = size // 2
    radius = 300

    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)

    colors = [
        "#ff595e",
        "#ffca3a",
        "#8ac926",
        "#1982c4",
        "#6a4c93",
        "#f77f00",
        "#06d6a0",
        "#ef476f",
    ]

    count = len(GIFTS)
    segment = 360 / count

    # Колесо
    for i, gift in enumerate(GIFTS):
        start = angle + i * segment
        end = start + segment

        draw.pieslice(
            (
                center - radius,
                center - radius,
                center + radius,
                center + radius,
            ),
            start=start,
            end=end,
            fill=colors[i % len(colors)],
            outline="white",
            width=4,
        )

        # Текст
        middle = math.radians(start + segment / 2)

        text_x = center + math.cos(middle) * 205
        text_y = center + math.sin(middle) * 205

        font = get_font(24)

        bbox = draw.textbbox((0, 0), gift, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        draw.text(
            (text_x - tw / 2, text_y - th / 2),
            gift,
            fill="black",
            font=font,
        )

    # Центральный круг
    draw.ellipse(
        (
            center - 55,
            center - 55,
            center + 55,
            center + 55,
        ),
        fill="white",
        outline="black",
        width=4,
    )

    # Стрелка
    arrow = [
        (center, 25),
        (center - 30, 90),
        (center + 30, 90),
    ]

    draw.polygon(arrow, fill="black")

    return image


# =========================
# ГЕНЕРАЦИЯ GIF
# =========================

def create_spin_gif(target_index):
    frames = []

    count = len(GIFTS)
    segment = 360 / count

    # Центр нужного сектора
    target_center = target_index * segment + segment / 2

    # Несколько полных оборотов
    rotations = random.randint(5, 7)

    # Финальный угол
    final_angle = (
        -90
        - target_center
        + rotations * 360
    )

    frame_count = 45

    for i in range(frame_count):
        progress = i / (frame_count - 1)

        # Плавное замедление
        eased = 1 - (1 - progress) ** 3

        angle = final_angle * eased

        frame = create_wheel(angle)
        frames.append(frame)

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION,
        loop=0,
    )

    output.seek(0)

    return output


# =========================
# КОМАНДА /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 Крутить колесо!",
                callback_data="spin"
            )
        ]
    ]

    await update.message.reply_text(
        "🎁 Добро пожаловать!\n\n"
        "Сегодня тебе предстоит испытать удачу...\n\n"
        "Готов? 😈",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# КНОПКА КОЛЕСА
# =========================

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # Выбираем подарок
    if FORCED_GIFT is not None and FORCED_GIFT in GIFTS:
        target_index = GIFTS.index(FORCED_GIFT)
    else:
        target_index = random.randrange(len(GIFTS))

    gift = GIFTS[target_index]

    # Создаём анимацию
    gif = create_spin_gif(target_index)

    # Отправляем колесо
    await query.message.reply_animation(
        animation=gif,
        caption="🎡 Колесо вращается...\n\n"
                "Куда же оно остановится? 👀"
    )

    # Результат
    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 Крутить ещё раз",
                callback_data="spin"
            )
        ]
    ]

    await query.message.reply_text(
        f"🎉 **КОЛЕСО ОСТАНОВИЛОСЬ!** 🎉\n\n"
        f"🏆 Твой подарок:\n\n"
        f"🎁 **{gift}**\n\n"
        f"Поздравляем! 🥳",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# ЗАПУСК
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        CallbackQueryHandler(spin, pattern="^spin$")
    )

    print("Gift-Bot запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
