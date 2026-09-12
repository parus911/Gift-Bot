import io
import math
import os
import random
import asyncio

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

from telegram.request import HTTPXRequest


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.environ["BOT_TOKEN"]

# GIF стал легче
GIF_DURATION = 65
GIF_FRAMES = 72

GIFTS = [
    "🎁 Надувная лодка для рыбалки",
    "🎮 Боевой пропуск в Fortnite",
    "🍕 Сет из AmSushi",
    "💰 200 €",
    "🍺 100 литров Aperol Spritz",
    "🎧 Билет в караоке",
    "✈️ Незабываемое совместное путешествие",
    "💵 10000 €",
]

# Подарок, который реально выпадет
FORCED_GIFT = "✈️ Незабываемое совместное путешествие"


# ============================================================
# ШРИФТ
# ============================================================

def get_font(size):

    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in fonts:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


# ============================================================
# ПРИВЕТСТВИЕ
# ============================================================

def welcome_text():

    return (
        "🎉🎂 **С ДНЁМ РОЖДЕНИЯ, ЛЮБОВЬ!** 🎂🎉\n\n"
        "❤️ Сегодня твой особенный день!\n\n"
        "И мы приготовили для тебя небольшой сюрприз... 🎁\n\n"
        "На колесе — несколько подарков, "
        "но какой именно достанется тебе? 👀\n\n"
        "✨ **Готова узнать?** ✨"
    )


# ============================================================
# СПИСОК ПОДАРКОВ
# ============================================================

def gifts_text():

    text = "🎁 **ВОЗМОЖНЫЕ ПОДАРКИ**\n\n"

    for i, gift in enumerate(GIFTS, 1):
        text += f"**{i}.** {gift}\n"

    text += (
        "\n❤️ Но какой подарок выберет колесо — "
        "узнаем только после вращения!\n\n"
        "🎡 **Ну что, Любовь, крутим?**"
    )

    return text


# ============================================================
# СОЗДАНИЕ КОЛЕСА
# ============================================================

def create_wheel(angle=0):

    SIZE = 500
    CENTER = SIZE // 2
    RADIUS = 205

    image = Image.new(
        "RGB",
        (SIZE, SIZE),
        (15, 15, 25)
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Внешнее кольцо
    # --------------------------------------------------------

    draw.ellipse(
        (
            CENTER - RADIUS - 12,
            CENTER - RADIUS - 12,
            CENTER + RADIUS + 12,
            CENTER + RADIUS + 12,
        ),
        fill=(255, 215, 80),
        outline=(255, 255, 255),
        width=4,
    )

    # --------------------------------------------------------
    # Цвета
    # --------------------------------------------------------

    colors = [
        (255, 82, 82),
        (255, 164, 62),
        (255, 215, 70),
        (76, 205, 115),
        (65, 155, 255),
        (111, 91, 255),
        (215, 83, 255),
        (255, 93, 168),
    ]

    count = len(GIFTS)
    sector = 360 / count

    # --------------------------------------------------------
    # Сектора
    # --------------------------------------------------------

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
            fill=colors[i],
            outline="white",
            width=3,
        )

    # --------------------------------------------------------
    # Подписи
    # --------------------------------------------------------

    font = get_font(15)

    for i, gift in enumerate(GIFTS):

        middle = angle + i * sector + sector / 2

        rad = math.radians(middle)

        text_radius = 138

        x = CENTER + math.cos(rad) * text_radius
        y = CENTER + math.sin(rad) * text_radius

        short_text = gift

        if len(short_text) > 19:
            short_text = short_text[:17] + "…"

        bbox = draw.textbbox(
            (0, 0),
            short_text,
            font=font,
        )

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

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
            stroke_width=2,
            stroke_fill="black",
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

    # --------------------------------------------------------
    # Центр
    # --------------------------------------------------------

    draw.ellipse(
        (
            CENTER - 48,
            CENTER - 48,
            CENTER + 48,
            CENTER + 48,
        ),
        fill=(25, 25, 35),
        outline=(255, 215, 80),
        width=6,
    )

    draw.ellipse(
        (
            CENTER - 13,
            CENTER - 13,
            CENTER + 13,
            CENTER + 13,
        ),
        fill=(255, 215, 80),
    )

    # --------------------------------------------------------
    # Стрелка
    # --------------------------------------------------------

    arrow = [
        (CENTER, 32),
        (CENTER - 25, 2),
        (CENTER + 25, 2),
    ]

    draw.polygon(
        arrow,
        fill=(255, 215, 80),
        outline="white",
    )

    draw.line(
        [
            (CENTER, 32),
            (CENTER - 25, 2),
            (CENTER + 25, 2),
            (CENTER, 32),
        ],
        fill="white",
        width=3,
    )

    # --------------------------------------------------------
    # Надпись
    # --------------------------------------------------------

    title_font = get_font(19)

    title = "КОЛЕСО УДАЧИ"

    bbox = draw.textbbox(
        (0, 0),
        title,
        font=title_font,
    )

    tw = bbox[2] - bbox[0]

    draw.text(
        (
            CENTER - tw / 2,
            472,
        ),
        title,
        font=title_font,
        fill=(255, 215, 80),
        stroke_width=2,
        stroke_fill="black",
    )

    return image


# ============================================================
# СОЗДАНИЕ GIF
# ============================================================

def create_spin_gif(target_index):

    frames = []

    rotations = random.randint(7, 9)

    sector = 360 / len(GIFTS)

    target_angle = (
        360
        - (target_index * sector + sector / 2)
    )

    for frame in range(GIF_FRAMES):

        progress = frame / (GIF_FRAMES - 1)

        # Очень плавное замедление
        eased = 1 - (1 - progress) ** 4

        angle = (
            rotations * 360 * eased
            + target_angle
        )

        image = create_wheel(angle)

        frames.append(
            image.convert(
                "P",
                palette=Image.Palette.ADAPTIVE
            )
        )

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION,
        loop=0,
        optimize=True,
        disposal=2,
    )

    output.seek(0)

    return output


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 ПОСМОТРЕТЬ ПОДАРКИ",
                callback_data="show_gifts",
            )
        ]
    ]

    await update.message.reply_text(
        welcome_text(),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# ПОКАЗАТЬ ПОДАРКИ
# ============================================================

async def show_gifts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    # Отвечаем Telegram сразу
    try:
        await query.answer()
    except Exception:
        pass

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ КОЛЕСО!",
                callback_data="spin",
            )
        ]
    ]

    await query.message.reply_text(
        gifts_text(),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# ВРАЩЕНИЕ
# ============================================================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    # --------------------------------------------------------
    # Сразу отвечаем Telegram
    # --------------------------------------------------------

    try:
        await query.answer(
            text="🎡 Запускаем колесо!"
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # Защита от повторного нажатия
    # --------------------------------------------------------

    if context.user_data.get("spinning"):
        return

    context.user_data["spinning"] = True

    try:

        # ----------------------------------------------------
        # Сообщение
        # ----------------------------------------------------

        await query.message.reply_text(
            "🎡 **ЛЮБОВЬ, ВНИМАНИЕ!**\n\n"
            "Колесо сейчас определит твой подарок...\n\n"
            "🔥 **ПОЕХАЛИ!** 🔥",
            parse_mode="Markdown",
        )

        # ----------------------------------------------------
        # Нужный подарок
        # ----------------------------------------------------

        target_index = GIFTS.index(
            FORCED_GIFT
        )

        # ----------------------------------------------------
        # ВАЖНО:
        # создаём GIF в отдельном потоке,
        # чтобы Telegram не зависал
        # ----------------------------------------------------

        gif = await asyncio.to_thread(
            create_spin_gif,
            target_index
        )

        animation = InputFile(
            gif,
            filename="birthday_wheel.gif",
        )

        # ----------------------------------------------------
        # Отправляем GIF
        # ----------------------------------------------------

        await query.message.reply_animation(
            animation=animation,
            caption=(
                "🎡 **КОЛЕСО ВРАЩАЕТСЯ...**\n\n"
                "👀 Куда же оно остановится?"
            ),
            parse_mode="Markdown",
        )

        # ----------------------------------------------------
        # Ждём окончания
        # ----------------------------------------------------

        animation_time = (
            GIF_DURATION * GIF_FRAMES
        ) / 1000

        await asyncio.sleep(
            animation_time + 1
        )

        # ----------------------------------------------------
        # Напряжение
        # ----------------------------------------------------

        await query.message.reply_text(
            "😱 **ОНО ОСТАНОВИЛОСЬ!**\n\n"
            "🥁 🥁 🥁\n\n"
            "✨ Сейчас узнаем, что тебе досталось...",
            parse_mode="Markdown",
        )

        await asyncio.sleep(2)

        # ----------------------------------------------------
        # РЕЗУЛЬТАТ
        # ----------------------------------------------------

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎡 КРУТИТЬ ЕЩЁ РАЗ",
                    callback_data="spin",
                )
            ]
        ]

        await query.message.reply_text(
            "🎉✨🎊🥳🎁✨🎉\n\n"
            "❤️ **ЛЮБОВЬ, ПОЗДРАВЛЯЕМ!** ❤️\n\n"
            "🏆 Сегодня фортуна выбрала именно тебя!\n\n"
            "🎁 **ТВОЙ ПОДАРОК:**\n\n"
            "✈️ **НЕЗАБЫВАЕМОЕ\n"
            "СОВМЕСТНОЕ ПУТЕШЕСТВИЕ** ❤️\n\n"
            "🎉✨🎊🥳🎁✨🎉\n\n"
            "С Днём рождения, Любовь! ❤️\n\n"
            "Пусть этот подарок станет одним "
            "из самых ярких воспоминаний! 🥰",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    finally:

        context.user_data["spinning"] = False


# ============================================================
# ЗАПУСК
# ============================================================

def main():

    # Увеличиваем таймауты Telegram API
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=30,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
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
            show_gifts,
            pattern="^show_gifts$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            spin,
            pattern="^spin$",
        )
    )

    print(
        "🎂 Gift-Bot для Любови запущен!"
    )

    app.run_polling()


if __name__ == "__main__":
    main()
