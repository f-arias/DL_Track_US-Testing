# Explicación Detallada del Módulo `processing_manual_method.py`

Este documento ofrece una explicación exhaustiva del módulo `processing_manual_method.py`, cuyo propósito es procesar una máscara de aponeurosis de una imagen de ultrasonido para generar una máscara de Región de Interés (ROI) que delimita el músculo.

## Outline

1.  [Introducción](#introducción)
2.  [Dependencias](#dependencias)
3.  [Funciones Importadas](#funciones-importadas)
4.  [Función Principal](#función-principal)
    *   [`process_aponeurosis_mask`](#process_aponeurosis_mask)
5.  [Flujo de Trabajo del Procesamiento](#flujo-de-trabajo-del-procesamiento)
    *   [Carga y Preprocesamiento de la Máscara](#carga-y-preprocesamiento-de-la-máscara)
    *   [Detección y Fusión de Contornos](#detección-y-fusión-de-contornos)
    *   [Refinamiento de Aponeurosis](#refinamiento-de-aponeurosis)
    *   [Extracción de Bordes y Suavizado](#extracción-de-bordes-y-suavizado)
    *   [Generación de la Máscara ROI](#generación-de-la-máscara-roi)

---

### Introducción

El objetivo principal de este módulo es replicar y mejorar la lógica de la función `doCalculations_custom` del archivo `do_calculations.py`. Este script está diseñado para trabajar con una única máscara de aponeurosis, generada manualmente, que contiene tanto la aponeurosis superficial como la profunda. A partir de esta imagen de máscara, el script genera una máscara binaria que define con precisión la región del músculo ubicada entre estas dos aponeurosis.

### Dependencias

El script depende de varias librerías de Python para su funcionamiento:

*   **OpenCV (`cv2`)**: Utilizada para todas las operaciones de visión por computadora, como la conversión de color, binarización y detección de contornos.
*   **NumPy (`np`)**: Fundamental para la manipulación de arrays y operaciones numéricas de alto rendimiento.
*   **ImageIO**: Empleada para leer una amplia variedad de formatos de imagen de manera eficiente.
*   **SciPy (`scipy.signal.savgol_filter`)**: Específicamente, se usa el filtro Savitzky-Golay para suavizar las líneas de las aponeurosis, lo que ayuda a eliminar el ruido y a obtener una representación más limpia.
*   **Scikit-image (`skimage.morphology.skeletonize`)**: Utilizada para operaciones morfológicas, en particular, la esqueletización, que reduce las formas a una representación de una sola línea.

### Funciones Importadas

Para mantener el código modular y evitar la duplicación, el script importa las siguientes funciones auxiliares del módulo `do_calculations.py`:

*   **`sortContours`**: Esta función es crucial para ordenar los contornos detectados, lo que es un paso previo indispensable para su correcto procesamiento.
*   **`contourEdge`**: Se utiliza para extraer con precisión el borde superior o inferior de un contorno, lo cual es vital para definir los límites de las aponeurosis.

### Función Principal

#### `process_aponeurosis_mask`

Esta es la función central y orquestadora de todo el módulo. Acepta como entrada la ruta de un archivo de máscara de aponeurosis y ejecuta una serie de pasos para generar la máscara de la ROI final.

### Flujo de Trabajo del Procesamiento

#### Carga y Preprocesamiento de la Máscara

1.  **Lectura de la Imagen**: El proceso comienza leyendo la imagen de la máscara desde la ruta de archivo proporcionada.
2.  **Conversión a Escala de Grises**: Si la imagen de entrada es a color (RGB), se convierte a escala de grises para simplificar el procesamiento.
3.  **Binarización**: La máscara en escala de grises se binariza, convirtiendo todos los píxeles por encima de un umbral a blanco y los demás a negro.

#### Detección y Fusión de Contornos

1.  **Detección y Filtrado de Contornos**: Se utiliza el algoritmo de `findContours` de OpenCV para detectar todos los contornos en la máscara binarizada. Los contornos pequeños, que suelen ser ruido, se filtran basándose en un umbral de longitud (`APO_LENGTH_TRESH`).
2.  **Ordenamiento y Fusión de Contornos**: Los contornos restantes se ordenan y, si están lo suficientemente cerca, se fusionan para formar líneas continuas, representando las aponeurosis.

#### Refinamiento de Aponeurosis

1.  **Esqueletización y Operaciones Morfológicas**: Se aplica la esqueletización para reducir las aponeurosis a líneas de un solo píxel de grosor. Luego, se realizan operaciones de dilatación y erosión para refinar y limpiar estas líneas, eliminando imperfecciones.

#### Extracción de Bordes y Suavizado

1.  **Extracción Precisa de Bordes**: Se extraen los bordes superior e inferior de los contornos refinados, que corresponden a las aponeurosis superficial y profunda.
2.  **Suavizado de los Bordes**: Los bordes extraídos se suavizan utilizando el filtro Savitzky-Golay para eliminar cualquier irregularidad y obtener una curva suave y continua.

#### Generación de la Máscara ROI

1.  **Ajuste Polinomial y Relleno**: Se ajusta un polinomio de segundo grado a cada uno de los bordes suavizados de las aponeurosis. Luego, se rellena el área entre estas dos curvas polinomiales para crear la máscara de la Región de Interés (ROI).
2.  **Retorno de la Máscara**: La función finaliza devolviendo la máscara ROI generada, que representa el área del músculo de interés.
