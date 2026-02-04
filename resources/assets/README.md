# Assets - Графические ресурсы для автоматизации

## Текущие ассеты

### HUD
| Файл | Описание |
|------|----------|
| `eve_hud_anchor.png` | Anchor для позиционирования HUD (иконка скорости корабля). Используется для расчёта позиции пушек и других элементов HUD. |

### Overview
| Файл | Описание |
|------|----------|
| `eve_overview_empty.png` | Надпись "Ничего не найдено" - индикатор пустого overview. |
| `eve_overview_header_name.png` | Заголовок "Название" - anchor для подсчёта строк. |
| `eve_tab_pvp_foe.png` | Таб "PvP Foe" (красный текст) - вкладка overview с враждебными целями. |
| `eve_tab_jump.png` | Таб "Jump" (жёлтый) - вкладка overview для навигации. |

### Аномалии (Probe Scanner)
| Файл | Описание |
|------|----------|
| `eve_anomaly_ubejishe.png` | Строка аномалии "Убежище Gurista" в списке Probe Scanner. |
| `eve_anomaly_ukrytie.png` | Строка аномалии "Укрытие Gurista" в списке Probe Scanner. |

### Попапы и диалоги
| Файл | Описание |
|------|----------|
| `eve_expedition_popup.png` | Попап экспедиции "База разведки Gurista" с кнопкой "Закрыть". |

---

## Соглашение об именовании

Формат: `eve_{module}_{element}_{state}.png`

- `eve_` - префикс проекта
- `{module}` - модуль/контекст (hud, overview, anomaly, button и т.д.)
- `{element}` - конкретный элемент
- `{state}` - состояние (опционально: active, inactive, empty, full)

### Примеры
```
eve_hud_anchor.png           - anchor элемент HUD
eve_overview_empty.png       - пустой overview
eve_tab_pvp_foe.png          - таб PvP Foe
eve_anomaly_ubejishe.png     - аномалия "Убежище"
eve_gun_active.png           - пушка в активном состоянии
eve_cargo_full.png           - полный карго
```

---

## Использование в коде

```python
from eve import click_on_image, is_visible

# Проверка пустого overview
if is_visible("eve_overview_empty.png"):
    print("Грид чист, целей нет")

# Клик по табу
click_on_image("eve_tab_pvp_foe.png")

# Поиск аномалии
click_on_image("eve_anomaly_ubejishe.png")
```

---

## Добавление новых ассетов

1. Пользователь делает скриншот `Win+Shift+S` → `inbox/`
2. Claude смотрит изображение через `Read("inbox/...")`
3. Claude переименовывает по соглашению и копирует в `assets/`
4. Claude очищает `inbox/`
5. Добавить описание в эту таблицу
