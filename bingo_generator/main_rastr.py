import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_gradient_background(width, height, color1, color2):
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    
    mask.putdata(mask_data)
    gradient = Image.composite(top, base, mask)
    return gradient

def wrap_text(text, font, max_width):
    """Функция для переноса текста на несколько строк, если он не помещается в одну строку"""
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += (words.pop(0) + ' ')
        if not line:  # Если слово слишком длинное и не вмещается на одной строке
            line = words.pop(0)
        lines.append(line.strip())
    return '\n'.join(lines)

def get_max_text_size(texts, font, max_width):
    """Определение максимального размера текста в пикселях"""
    max_width_text = 0
    max_height_text = 0
    for text in texts:
        wrapped_text = wrap_text(text, font, max_width)
        text_size = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = text_size[2] - text_size[0], text_size[3] - text_size[1]
        max_width_text = max(max_width_text, text_width)
        max_height_text = max(max_height_text, text_height)
    return max_width_text, max_height_text

def adjust_font_size(draw, text, cell_size, font_path, max_font_size):
    """Настройка размера шрифта для текста, чтобы он влезал в ячейку"""
    font_size = max_font_size
    font = ImageFont.truetype(font_path, font_size)
    wrapped_text = wrap_text(text, font, cell_size - 20)
    text_size = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width, text_height = text_size[2] - text_size[0], text_size[3] - text_size[1]
    while (text_width > cell_size - 20 or text_height > cell_size - 20) and font_size > 10:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        wrapped_text = wrap_text(text, font, cell_size - 20)
        text_size = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = text_size[2] - text_size[0], text_size[3] - text_size[1]
    return font, wrapped_text

def round_corners(image, radius):
    """Закругление углов изображения"""
    rounded = Image.new('RGB', image.size, (255, 255, 255))
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
    rounded.paste(image, mask=mask)
    return rounded, mask

def create_bingo_card(title, elements, output_filename, font_path="arial.ttf", gradient_colors=("lightblue", "lightpink"), table_bg_color="white", main_border_width=5, inner_border_width=2, corner_radius=30):
    size = int(len(elements) ** 0.5)  # Определяем размер таблицы (например, 5x5)
    assert size * size == len(elements), "Количество элементов должно быть квадратом целого числа."

    # Настраиваем шрифты
    try:
        font_title = ImageFont.truetype(font_path, 50)
        font_cells = ImageFont.truetype(font_path, 22)  # Начальный размер шрифта
    except IOError:
        font_title = ImageFont.load_default()
        font_cells = ImageFont.load_default()

    # Определяем размер ячеек
    cell_size = 200  # Начальный размер ячейки
    table_width = cell_size * size
    table_height = cell_size * size
    img_width = table_width + 200
    img_height = table_height + 200

    # Создаем градиентный фон
    gradient = create_gradient_background(img_width, img_height, gradient_colors[0], gradient_colors[1])
    draw = ImageDraw.Draw(gradient)

    # Создаем фон для таблицы
    table_bg = Image.new('RGB', (table_width, table_height), table_bg_color)
    table_draw = ImageDraw.Draw(table_bg)

    # Рисуем сетку бинго и добавляем элементы
    for i in range(size):
        for j in range(size):
            x0 = j * cell_size
            y0 = i * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            table_draw.rectangle([x0, y0, x1, y1], outline="black", width=inner_border_width)
            text = elements[i * size + j]
            font, wrapped_text = adjust_font_size(table_draw, text, cell_size, font_path, 22)
            text_size = table_draw.textbbox((0, 0), wrapped_text, font=font)
            text_width, text_height = text_size[2] - text_size[0], text_size[3] - text_size[1]
            text_x = x0 + (cell_size - text_width) // 2
            text_y = y0 + (cell_size - text_height) // 2
            table_draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill="black", align="center")

    # Закругляем углы таблицы
    table_bg, mask = round_corners(table_bg, corner_radius)

    # Добавляем заголовок на градиентный фон
    title_size = draw.textbbox((0, 0), title, font=font_title)
    draw.text((img_width // 2 - (title_size[2] - title_size[0]) // 2, 20), title, font=font_title, fill="black")

    # Вставляем таблицу на градиентный фон
    table_x = 100
    table_y = 100
    gradient.paste(table_bg, (table_x, table_y), mask)

    # Рисуем главный контур
    draw.rounded_rectangle([table_x, table_y, table_x + table_width, table_y + table_height], radius=corner_radius, outline="black", width=main_border_width)

    # Сохраняем изображение в папку со скриптом
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_filename)
    gradient.save(output_path)
    print(f"Карточка бинго сохранена в {output_path}")

# Пример использования
title = "Guilty pleasure"
elements = [
    "Проводить время в соцсетях, прокручивая ленту в течение часов", "Ловить фиксацию на сериалах/ персонажах/ реальных людях", "Следить за жизнью блогеров и инфлюенсеров", "петь в караоке, несмотря на отсутствие вокальных данных", "смотреть мелодрамы и романтические фильмы (ромком/ подростковые фильмы про любовь)",
    "покупать и коллекционировать игрушки или предметы", "читать легкую литературу (фанфики/ фэнтези/ поп-литература)", "слушать поп-песни, рэп, к-поп", "представлять сценарии возможных событий с людьми, которые вам симпатизируют", "следить за человеком в соц сетях (его подписки/ музыка/ сообщества/ кого лайкает и тд)",
    "изучать астрологию, знаки зодиака, смотреть шоу, связанные с этой темой", "учиться в школе", "разработка собственного кода и программного обеспечения", "смотреть реалити-шоу или уральских пельменей", "покупать подписки на стримеров/ мерч у блогеров",
    "заказывать еду на дом, даже если можно было бы приготовить дома", "смотреть аниме (я хз почему он в эту категорию это записал, это же нормально уже...ладно молчу)", "покупать дорогие кофейные напитки, вместо того чтобы приготовить дома", "слушать грустные песни, чтобы стало ещё хуже", "романтизировать свою жизнь или какие-то события",
    "посещать какие-то мероприятия, скрывая это от окружающих", "предпочтения в сексе/сексуальные фантазии, которые в обществе считаются странными", "любить быть в курсе сплетен", "забирать из заведений/отелей бесплатные вещи (салфетки/ шампуни/ пакетики с сахаром и тд)", "перечитывать старые переписки"
]
output_filename = "bingo_card_guilty_pleasure.png"
font_path = "bingo_generator/fonts/Oldtimer.ttf"

create_bingo_card(title, elements, output_filename, font_path ,gradient_colors=("#FFE1E1", "#9A8888"), table_bg_color="#E6CFE2",  main_border_width=5, inner_border_width=2, corner_radius=30)
