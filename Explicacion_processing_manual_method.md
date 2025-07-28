# Explicación del Módulo `processing_manual_method.py`

Este documento detalla el funcionamiento del módulo `processing_manual_method_reference.py`, diseñado para procesar una máscara de aponeurosis de una imagen de ultrasonido y generar una máscara de Región de Interés (ROI) que delimita el músculo.

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

El objetivo de este módulo es replicar la lógica de la función `doCalculations_custom` del archivo `do_calculations.py`, pero aplicado a una única máscara de aponeurosis generada manualmente que contiene tanto la aponeurosis superficial como la profunda. A partir de una única imagen (máscara), el script genera una máscara binaria que define la región del músculo entre ellas.

### Dependencias

El script utiliza las siguientes librerías de Python:

*   **OpenCV (`cv2`)**: Para operaciones de visión por computadora.
*   **NumPy (`np`)**: Para manipulación de arrays.
*   **ImageIO**: Para leer formatos de imagen.
*   **SciPy (`scipy.signal.savgol_filter`)**: Para suavizar las líneas de las aponeurosis.
*   **Scikit-image (`skimage.morphology.skeletonize`)**: Para operaciones morfológicas.

### Funciones Importadas

Para evitar la duplicación de código, el script importa las siguientes funciones del módulo `do_calculations.py`:

*   **`sortContours`**: Ordena los contornos.
*   **`contourEdge`**: Extrae el borde de un contorno.

### Función Principal

#### `process_aponeurosis_mask`

Esta es la función central del módulo. Acepta una única ruta de archivo a la máscara de aponeurosis y orquesta todo el proceso para generar el ROI.

### Flujo de Trabajo del Procesamiento

#### Carga y Preprocesamiento de la Máscara

1.  **Lectura de Imagen**: La máscara se lee desde la ruta proporcionada.
2.  **Conversión a Escala de Grises**: Si la imagen es RGB, se convierte a escala de grises.
3.  **Binarización**: La máscara se binariza.

#### Detección y Fusión de Contornos

1.  **Detección y Filtrado**: Se detectan los contornos y se filtran por longitud.
2.  **Ordenamiento y Fusión**: Los contornos se ordenan y se fusionan si están cerca.

#### Refinamiento de Aponeurosis

1.  **Esqueletización y Morfología**: Se aplican operaciones morfológicas para refinar las aponeurosis.

#### Extracción de Bordes y Suavizado

1.  **Extracción y Suavizado**: Se extraen los bordes relevantes y se suavizan.

#### Generación de la Máscara ROI

1.  **Ajuste y Relleno**: Se ajusta un polinomio a las aponeurosis y se rellena el área intermedia para crear el ROI.
2.  **Retorno**: La función devuelve la máscara ROI.
