# Módulos de Análisis Personalizado para ASSIST, SMA, DL_Tracks y Ground Truth

Los módulos en esta carpeta `lib_ultrasound_utils` pueden ser utilizados como parte de flujos de trabajo alternativos o para generar datos de referencia (ground truth) para estos análisis automáticos.

El objetivo es mantener el código original de la librería intacto mientras se permite la adición de nuevas funcionalidades, pruebas y flujos de trabajo de análisis.

*NOTA: EL fichero lib_ultrasound_utils se encuentra en los repositorios DL_track_US-testing , Algoritmo ASSIST y SMA-testing , en ASSIST estara la version mas reciente*

---

## Índice

1. [Contexto General del Proyecto](#contexto-general-del-proyecto-)
2. [Módulos en este Directorio](#módulos-en-este-directorio)
    * [`US_manual_tools.py`](#1-us_manual_toolspy)
        * [Introducción](#introducción)
        * [Dependencias](#dependencias)
        * [Funciones del Módulo](#funciones-del-módulo)
            * [`calculate_musa_thickness`](#calculate_musa_thickness)
            * [`process_aponeurosis_mask`](#process_aponeurosis_mask)
            * [`process_aponeurosis_mask_comprehensive`](#process_aponeurosis_mask_comprehensive)
            * [`overlay_apo_mask`](#overlay_apo_mask)
        * [Diferencias Clave entre las Funciones de Procesamiento](#diferencias-clave-entre-las-funciones-de-procesamiento)
        * [Flujo de Trabajo Detallado](#flujo-de-trabajo-detallado)
    * [`US_metrics.py`](#2-us_metricspy)

---

## Contexto general del proyecto 

...
---

## Módulos en este Directorio

### 1. `US_manual_tools.py`

Este es el módulo principal en esta carpeta y ha sido movido aquí para separarlo de la lógica central de la GUI. Proporciona un conjunto de herramientas y funciones de ayuda para el análisis manual y el etiquetado de imágenes de ultrasonido musculoesquelético.

Este módulo complementa los métodos de análisis automático (basados en CNN) de `DL_Track_US`, ofreciendo una alternativa o un método de validación ("gold standard") controlado por el usuario.

#### Introducción

El objetivo principal de este módulo es proporcionar herramientas para el cálculo del grosor muscular con el método MUSA, así como procesar máscaras de aponeurosis de una imagen de ultrasonido para generar una máscara de Región de Interés (ROI) que delimita el músculo. El módulo ofrece varias funciones para este propósito, cada una adaptada a diferentes necesidades y tipos de máscaras de entrada.

#### Dependencias

El script depende de varias librerías de Python para su funcionamiento:
*   **OpenCV (`cv2`)**: Utilizada para todas las operaciones de visión por computadora, como detección de contornos, redimensionamiento y superposición.
*   **NumPy (`np`)**: Fundamental para la manipulación de arrays, ajuste de polinomios y operaciones numéricas.
*   **ImageIO**: Empleada para leer formatos de imagen.
*   **SciPy (`scipy.signal.savgol_filter`)**: Para suavizar las líneas de las aponeurosis detectadas.
*   **Scikit-image (`skimage.morphology.skeletonize`)**: Utilizada para operaciones morfológicas, específicamente para refinar máscaras ruidosas.

#### Funciones del Módulo

##### `calculate_musa_thickness`

Calcula el Grosor Muscular utilizando el método MUSA (Muscle Ultrasound Analysis). Basado en la "Métrica de Distancia de Línea Central" descrita por Caresio et al. (2017).

El algoritmo realiza los siguientes pasos detallados:
1.  Ajusta modelos lineales (líneas rectas) a los puntos de las aponeurosis proporcionados usando regresión lineal.
2.  Calcula la línea central geométrica (bisectriz) entre las dos líneas resultantes.
3.  Define cuerdas perpendiculares a la línea central a intervalos regulares a lo largo del eje X.
4.  Encuentra las intersecciones de estas cuerdas con las aponeurosis superficial y profunda.
5.  Calcula la longitud de cada cuerda (distancia Euclidiana) y retorna el promedio y la desviación estándar, permitiendo la salida en píxeles ('pp') o milímetros ('mm').

##### `process_aponeurosis_mask`

Procesa una máscara de aponeurosis para crear una máscara de ROI.

Esta función está optimizada para procesar máscaras de aponeurosis generadas manualmente. Es una versión directa y eficiente. Permite que el usuario ingrese ya sea la ruta de la máscara o bien un ndarray de la misma directamente en la función, para mayor flexibilidad. Asume que la máscara de entrada es una representación limpia y no requiere un preprocesamiento extenso, es decir:
*   Las aponeurosis están claramente definidas y no contienen ruido.
*   No hay necesidad de fusionar contornos, ya que las aponeurosis son líneas continuas.
*   El refinamiento morfológico es redundante, ya que la máscara ya es una representación ideal.

##### `process_aponeurosis_mask_comprehensive`

Procesa una máscara de aponeurosis para crear una máscara de ROI con un preprocesamiento completo.

Esta función es una versión más robusta y completa, diseñada para manejar máscaras que pueden contener ruido o discontinuidades, como las generadas automáticamente por modelos de segmentación. Al igual que la función simplificada, permite ingresar tanto la ruta de la máscara como un ndarray. Incluye pasos adicionales vitales:
*   Lógica para reordenar puntos de contorno y fusionar contornos cercanos que se hayan cortado.
*   Aplica esqueletización (con `skeletonize`) y operaciones morfológicas de dilatación y erosión para refinar las líneas de las aponeurosis antes de calcular la ROI.

##### `overlay_apo_mask`

Una utilidad para superponer una máscara de aponeurosis sobre una imagen de ultrasonido con una opacidad y color personalizables.

Permite una validación visual rápida de las máscaras generadas, admitiendo tanto las rutas de los archivos (str) como los arrays correspondientes (np.ndarray) de la imagen original y la máscara de aponeurosis como parámetros de entrada.
*   **Opacidad**: Acepta un valor flotante entre 0.0 y 1.0 (por defecto 0.5).
*   **Color**: Acepta 'Rojo', 'Verde' o 'Azul' como entrada de color (por defecto 'Verde').

#### Diferencias Clave entre las Funciones de Procesamiento

La principal diferencia radica en el nivel de preprocesamiento:

*   **`process_aponeurosis_mask`**:
    *   Es más directa y eficiente.
    *   No realiza fusión de contornos ni refinamiento morfológico.
    *   Ideal para máscaras manuales de alta calidad.

*   **`process_aponeurosis_mask_comprehensive`**:
    *   Incluye lógica para reordenar puntos de contorno y fusionar contornos cercanos.
    *   Aplica esqueletización y operaciones morfológicas para refinar las aponeurosis.
    *   Recomendada para máscaras automáticas o ruidosas.

***Nota: Una diferencia clave, se observa que la función más robusta `_comprehensive` abarca más área en la imagen, y no necesariamente pertenece al área del ROI del musculoesquelético (ME). Sino, de los costados, es decir del marco de información que no forma parte como tal de la imagen de US del paciente.***

#### Flujo de Trabajo Detallado

Ambas funciones de procesamiento de máscaras siguen un flujo de trabajo similar, pero `process_aponeurosis_mask_comprehensive` incluye pasos adicionales:

1.  **Carga y Preprocesamiento Básico**: Ambas funciones leen la imagen de entrada, la convierten a escala de grises si es necesario, y la binarizan mediante umbralización.
2.  **Detección de Contornos**: Ambas detectan los contornos externos y los filtran por longitud para eliminar ruido pequeño.
3.  **Fusión y Refinamiento (Solo `_comprehensive`)**: La versión completa ordena los puntos, une contornos discontinuos cercanos, y aplica operaciones morfológicas (esqueletización, dilatación, erosión) para reconstruir líneas de aponeurosis rotas.
4.  **Extracción de Bordes y Suavizado**: Ambas ordenan los contornos resultantes, extraen el borde inferior de la aponeurosis superior y el borde superior de la aponeurosis inferior, y suavizan las líneas resultantes usando un filtro Savitzky-Golay.
5.  **Generación de la Máscara ROI**: Ambas ajustan un polinomio de segundo grado a los bordes suavizados y rellenan el área vertical entre estos dos límites para cada posición horizontal, creando la región de interés final.
6.  **Retorno**: Ambas devuelven la máscara ROI como un array de NumPy.

---

### 2. `US_metrics.py`

Este módulo proporciona un conjunto de herramientas estandarizadas y robustas para la evaluación cuantitativa de las máscaras de segmentación.

**Propósito Principal:**
Su objetivo es comparar el rendimiento de un modelo de segmentación (como el de `DL_Track_US`) con una máscara de referencia o "ground truth" (ej. delineada manualmente). Permite una evaluación objetiva mediante métricas estándar en la literatura de visión por computador.

**Métricas Implementadas:**

| Función                  | Métrica                               | Descripción Breve                                                                   |
| :----------------------- | :------------------------------------ | :---------------------------------------------------------------------------------- |
| `dice_coefficient()`     | Coeficiente de Dice (F1-Score)        | La métrica más común para superposición, sensible al tamaño de las máscaras.        |
| `jaccard_index()`        | Índice de Jaccard (IoU)               | Mide la intersección sobre la unión; penaliza más los errores que el Dice.          |
| `sensitivity()`          | Sensibilidad (Recall)                 | Mide la fracción de la máscara real que fue correctamente identificada.             |
| `precision()`            | Precisión                             | Mide qué tan "limpia" es la predicción, es decir, cuántos píxeles predichos son correctos. |
| `hausdorff_distance()`   | Distancia de Hausdorff                | Mide el error máximo entre contornos. Permite elegir la librería (`scipy`/`skimage`) y el método. |
| `cohen_kappa()`          | Kappa de Cohen                        | Evalúa la concordancia entre las dos máscaras, corrigiendo el acuerdo por azar.     |

**Ejemplo de Uso:**
```python
import numpy as np
from DL_Track_US.lib_ultrasound_utils import US_metrics

# Crear máscaras binarias de ejemplo
mascara_referencia = np.array([[1, 1, 0], [1, 1, 0]], dtype=np.uint8)
mascara_prueba = np.array([[1, 1, 1], [1, 0, 0]], dtype=np.uint8)

# Calcular métricas
dice = US_metrics.dice_coefficient(mascara_referencia, mascara_prueba)
iou = US_metrics.jaccard_index(mascara_referencia, mascara_prueba)

# Calcular distancia de Hausdorff con diferentes opciones
h_scipy = US_metrics.hausdorff_distance(mascara_referencia, mascara_prueba, library='scipy')
h_skimage = US_metrics.hausdorff_distance(mascara_referencia, mascara_prueba, library='skimage', method='modified')


print(f"Coeficiente de Dice: {dice:.4f}")
print(f"Índice de Jaccard (IoU): {iou:.4f}")
print(f"Hausdorff (SciPy): {h_scipy:.4f}")
print(f"Hausdorff (scikit-image, modified): {h_skimage:.4f}")
```
