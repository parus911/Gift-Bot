import io
import math
import os
import random

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


# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.environ["BOT_TOKEN"]

GIF_DURATION = 55

GIFTS = [
    "🎁 Надувная лодка для рыбалки",
    "🎮 Боевой пропуск в Fortnite",
    "🍕 Сет из AmSushi",
    "💰 200 €",
    "🍺 100 литров Apperol Spritz",
    "🎧 Билет в караоке",
    "🎁 Незабываемое совместное путешествие",
    "💵 10000 €",
]

# Подарок, который реально выпадет
FORCED_GIFT = "🎁 Незабываемое совместное путешествие"


# =========================
# ШРИФТ
# =========================

def get_font(size):
    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in fonts:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


# =========================
# СОЗДАНИЕ КОЛЕСА
# =========================

def create_wheel(angle=0):
    SIZE = 700
    CENTER = SIZE // 2
    RADIUS = 285

    image = Image.new("RGB", (SIZE, SIZE), (18, 18, 28))
    draw = ImageDraw.Draw(image)

    # Внешнее свечение
    for r in range(RADIUS + 30, RADIUS, -1):
        alpha = int(100 * (RADIUS + 30 - r) / 30)

        color = (
            30 + alpha // 3,
            30 + alpha // 3,
            50 + alpha // 2,
        )

        draw.ellipse(
            (
                CENTER - r,
                CENTER - r,
                CENTER + r,
                CENTER + r,
            ),
            fill=color,
        )

    # Цвета секторов
    colors = [
        (255, 92, 92),
        (255, 174, 66),
        (255, 221, 89),
        (92, 214, 120),
        (70, 170, 255),
        (125, 105, 255),
        (226, 92, 255),
        (255, 105, 180),
    ]

    count = len(GIFTS)
    sector = 360 / count

    # Колесо
    for i in range(count):

        start = angle + i * sector
        end = start + sector

        draw.pieslice(
            (
                CENTER - RADIUS,
                CENTER - RADIUS,
                CENTER + RADIUS,
                CENTER + RADIUS,
            ),
            start=start,
            end=end,
            fill=colors[i % len(colors)],
            outline=(255, 255, 255),
            width=4,
        )

    # Подписи
    font = get_font(22)

    for i, gift in enumerate(GIFTS):

        middle = angle + i * sector + sector / 2

        rad = math.radians(middle)

        text_radius = 190

        x = CENTER + math.cos(rad) * text_radius
        y = CENTER + math.sin(rad) * text_radius

        # Короткий текст для колеса
        short_text = gift

        if len(short_text) > 25:
            short_text = short_text[:23] + "…"

        bbox = draw.textbbox((0, 0), short_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Поворот текста
        text_img = Image.new(
            "RGBA",
            (tw + 20, th + 20),
            (0, 0, 0, 0),
        )

        text_draw = ImageDraw.Draw(text_img)

        text_draw.text(
            (10, 10),
            short_text,
            font=font,
            fill="white",
            stroke_width=3,
            stroke_fill=(0, 0, 0),
        )

        text_img = text_img.rotate(
            -middle,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

        image.paste(
            text_img,
            (
                int(x - text_img.width / 2),
                int(y - text_img.height / 2),
            ),
            text_img,
        )

    # Центральная часть
    draw.ellipse(
        (
            CENTER - 65,
            CENTER - 65,
            CENTER + 65,
            CENTER + 65,
        ),
        fill=(25, 25, 35),
        outline=(255, 215, 80),
        width=8,
    )

    # Центральная точка
    draw.ellipse(
        (
            CENTER - 18,
            CENTER - 18,
            CENTER + 18,
            CENTER + 18,
        ),
        fill=(255, 215, 80),
    )

    # Стрелка сверху
    arrow = [
        (CENTER, 45),
        (CENTER - 32, 5),
        (CENTER + 32, 5),
    ]

    draw.polygon(
        arrow,
        fill=(255, 215, 80),
        outline=(255, 255, 255),
    )

    draw.line(
        [
            (CENTER, 45),
            (CENTER - 32, 5),
            (CENTER + 32, 5),
            (CENTER, 45),
        ],
        fill="white",
        width=4,
    )

    return image


# =========================
# АНИМАЦИЯ
# =========================

def create_spin_gif(target_index):

    frames = []

    # Количество кадров
    total_frames = 100

    # Много оборотов
    rotations = random.randint(7, 9)

    sector = 360 / len(GIFTS)

    # Центр выбранного сектора
    target_angle = (
        360 - (target_index * sector + sector / 2)
    )

    for frame in range(total_frames):

        progress = frame / (total_frames - 1)

        # Плавное замедление
        eased = 1 - (1 - progress) ** 4

        angle = (
            rotations * 360 * eased
            + target_angle
        )

        image = create_wheel(angle)

        # Небольшая надпись внизу
        draw = ImageDraw.Draw(image)

        font = get_font(25)

        text = "🎡 КОЛЕСО УДАЧИ"

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        tw = bbox[2] - bbox[0]

        draw.text(
            (
                350 - tw / 2,
                655,
            ),
            text,
            font=font,
            fill=(255, 215, 80),
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )

        frames.append(
            image.convert("P", palette=Image.Palette.ADAPTIVE)
        )

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


# =========================
# СПИСОК ПОДАРКОВ
# =========================

def gifts_text():

    text = "🎁 **ВОЗМОЖНЫЕ ВЫИГРЫШИ**\n\n"

    for i, gift in enumerate(GIFTS, 1):
        text += f"**{i}.** {gift}\n"

    text += "\n🎡 Ну что, крутим?"

    return text


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ КОЛЕСО!",
                callback_data="spin",
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        gifts_text(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# =========================
# ВРАЩЕНИЕ
# =========================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    # Определяем нужный подарок
    target_index = GIFTS.index(FORCED_GIFT)

    # Создаём анимацию
    gif = create_spin_gif(target_index)

    animation = InputFile(
        gif,
        filename="wheel.gif",
    )

    await query.message.reply_animation(
        animation=animation,
        caption="🎡 Колесо запускается...\n\n🔥 Поехали!",
    )

    # Небольшая пауза
    # чтобы сообщение с результатом не появилось
    # одновременно с началом GIF

    import asyncio

    await asyncio.sleep(
        (GIF_DURATION * 100) / 1000
        + 0.5
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ ЕЩЁ РАЗ",
                callback_data="spin",
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await query.message.reply_text(
        "🎉🎉🎉 **КОЛЕСО ОСТАНОВИЛОСЬ!** 🎉🎉🎉\n\n"
        f"🏆 ТВОЙ ПОДАРОК:\n\n"
        f"✨ **{FORCED_GIFT}** ✨\n\n"
        "Поздравляем! 🥳🎁",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# =========================
# ЗАПУСК
# =========================

def main():

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(
            spin,
            pattern="^spin$",
        )
    )

    print("Gift-Bot запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
