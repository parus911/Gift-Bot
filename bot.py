import io
import math
import os
import asyncio

from PIL import Image, ImageDraw, ImageFont

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

GIF_DURATION = 65
GIF_FRAMES = 72

WHEEL_SIZE = 500

GIF_FILE = "wheel.gif"

GIF_DATA = None
GIF_READY = False


# ============================================================
# ПОДАРКИ
# ============================================================

GIFTS = [
    "🎁 Надувная лодка для рыбалки",
    "🎮 Боевой пропуск в Fortnite",
    "💎 Подарок-сюрприз от любимого",
    "🍹 100 литров Aperol Spritz",
    "🎤 Билет в караоке",
    "✈️ Путешествие в неизвестную страну",
    "💵 10 000 €",
    "👑 День, когда Любовь выбирает всё",
]

# Главный подарок
FORCED_GIFT = "✈️ Путешествие в неизвестную страну"


# ============================================================
# ШРИФТ
# ============================================================

def get_font(size, bold=False):

    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# ============================================================
# ПРИВЕТСТВИЕ
# ============================================================

def welcome_text():

    return (
        "🎉🎂 <b>С ДНЁМ РОЖДЕНИЯ, ЛЮБОВЬ!</b> 🎂🎉\n\n"
        "❤️ Сегодня твой особенный день!\n\n"
        "А значит, пришло время узнать,\n"
        "какой подарок приготовил для тебя\n"
        "твой любимый человек. 🎁\n\n"
        "Но подарок определит...\n"
        "<b>КОЛЕСО УДАЧИ! 🎡</b>"
    )


# ============================================================
# СПИСОК ПОДАРКОВ
# ============================================================

def gifts_text():

    return (
        "🎁 <b>ВОТ ЧТО МОЖЕТ ТЕБЯ ЖДАТЬ:</b>\n\n"
        "▫️ 🎁 Надувная лодка для рыбалки\n"
        "▫️ 🎮 Боевой пропуск в Fortnite\n"
        "▫️ 💎 Подарок-сюрприз от любимого\n"
        "▫️ 🍹 100 литров Aperol Spritz\n"
        "▫️ 🎤 Билет в караоке\n"
        "▫️ ✈️ Путешествие в неизвестную страну\n"
        "▫️ 💵 10 000 €\n"
        "▫️ 👑 День, когда Любовь выбирает всё\n\n"
        "❤️ Но какой именно подарок достанется тебе — "
        "решит судьба!"
    )


# ============================================================
# СОЗДАНИЕ КОЛЕСА
# ============================================================

def create_wheel(angle=0):

    size = WHEEL_SIZE

    image = Image.new(
        "RGB",
        (size, size),
        "#FFF5E6",
    )

    draw = ImageDraw.Draw(image)

    center = size // 2
    radius = 220

    colors = [
        "#FF6B6B",
        "#FFD93D",
        "#6BCB77",
        "#4D96FF",
        "#C77DFF",
        "#FF922B",
        "#20C997",
        "#F06595",
    ]

    sector_angle = 360 / len(GIFTS)

    # --------------------------------------------------------
    # СЕКТОРА
    # --------------------------------------------------------

    for i in range(len(GIFTS)):

        start = i * sector_angle + angle - 90
        end = start + sector_angle

        draw.pieslice(
            (
                center - radius,
                center - radius,
                center + radius,
                center + radius,
            ),
            start=start,
            end=end,
            fill=colors[i],
            outline="white",
            width=3,
        )

        # Короткие названия для колеса
        names = [
            "ЛОДКА",
            "FORTNITE",
            "СЮРПРИЗ",
            "APEROL",
            "КАРАОКЕ",
            "ПУТЕШЕСТВИЕ",
            "10 000 €",
            "ЛЮБОВЬ\nВЫБИРАЕТ ВСЁ",
        ]

        text = names[i]

        font = get_font(15, bold=True)

        middle = math.radians(
            (start + end) / 2
        )

        text_radius = 155

        x = center + math.cos(middle) * text_radius
        y = center + math.sin(middle) * text_radius

        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            align="center",
        )

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        draw.multiline_text(
            (
                x - tw / 2,
                y - th / 2,
            ),
            text,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill="black",
            align="center",
        )

    # --------------------------------------------------------
    # ВНЕШНЕЕ КОЛЬЦО
    # --------------------------------------------------------

    draw.ellipse(
        (
            center - radius,
            center - radius,
            center + radius,
            center + radius,
        ),
        outline="#333333",
        width=6,
    )

    # --------------------------------------------------------
    # ЦЕНТР КОЛЕСА
    # --------------------------------------------------------

    hub_radius = 55

    draw.ellipse(
        (
            center - hub_radius,
            center - hub_radius,
            center + hub_radius,
            center + hub_radius,
        ),
        fill="white",
        outline="#333333",
        width=5,
    )

    font = get_font(16, bold=True)

    text = "КОЛЕСО\nУДАЧИ"

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        align="center",
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.multiline_text(
        (
            center - tw / 2,
            center - th / 2,
        ),
        text,
        font=font,
        fill="#222222",
        align="center",
    )

    # --------------------------------------------------------
    # СТРЕЛКА
    # --------------------------------------------------------

    arrow = [
        (center, 12),
        (center - 21, 52),
        (center + 21, 52),
    ]

    draw.polygon(
        arrow,
        fill="#E63946",
        outline="#7F1D1D",
    )

    return image


# ============================================================
# СОЗДАНИЕ GIF
# ============================================================

def create_spin_gif(target_index):

    frames = []

    sector_angle = 360 / len(GIFTS)

    # Вычисляем угол, при котором нужный сектор
    # окажется ровно под верхней стрелкой
    target_angle = (
        360
        - (
            target_index * sector_angle
            + sector_angle / 2
        )
    )

    # 8 полных оборотов
    total_rotation = (
        360 * 8
        + target_angle
    )

    for frame in range(GIF_FRAMES):

        progress = frame / (GIF_FRAMES - 1)

        # Плавное замедление к концу
        eased = 1 - (1 - progress) ** 3

        angle = total_rotation * eased

        frame_image = create_wheel(angle)

        frames.append(frame_image)

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION,
        loop=1,
        optimize=True,
    )

    output.seek(0)

    return output.getvalue()


# ============================================================
# ФИНАЛЬНЫЙ ЭКРАН-БИЛЕТ
# ============================================================

def create_final_ticket():

    width = 800
    height = 1050

    image = Image.new(
        "RGB",
        (width, height),
        "#FFF8EE",
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # РАМКА
    # --------------------------------------------------------

    draw.rectangle(
        (35, 35, width - 35, height - 35),
        outline="#222222",
        width=5,
    )

    draw.rectangle(
        (55, 55, width - 55, height - 55),
        outline="#C9A227",
        width=3,
    )

    # --------------------------------------------------------
    # ШРИФТЫ
    # --------------------------------------------------------

    font_big = get_font(48, bold=True)
    font_title = get_font(38, bold=True)
    font_medium = get_font(30, bold=True)
    font_small = get_font(26)
    font_instruction = get_font(25)

    # --------------------------------------------------------
    # ФУНКЦИЯ ЦЕНТРИРОВАННОГО ТЕКСТА
    # --------------------------------------------------------

    def centered(
        text,
        y,
        font,
        fill="#222222",
    ):

        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            align="center",
        )

        tw = bbox[2] - bbox[0]

        draw.multiline_text(
            (
                width / 2 - tw / 2,
                y,
            ),
            text,
            font=font,
            fill=fill,
            align="center",
        )

    # --------------------------------------------------------
    # ЗАГОЛОВОК
    # --------------------------------------------------------

    centered(
        "ЛЮБОВЬ!",
        95,
        font_big,
        "#B22222",
    )

    centered(
        "ТЫ ВЫИГРАЛА",
        165,
        font_title,
    )

    centered(
        "ПУТЕШЕСТВИЕ",
        220,
        font_title,
        "#C9A227",
    )

    centered(
        "В НЕИЗВЕСТНУЮ СТРАНУ",
        275,
        font_medium,
    )

    # --------------------------------------------------------
    # РАЗДЕЛИТЕЛЬ
    # --------------------------------------------------------

    draw.line(
        (110, 345, 690, 345),
        fill="#C9A227",
        width=4,
    )

    # --------------------------------------------------------
    # МЕСТО НАЗНАЧЕНИЯ
    # --------------------------------------------------------

    centered(
        "МЕСТО НАЗНАЧЕНИЯ",
        390,
        font_small,
    )

    centered(
        "СЕКРЕТНО",
        435,
        font_big,
        "#B22222",
    )

    centered(
        "🤫",
        505,
        font_medium,
    )

    # --------------------------------------------------------
    # ДАТА
    # --------------------------------------------------------

    centered(
        "ДАТА ВЫЛЕТА",
        585,
        font_small,
    )

    centered(
        "29 ОКТЯБРЯ",
        625,
        font_big,
        "#B22222",
    )

    # --------------------------------------------------------
    # ВРЕМЯ
    # --------------------------------------------------------

    centered(
        "ВРЕМЯ ВЫЛЕТА",
        705,
        font_small,
    )

    centered(
        "06:00",
        745,
        font_big,
        "#B22222",
    )

    # --------------------------------------------------------
    # ИНСТРУКЦИЯ
    # --------------------------------------------------------

    draw.line(
        (110, 830, 690, 830),
        fill="#C9A227",
        width=3,
    )

    centered(
        "ИНСТРУКЦИЯ",
        855,
        font_medium,
        "#C9A227",
    )

    centered(
        "Собрать чемодан\n"
        "Не спрашивать, куда летим\n"
        "Довериться любимому",
        900,
        font_instruction,
    )

    return image


# ============================================================
# ПРЕДВАРИТЕЛЬНАЯ ГЕНЕРАЦИЯ GIF
# ============================================================

async def prepare_gif():

    global GIF_DATA
    global GIF_READY

    print("🎡 Генерируем GIF колеса...")

    target_index = GIFTS.index(
        FORCED_GIFT
    )

    GIF_DATA = await asyncio.to_thread(
        create_spin_gif,
        target_index,
    )

    GIF_READY = True

    print(
        f"✅ GIF готов! "
        f"Размер: "
        f"{len(GIF_DATA) / 1024 / 1024:.2f} MB"
    )


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

    await update.message.reply_text(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# ПОКАЗАТЬ ПОДАРКИ
# ============================================================

async def show_gifts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

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
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# ВРАЩЕНИЕ КОЛЕСА
# ============================================================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    global GIF_READY
    global GIF_DATA

    query = update.callback_query

    # --------------------------------------------------------
    # СРАЗУ ОТВЕЧАЕМ TELEGRAM
    # --------------------------------------------------------

    try:
        await query.answer(
            text="🎡 Запускаем колесо!"
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # ЗАЩИТА ОТ ДВОЙНОГО НАЖАТИЯ
    # --------------------------------------------------------

    if context.user_data.get(
        "spinning"
    ):
        return

    context.user_data["spinning"] = True

    try:

        # ----------------------------------------------------
        # ПРОВЕРКА ГОТОВНОСТИ GIF
        # ----------------------------------------------------

        if not GIF_READY or GIF_DATA is None:

            await query.message.reply_text(
                "⏳ <b>Колесо ещё готовится...</b>\n\n"
                "Подожди несколько секунд и попробуй снова! 🎡",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # ОБРАТНЫЙ ОТСЧЁТ
        # ----------------------------------------------------

        countdown = await query.message.reply_text(
            "🎁 <b>ПОДГОТАВЛИВАЕМ СЮРПРИЗ...</b>\n\n"
            "⏳ <b>3️⃣</b>",
            parse_mode="HTML",
        )

        await asyncio.sleep(1)

        await countdown.edit_text(
            "🎁 <b>ПОДГОТАВЛИВАЕМ СЮРПРИЗ...</b>\n\n"
            "⏳ <b>2️⃣</b>",
            parse_mode="HTML",
        )

        await asyncio.sleep(1)

        await countdown.edit_text(
            "🎁 <b>ПОДГОТАВЛИВАЕМ СЮРПРИЗ...</b>\n\n"
            "⏳ <b>1️⃣</b>",
            parse_mode="HTML",
        )

        await asyncio.sleep(1)

        await countdown.edit_text(
            "🎡 <b>ПОЕХАЛИ! 🔥</b>",
            parse_mode="HTML",
        )

        # ----------------------------------------------------
        # ОТПРАВЛЯЕМ ГОТОВЫЙ GIF
        # ----------------------------------------------------

        gif_stream = io.BytesIO(
            GIF_DATA
        )

        gif_stream.name = GIF_FILE

        await query.message.reply_animation(
            animation=gif_stream,
        )

        # ----------------------------------------------------
        # ЖДЁМ ОКОНЧАНИЯ АНИМАЦИИ
        # ----------------------------------------------------

        animation_time = (
            GIF_DURATION * GIF_FRAMES
        ) / 1000

        await asyncio.sleep(
            animation_time + 0.5
        )

        # ----------------------------------------------------
        # СОЗДАЁМ ФИНАЛЬНЫЙ БИЛЕТ
        # ----------------------------------------------------

        ticket_image = create_final_ticket()

        ticket_stream = io.BytesIO()

        ticket_image.save(
            ticket_stream,
            format="PNG",
        )

        ticket_stream.seek(0)

        ticket_stream.name = (
            "birthday_ticket.png"
        )

        # ----------------------------------------------------
        # ОТПРАВЛЯЕМ ФИНАЛ
        # ----------------------------------------------------

        await query.message.reply_photo(
            photo=ticket_stream,
            caption=(
                "❤️ <b>ЛЮБОВЬ, ПОЗДРАВЛЯЕМ!</b> ❤️\n\n"
                "Твой главный подарок уже определён.\n\n"
                "🌍 Страна назначения пока остаётся "
                "секретом... 🤫\n\n"
                "🧳 Готовь чемодан!"
            ),
            parse_mode="HTML",
        )

        # Больше никаких кнопок.
        # Финал завершён.

    except Exception as e:

        print(
            f"❌ Ошибка во время вращения: {e}"
        )

        try:
            await query.message.reply_text(
                "😢 Что-то пошло не так.\n\n"
                "Попробуй ещё раз! 🎡"
            )
        except Exception:
            pass

    finally:

        context.user_data["spinning"] = False


# ============================================================
# POST INIT
# ============================================================

async def post_init(
    application: Application,
):

    await prepare_gif()


# ============================================================
# MAIN
# ============================================================

def main():

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
        .post_init(post_init)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
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

    print("🤖 Gift-Bot запущен!")

    app.run_polling()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    main()
