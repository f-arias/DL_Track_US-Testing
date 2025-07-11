# Nota de Cambios en `doCalculations_custom`

Se han realizado modificaciones en la función `doCalculations_custom` ubicada en el archivo `DL_Track_US/gui_helpers/do_calculations.py` para mejorar el acceso a los datos de las aponeurosis y la región de interés muscular.

## Cambios Realizados:

1.  **Nuevas Variables de Salida:**
    Se han añadido cinco nuevas variables al `return` de la función. Estas variables exponen:
    *   Las coordenadas X e Y procesadas y suavizadas de las aponeurosis superficial (superior) e profunda (inferior).
    *   Una máscara binaria (`mask_roi`) que define la región de interés entre las aponeurosis.

    Las variables son:
    *   `mask_roi`: Máscara binaria (NumPy array) de la región muscular.
    *   `upp_x_apo`: Coordenadas X de la aponeurosis superior (NumPy array).
    *   `upp_y_apo`: Coordenadas Y suavizadas de la aponeurosis superior (NumPy array).
    *   `low_x_apo`: Coordenadas X de la aponeurosis inferior (NumPy array).
    *   `low_y_apo`: Coordenadas Y suavizadas de la aponeurosis inferior (NumPy array).

    Estas variables se definen y retornan en las siguientes secciones del código:
    *   Definición de `ex_mask` (usada para `mask_roi`): [Líneas 1062](https://github.com/f-arias/DL_Track_US-Testing/blob/b2a15fb9ab8be11295f24ef4b2b9c22cfd8f9194/DL_Track_US/gui_helpers/do_calculations.py#L1062)
    *   Copia de variables internas para la salida (`mask_roi`, `upp_x_apo`, etc.): [Líneas 1355-1360](https://github.com/f-arias/DL_Track_US-Testing/blob/b2a15fb9ab8be11295f24ef4b2b9c22cfd8f9194/DL_Track_US/gui_helpers/do_calculations.py#L1355-L1360)
    *   Sentencia `return` actualizada (9 variables en total): [Líneas 1362-1372](https://github.com/f-arias/DL_Track_US-Testing/blob/b2a15fb9ab8be11295f24ef4b2b9c22cfd8f9194/DL_Track_US/gui_helpers/do_calculations.py#L1362-L1372)
    *   Sentencias `return None` actualizadas para devolver 9 `None`s en caso de fallo:
        *   [Línea 963](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L963)
        *   [Línea 1376](https://github.com/f-arias/DL_Track_US-Testing/blob/b2a15fb9ab8be11295f24ef4b2b9c22cfd8f9194/DL_Track_US/gui_helpers/do_calculations.py#L1376)

2.  **Actualización del Docstring:**
    El docstring de la función `doCalculations_custom` ha sido expandido para incluir la descripción detallada de las cinco nuevas variables retornadas y para asegurar que la tupla de retorno refleje nueve elementos.
    *   Docstring actualizado (ver sección `Returns`): [Líneas 782-878](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L782-L878)

3.  **Corrección de Sintaxis y Mejoras Menores:**
    *   Se corrigió un error de sintaxis en la sentencia `return` (una coma faltante).
    *   Se mejoró la legibilidad de una condición booleana (`if filter_fasc`).

## Puntos Clave del Procesamiento de Aponeurosis y ROI:

El procesamiento central de las aponeurosis, que incluye la segmentación de la imagen, la detección de contornos con `contourEdge`, el suavizado de las coordenadas con `savgol_filter`, y la creación de la máscara `ex_mask` (ROI), se encuentra principalmente en estas secciones del código:

*   Procesamiento de imagen, obtención y suavizado de bordes de aponeurosis: [Líneas 1038-1053](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1038-L1053)
*   Creación de la máscara de la región de interés `ex_mask`: [Líneas 1062-1072](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1062-L1072)

El propósito de estos cambios es facilitar el uso de las coordenadas de las aponeurosis y la máscara ROI para análisis y visualizaciones posteriores directamente desde la llamada a la función.
