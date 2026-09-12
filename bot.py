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


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.environ["BOT_TOKEN"]

GIF_DURATION = 55

# Все возможные подарки
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

# Подарок, который действительно выпадет
FORCED_GIFT = "✈️ Незабываемое совместное путешествие"


# ============================================================
# ШРИФТЫ
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
# ТЕКСТ ПРИВЕТСТВИЯ
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

    text = (
        "🎁 **ЧТО МОЖЕТ ВЫПАСТЬ?**\n\n"
    )

    for i, gift in enumerate(GIFTS, 1):
        text += f"**{i}.** {gift}\n"

    text += (
        "\n❤️ Но какой подарок выберет колесо — "
        "узнаем только после вращения!\n\n"
        "🎡 **Ну что, Любовь, крутим?**"
    )

    return text


# ============================================================
# КОЛЕСО
# ============================================================

def create_wheel(angle=0):

    SIZE = 700
    CENTER = SIZE // 2
    RADIUS = 285

    # Фон
    image = Image.new(
        "RGB",
        (SIZE, SIZE),
        (15, 15, 25)
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Декоративное внешнее кольцо
    # --------------------------------------------------------

    draw.ellipse(
        (
            CENTER - RADIUS - 18,
            CENTER - RADIUS - 18,
            CENTER + RADIUS + 18,
            CENTER + RADIUS + 18,
        ),
        fill=(255, 215, 80),
        outline=(255, 255, 255),
        width=5,
    )

    # --------------------------------------------------------
    # Цвета секторов
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
            fill=colors[i % len(colors)],
            outline=(255, 255, 255),
            width=4,
        )

    # --------------------------------------------------------
    # Подписи
    # --------------------------------------------------------

    font = get_font(20)

    for i, gift in enumerate(GIFTS):

        middle = angle + i * sector + sector / 2

        rad = math.radians(middle)

        text_radius = 195

        x = CENTER + math.cos(rad) * text_radius
        y = CENTER + math.sin(rad) * text_radius

        # Сокращаем длинные названия
        short_text = gift

        if len(short_text) > 23:
            short_text = short_text[:21] + "…"

        bbox = draw.textbbox(
            (0, 0),
            short_text,
            font=font,
        )

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        text_img = Image.new(
            "RGBA",
            (tw + 30, th + 30),
            (0, 0, 0, 0),
        )

        text_draw = ImageDraw.Draw(text_img)

        text_draw.text(
            (15, 15),
            short_text,
            font=font,
            fill="white",
            stroke_width=3,
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
    # Центральная часть
    # --------------------------------------------------------

    draw.ellipse(
        (
            CENTER - 70,
            CENTER - 70,
            CENTER + 70,
            CENTER + 70,
        ),
        fill=(25, 25, 35),
        outline=(255, 215, 80),
        width=8,
    )

    draw.ellipse(
        (
            CENTER - 20,
            CENTER - 20,
            CENTER + 20,
            CENTER + 20,
        ),
        fill=(255, 215, 80),
    )

    # --------------------------------------------------------
    # Стрелка сверху
    # --------------------------------------------------------

    arrow = [
        (CENTER, 43),
        (CENTER - 35, 3),
        (CENTER + 35, 3),
    ]

    draw.polygon(
        arrow,
        fill=(255, 215, 80),
        outline=(255, 255, 255),
    )

    draw.line(
        [
            (CENTER, 43),
            (CENTER - 35, 3),
            (CENTER + 35, 3),
            (CENTER, 43),
        ],
        fill="white",
        width=4,
    )

    # --------------------------------------------------------
    # Нижняя надпись
    # --------------------------------------------------------

    title_font = get_font(25)

    title = "🎡 КОЛЕСО УДАЧИ"

    bbox = draw.textbbox(
        (0, 0),
        title,
        font=title_font,
    )

    tw = bbox[2] - bbox[0]

    draw.text(
        (
            CENTER - tw / 2,
            655,
        ),
        title,
        font=title_font,
        fill=(255, 215, 80),
        stroke_width=2,
        stroke_fill="black",
    )

    return image


# ============================================================
# АНИМАЦИЯ ВРАЩЕНИЯ
# ============================================================

def create_spin_gif(target_index):

    frames = []

    total_frames = 105

    # Количество полных оборотов
    rotations = random.randint(7, 9)

    sector = 360 / len(GIFTS)

    # Центр нужного сектора
    target_angle = (
        360
        - (target_index * sector + sector / 2)
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
        optimize=False,
        disposal=2,
    )

    output.seek(0)

    return output


# ============================================================
# /START
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

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        welcome_text(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# ============================================================
# ПОКАЗАТЬ ПОДАРКИ
# ============================================================

async def show_gifts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🎡 КРУТИТЬ КОЛЕСО!",
                callback_data="spin",
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await query.message.reply_text(
        gifts_text(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# ============================================================
# ВРАЩЕНИЕ КОЛЕСА
# ============================================================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    # --------------------------------------------------------
    # Определяем нужный сектор
    # --------------------------------------------------------

    target_index = GIFTS.index(
        FORCED_GIFT
    )

    # --------------------------------------------------------
    # Сообщение перед запуском
    # --------------------------------------------------------

    await query.message.reply_text(
        "🎡 **ЛЮБОВЬ, ВНИМАНИЕ!**\n\n"
        "Колесо сейчас определит твой подарок...\n\n"
        "🔥 **ПОЕХАЛИ!** 🔥",
        parse_mode="Markdown",
    )

    # --------------------------------------------------------
    # Создаём GIF
    # --------------------------------------------------------

    gif = create_spin_gif(
        target_index
    )

    animation = InputFile(
        gif,
        filename="birthday_wheel.gif",
    )

    # --------------------------------------------------------
    # Отправляем колесо
    # --------------------------------------------------------

    await query.message.reply_animation(
        animation=animation,
        caption=(
            "🎡 **КОЛЕСО ВРАЩАЕТСЯ...**\n\n"
            "👀 Куда же оно остановится?"
        ),
        parse_mode="Markdown",
    )

    # --------------------------------------------------------
    # Ждём окончания анимации
    # --------------------------------------------------------

    animation_time = (
        GIF_DURATION * 105
    ) / 1000

    await asyncio.sleep(
        animation_time + 1.0
    )

    # --------------------------------------------------------
    # Объявление результата
    # --------------------------------------------------------

    await query.message.reply_text(
        "😱 **ОНО ОСТАНОВИЛОСЬ!**\n\n"
        "🥁🥁🥁\n\n"
        "✨ Сейчас узнаем, что тебе досталось...",
        parse_mode="Markdown",
    )

    await asyncio.sleep(2)

    # --------------------------------------------------------
    # Финальный подарок
    # --------------------------------------------------------

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
        reply_markup=reply_markup,
    )


# ============================================================
# ЗАПУСК БОТА
# ============================================================

def main():

    app = (
        Application.builder()
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
