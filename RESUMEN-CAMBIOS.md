# Aspectos Importantes de la Librería DL_Track_US

Este documento resume los componentes clave y el flujo de ejecución para el análisis automático de imágenes estáticas dentro del paquete `DL_Track_US`.
El diagrama de flujo se encuentra en Zotero/ Su Articulo de revista Academica/ Archivos adjuntos.
---

### 1. Interfaz Gráfica de Usuario (GUI)

-   **Módulo Principal de la GUI:** `DL_Track_US/DL_Track_US_GUI.py`
    -   Este script es el punto de entrada para lanzar la interfaz gráfica principal de la aplicación.
    -   Se encarga de construir la ventana, los botones, los campos de entrada y de orquestar las llamadas a las funciones de backend cuando el usuario interactúa con la aplicación.

### 2. Orquestación del Análisis de Imágenes Estáticas

-   **Módulo Organizador:** `DL_Track_US/gui_helpers/calculate_architecture.py`
    -   Actúa como el "director de orquesta" para el análisis de un lote de imágenes estáticas.
    -   Su función principal es preparar todas las variables, configuraciones y rutas de archivos necesarias antes de iniciar el procesamiento real.

-   **Función Orquestadora Principal:** `calculateBatch()`
    -   Ubicada dentro de `calculate_architecture.py`, esta es la función más relevante que se invoca desde la GUI para el análisis automático por lotes.
    -   **Responsabilidades Clave:**
        -   Implementa las configuraciones de parámetros seleccionadas por el usuario.
        -   Itera sobre cada imagen en el directorio especificado.
        -   Llama a la función de cálculo central (`doCalculations`) para cada imagen.
        -   Agrega los resultados de cada imagen.
        -   **Genera los archivos de salida finales:**
            -   Un documento `.xlsx` (Excel) con todos los resultados numéricos.
            -   Un documento `.pdf` que contiene las imágenes de visualización de cada análisis.

### 3. El Núcleo del Procesamiento de Imagen: La Función `doCalculations()`

Dentro del flujo iniciado por `calculateBatch()`, la función **`doCalculations()`** es el componente más importante y central. Contiene toda la lógica fundamental y la secuencia de algoritmos de procesamiento de imagen y geometría para analizar una **única imagen**.

#### Responsabilidades Detalladas de `doCalculations()`:

1.  **Uso de Modelos de Deep Learning**
    -   Es la única función que llama directamente a `model_apo.predict()` y `model_fasc.predict()`. Este es el primer y más crucial paso del análisis automático para obtener las máscaras de segmentación.

2.  **Procesamiento Completo de Aponeurosis**
    -   Realiza una secuencia robusta para refinar la detección de las aponeurosis:
        -   **Umbralización:** Convierte la máscara de probabilidad del modelo en una imagen binaria.
        -   **Detección de Contornos:** Usa `cv2.findContours` para delinear las áreas detectadas.
        -   **Filtrado:** Elimina contornos pequeños y ruidosos y los ordena espacialmente.
        -   **Refinamiento Morfológico:** Aplica `skeletonize`, `dilate` y `erode` para obtener líneas de aponeurosis limpias y continuas.
        -   **Extracción de Bordes:** Utiliza `contourEdge()` para aislar los bordes superior e inferior de las aponeurosis.
        -   **Suavizado:** Aplica un filtro `savgol_filter` para obtener curvas suaves y matemáticamente manejables.

3.  **Modelado y Extrapolación Geométrica**
    -   Es responsable de ajustar modelos lineales (usando `np.polyfit`) a los bordes de las aponeurosis y los fascículos.
    -   Esto permite **extrapolar** las estructuras más allá del campo de visión de la imagen, una técnica clave para medir fascículos parcialmente visibles.

4.  **Cálculo de Parámetros de Arquitectura Muscular**
    -   **Grosor Muscular (`midthick`):** Mide la distancia entre las aponeurosis en la región central.
    -   **Longitud del Fascículo (`fasc_l`):** Calcula la distancia euclidiana entre los puntos de intersección del fascículo extrapolado con las aponeurosis extrapoladas.
    -   **Ángulo de Pennación (`pennation`):** Calcula el ángulo entre la línea del fascículo y la línea de la aponeurosis profunda en el punto de inserción.

5.  **Generación de la Visualización**
    -   Crea el objeto `fig` de Matplotlib, que es la imagen de salida visual principal.
    -   Esta figura muestra la imagen de ultrasonido original con las aponeurosis y los fascículos detectados superpuestos, proporcionando una validación visual inmediata del análisis.
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
  
4.  **Problema mascara ROI:
    La función `doCalculations_custom` en `DL_Track_US/gui_helpers/do_calculations.py` es responsable de calcular los parámetros de la arquitectura muscular a partir de imágenes de ultrasonido. Parte de este proceso implica la creación de una máscara binaria de la región de interés (ROI) entre las aponeurosis superficial y profunda.
    El error se encuentra en la sección del código que genera la `ex_mask`. La lógica asume incorrectamente que las coordenadas x de las aponeurosis superior e inferior están alineadas.

    El código problemático es:

    ```python
    ex_mask = np.zeros(thresh.shape, np.uint8)
    ex_1 = 0
    ex_2 = np.minimum(len(low_x), len(upp_x))
    
    for ii in range(ex_1, ex_2):    #Barrido columna por columna
        ymin = int(np.floor(upp_y_new[ii]))
        ymax = int(np.ceil(low_y_new[ii]))
    
        ex_mask[:ymin, ii] = 0    #Sobre la apo. superficial
        ex_mask[ymax:, ii] = 0    #Debajo de la apo. profunda
        ex_mask[ymin:ymax, ii] = 255    #Entre las apos.
    ```
    
    El bucle itera desde `0` hasta `min(len(low_x), len(upp_x))`, utilizando la variable de bucle `ii` como índice tanto para `upp_y_new` como para `low_y_new`. Sin embargo, no se garantiza que `upp_x` y `low_x` tengan la misma coordenada x inicial o la misma longitud. Esto significa que `upp_x[ii]` y `low_x[ii]` podrían corresponder a diferentes columnas en la imagen, provocando un desplazamiento en la máscara generada.
    
    ### Solución Propuesta
    
    Para solucionar esto, la lógica de generación de la máscara debe actualizarse para mapear correctamente las coordenadas y de las aponeurosis a las coordenadas x correspondientes en la imagen.
    
    La solución propuesta implica los siguientes pasos:
    
    1.  Encontrar el rango superpuesto de coordenadas x entre las dos aponeurosis.
    2.  Crear funciones de interpolación para ambas aponeurosis para obtener las coordenadas y para cualquier coordenada x dada.
    3.  Iterar a través de las coordenadas x superpuestas y rellenar la máscara columna por columna.
    
    Este es el código corregido:
    
    ```python
    # Creacion de mascara ROI que solo contenga el Musculo limitado por sus aponeurosis
    ex_mask = np.zeros(thresh.shape, np.uint8)
    
    # Crear funciones de interpolación para ambas aponeurosis
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))
    
    # Determinar el rango x superpuesto
    start_x = int(max(np.min(upp_x), np.min(low_x)))
    end_x = int(min(np.max(upp_x), np.max(low_x)))
    
    for x in range(start_x, end_x):
        ymin = int(np.floor(f_upp(x)))
        ymax = int(np.ceil(f_low(x)))
    
        # Asegurarse de que ymin e ymax estén dentro de los límites de la imagen
        ymin = max(0, ymin)
        ymax = min(ex_mask.shape[0], ymax)
    
        ex_mask[ymin:ymax, x] = 255
    ```
    Este cambio asegurará que la máscara se genere correctamente, alineándose con las aponeurosis en la imagen original.


## Puntos Clave del Procesamiento de Aponeurosis y ROI:

El procesamiento central de las aponeurosis, que incluye la segmentación de la imagen, la detección de contornos con `contourEdge`, el suavizado de las coordenadas con `savgol_filter`, y la creación de la máscara `ex_mask` (ROI), se encuentra principalmente en estas secciones del código:

*   Procesamiento de imagen, obtención y suavizado de bordes de aponeurosis: [Líneas 1038-1053](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1038-L1053)
*   Creación de la máscara de la región de interés `ex_mask`: [Líneas 1062-1072](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1062-L1072)

El propósito de estos cambios es facilitar el uso de las coordenadas de las aponeurosis y la máscara ROI para análisis y visualizaciones posteriores directamente desde la llamada a la función.
