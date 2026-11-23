# Библиотечные данные KiCad

Посадочные места в `footprints/` и модели в `models/` получены из официального дистрибутива KiCad 9.0.7. Авторы: сообщество библиотек KiCad. Лицензия: CC BY-SA 4.0 с исключением для электронных проектов и получаемых из них файлов. Эта лицензия сохраняется для включённой коллекции библиотечных файлов; собственная схема и разводка лицензированы отдельно.

В посадочных местах изменены только пути к 3D-моделям: вместо глобального каталога KiCad используется `${KIPRJMOD}/models/`. Геометрия посадочных мест и моделей не изменялась.

Включены:

- `Resistor_SMD:R_0805_2012Metric` и его STEP-модель;
- `Capacitor_SMD:C_0805_2012Metric` и его STEP-модель;
- `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` и его STEP-модель;
- `TestPoint:TestPoint_Pad_D2.0mm`;
- `MountingHole:MountingHole_2.7mm_M2.5`.

Лицензионные документы сохранены в `third_party_licenses/`. Источники: [правила лицензирования KiCad](https://www.kicad.org/libraries/license/), [kicad-footprints](https://gitlab.com/kicad/libraries/kicad-footprints), [kicad-packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D).
