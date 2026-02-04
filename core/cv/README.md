# Computer Vision Module

Модуль компьютерного зрения для template matching (fallback для Sanderling).

## Компоненты

- **template_matcher.py** - Template matching для поиска изображений на экране

## Использование

```python
from core.cv.template_matcher import TemplateMatcher

# Создать matcher
matcher = TemplateMatcher()

# Найти изображение
coords = matcher.find_image("eve_overview_header_name.png", confidence=0.9)
if coords:
    x, y = coords
    print(f"Found at ({x}, {y})")

# Найти все вхождения
all_coords = matcher.find_all_images("target_icon.png", confidence=0.85)
print(f"Found {len(all_coords)} instances")
```

## Шаблоны

Шаблоны изображений хранятся в `resources/assets/`

Поддерживаемые форматы: PNG, JPG

## Параметры

- **confidence** - Порог совпадения (0.0 - 1.0), по умолчанию 0.9
- **region** - Область поиска (x1, y1, x2, y2) или None для всего экрана

## Производительность

Template matching работает быстро для небольших шаблонов, но может быть медленным для больших изображений или высоких разрешений.

Рекомендации:
- Используйте небольшие шаблоны (< 100x100 пикселей)
- Ограничивайте область поиска через параметр region
- Используйте разумный порог confidence (0.8-0.95)
