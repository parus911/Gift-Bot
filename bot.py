
import io
import math
import random
import os

from PIL import Image, ImageDraw, ImageFont

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]

GIF_DURATION = 70

GIFTS = [
    "🎁 Надувная лодка для рыбалки",
    "🎮 Боевой пропуск в Fortnite",
    "🍕 Сет из AmSushi",
    "💰 200 €",
    "🍺 100 литров Apperol Spritz",
    "🎧 Билет в караоке",
    "🎁 Незабываемое совместное путешествие",
    "💵 10000€",
]

# Подарок, на котором колесо гарантированно остановится.
# Чтобы сделать случайный подарок:
# FORCED_GIFT = None

FORCED_GIFT = "🎁 Незабываемое совместное путешествие"


# =========================================================
# ШРИФТ
# =========================================================

def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


# =========================================================
# СОЗДАНИЕ КОЛЕСА
# =========================================================

def create_wheel(angle):
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
            width=5,
        )

        # Положение текста
        middle = math.radians(start + segment / 2)

        text_x = center + math.cos(middle) * 200
        text_y = center + math.sin(middle) * 200

        font = get_font(20)

        bbox = draw.textbbox(
            (0, 0),
            gift,
            font=font
        )

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Текст
        draw.text(
            (
                text_x - tw / 2,
                text_y - th / 2
            ),
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
        width=5,
    )

    # Центральная точка
    draw.ellipse(
        (
            center - 10,
            center - 10,
            center + 10,
            center + 10,
        ),
        fill="black",
    )

    # Стрелка сверху
    arrow = [
        (center, 15),
        (center - 35, 90),
        (center + 35, 90),
    ]

    draw.polygon(
        arrow,
        fill="black"
    )

    return image


# =========================================================
# СОЗДАНИЕ АНИМАЦИИ
# =========================================================

def create_spin_gif(target_index):

    frames = []

    count = len(GIFTS)
    segment = 360 / count

    # Центр нужного сектора
    target_center = target_index * segment + segment / 2

    # Количество оборотов
    rotations = random.randint(6, 8)

    # Финальный угол
    final_angle = (
        -90
        - target_center
        + rotations * 360
    )

    # Больше кадров = плавнее
    frame_count = 70

    for i in range(frame_count):

        progress = i / (frame_count - 1)

        # Плавное ускорение/замедление
        eased = 1 - (1 - progress) ** 4

        angle = final_angle * eased

        frame = create_wheel(angle)

        # Важно для корректного GIF
        frame = frame.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )

        frames.append(frame)

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION,
        loop=0,
        optimize=False,
        disposal=2,
    )

    output.seek(0)

    return output


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ КОЛЕСО!",
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


# =========================================================
# ВРАЩЕНИЕ
# =========================================================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # Выбираем подарок
    if FORCED_GIFT is not None and FORCED_GIFT in GIFTS:
        target_index = GIFTS.index(FORCED_GIFT)
    else:
        target_index = random.randrange(len(GIFTS))

    gift = GIFTS[target_index]

    # Создаём GIF
    gif = create_spin_gif(target_index)

    # ВАЖНО:
    # Передаём Telegram имя файла
    animation = InputFile(
        gif,
        filename="wheel.gif"
    )

    # Отправляем анимацию
    await query.message.reply_animation(
        animation=animation,
        caption="🎡 Колесо вращается...\n\n"
                "Куда же оно остановится? 👀"
    )

    # Результат
    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ ЕЩЁ РАЗ",
                callback_data="spin"
            )
        ]
    ]

    await query.message.reply_text(
        f"🎉 КОЛЕСО ОСТАНОВИЛОСЬ! 🎉\n\n"
        f"🏆 ТВОЙ ПОДАРОК:\n\n"
        f"🎁 {gift}\n\n"
        f"🥳 ПОЗДРАВЛЯЕМ!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# ЗАПУСК
# =========================================================

def main():

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            spin,
            pattern="^spin$"
        )
    )

    print("Gift-Bot запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()

