# Nota de Cambios en `doCalculations_custom`

Se han realizado modificaciones en la función `doCalculations_custom` ubicada en el archivo `DL_Track_US/gui_helpers/do_calculations.py` para mejorar el acceso a los datos de las aponeurosis.

## Cambios Realizados:

1.  **Nuevas Variables de Salida:**
    Se han añadido cuatro nuevas variables al `return` de la función. Estas variables exponen las coordenadas X e Y procesadas y suavizadas de las aponeurosis superficial (superior) e profunda (inferior), que anteriormente solo se usaban internamente.

    *   `upp_x_apo`: Coordenadas X de la aponeurosis superior.
    *   `upp_y_apo`: Coordenadas Y suavizadas de la aponeurosis superior.
    *   `low_x_apo`: Coordenadas X de la aponeurosis inferior.
    *   `low_y_apo`: Coordenadas Y suavizadas de la aponeurosis inferior.

    Estas variables se definen y retornan en las siguientes secciones del código:
    *   Copia de variables internas para la salida: [Líneas 1314-1318](https://github.com/f-arias/DL_Track_US-Testing/blob/2bb02b13cfbe4265f2accba36a0a9447e19bc4d3/DL_Track_US/gui_helpers/do_calculations.py#L1314-L1318)
    *   Sentencia `return` actualizada con las nuevas variables: [Líneas 1320-1329](https://github.com/f-arias/DL_Track_US-Testing/blob/2bb02b13cfbe4265f2accba36a0a9447e19bc4d3/DL_Track_US/gui_helpers/do_calculations.py#L1320-L1329)
    *   Sentencia `return None` actualizada para mantener consistencia en caso de fallo: [Línea 1333](https://github.com/f-arias/DL_Track_US-Testing/blob/2bb02b13cfbe4265f2accba36a0a9447e19bc4d3/DL_Track_US/gui_helpers/do_calculations.py#L1333)

2.  **Actualización del Docstring:**
    El docstring de la función ha sido expandido para incluir la descripción detallada de las nuevas variables retornadas, explicando qué representa cada una.
    *   Docstring actualizado: [Líneas 770-861](https://github.com/f-arias/DL_Track_US-Testing/blob/2bb02b13cfbe4265f2accba36a0a9447e19bc4d3/DL_Track_US/gui_helpers/do_calculations.py#L770-L861)

## Puntos Clave del Procesamiento de Aponeurosis:

El procesamiento central de las aponeurosis, que incluye la segmentación de la imagen, la detección de contornos con `contourEdge`, y el suavizado de las coordenadas con `savgol_filter`, se encuentra en esta sección del código:

*   Procesamiento de imagen y obtención de bordes de aponeurosis: [Líneas 911-1020](https://github.com/f-arias/DL_Track_US-Testing/blob/2bb02b13cfbe4265f2accba36a0a9447e19bc4d3/DL_Track_US/gui_helpers/do_calculations.py#L911-L1020)

El propósito de estos cambios es facilitar el uso de las coordenadas de las aponeurosis para análisis y visualizaciones posteriores directamente desde la llamada a la función.
