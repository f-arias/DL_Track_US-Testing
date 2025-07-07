# Nota de Cambios en `doCalculations_custom`

Se han realizado modificaciones en la función `doCalculations_custom` ubicada en el archivo `DL_Track_US/gui_helpers/do_calculations.py`.

## Cambios Realizados:

1.  **Nuevas Variables de Salida:**
    Se han añadido cuatro nuevas variables al `return` de la función `doCalculations_custom`. Estas variables proporcionan las coordenadas X e Y procesadas y suavizadas de las aponeurosis superficial (superior) e profunda (inferior).
    *   `upp_x_apo`: Copia de las coordenadas X de la aponeurosis superior (`upp_x`).
    *   `upp_y_apo`: Copia de las coordenadas Y suavizadas de la aponeurosis superior (`upp_y_new`).
    *   `low_x_apo`: Copia de las coordenadas X de la aponeurosis inferior (`low_x`).
    *   `low_y_apo`: Copia de las coordenadas Y suavizadas de la aponeurosis inferior (`low_y_new`).

    Estas variables se pueden encontrar en las siguientes líneas (los números de línea pueden variar ligeramente si el archivo es modificado posteriormente):
    *   Definición y copia de variables: [Línea ~1303-1306](https://github.com/alexjaraUC/DL_Track_US/blob/Custom-MT/DL_Track_US/gui_helpers/do_calculations.py#L1303-L1306)
    *   Sentencia `return` actualizada: [Línea ~1310-1321](https://github.com/alexjaraUC/DL_Track_US/blob/Custom-MT/DL_Track_US/gui_helpers/do_calculations.py#L1310-L1321)
    *   Sentencia `return None` actualizada en caso de fallo: [Línea ~1326](https://github.com/alexjaraUC/DL_Track_US/blob/Custom-MT/DL_Track_US/gui_helpers/do_calculations.py#L1326)

2.  **Actualización del Docstring:**
    El docstring de la función `doCalculations_custom` ha sido actualizado para reflejar estas nuevas variables de salida y proporcionar una descripción de cada una.
    *   Docstring actualizado: [Línea ~825-854](https://github.com/alexjaraUC/DL_Track_US/blob/Custom-MT/DL_Track_US/gui_helpers/do_calculations.py#L825-L854)

## Puntos de Interés en el Procesamiento de Aponeurosis:

El procesamiento principal de las aponeurosis, incluyendo la detección de contornos, el suavizado y la definición de `upp_x`, `upp_y_new`, `low_x`, `low_y_new`, ocurre alrededor de estas secciones del código:

*   Obtención de los bordes de las aponeurosis (`contourEdge`) y suavizado (`savgol_filter`): [Líneas ~1007-1015](https://github.com/alexjaraUC/DL_Track_US/blob/Custom-MT/DL_Track_US/gui_helpers/do_calculations.py#L1007-L1015)

Estos cambios tienen como objetivo facilitar el acceso a las coordenadas directas de las aponeurosis para análisis posteriores o visualizaciones personalizadas.
