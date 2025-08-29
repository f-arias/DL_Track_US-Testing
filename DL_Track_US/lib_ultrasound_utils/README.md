# Módulos de Análisis Personalizado para DL_Track_US

Este directorio contiene módulos personalizados y herramientas específicas que se han desarrollado para extender o complementar la funcionalidad principal de la librería `DL_Track_US`.

El objetivo es mantener el código original de la librería intacto mientras se permite la adición de nuevas funcionalidades, pruebas y flujos de trabajo de análisis.

---

## Módulos en este Directorio

### 1. `US_manual_tools.py`

Este es el módulo principal en esta carpeta y ha sido movido aquí para separarlo de la lógica central de la GUI.

**Propósito Principal:**
El módulo `US_manual_tools.py` proporciona herramientas para procesar una máscara de aponeurosis (generalmente creada manualmente) de una imagen de ultrasonido y generar una máscara de Región de Interés (ROI) que delimita el área del músculo.

**Funciones Clave:**
*   `process_aponeurosis_mask`: Una función directa y eficiente, ideal para procesar máscaras de aponeurosis limpias y de alta calidad que no requieren pre-procesamiento extenso.
*   `process_aponeurosis_mask_comprehensive`: Una versión más robusta y completa, diseñada para manejar máscaras que pueden tener ruido o discontinuidades (como las generadas por un modelo automático). Incluye pasos adicionales para fusionar contornos y refinar morfológicamente las líneas de aponeurosis.
*   `overlay_apo_mask`: Una utilidad para superponer la máscara de aponeurosis sobre la imagen original de ultrasonido, permitiendo una validación visual rápida.

---

## Contexto General del Proyecto `DL_Track_US`

Este trabajo se enmarca dentro del proyecto `DL_Track_US`, cuyo objetivo es el análisis automático de imágenes estáticas de ultrasonido muscular. El flujo de trabajo general, descrito en el `README.md` principal, implica:
1.  **Segmentación con CNNs**: Se usan modelos de Deep Learning (`model_apo` y `model_fasc`) para identificar aponeurosis y fascículos.
2.  **Procesamiento y Refinamiento**: Las máscaras generadas se procesan para extraer contornos, filtrar ruido y suavizar las líneas.
3.  **Cálculo de Parámetros**: Se calculan métricas clave de la arquitectura muscular como la longitud del fascículo (FL), el ángulo de pennación (PA) y el grosor muscular (MT).

Los módulos en esta carpeta `lib_ultrasound_utils` pueden ser utilizados como parte de flujos de trabajo alternativos o para generar datos de referencia (ground truth) para estos análisis automáticos.

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
| `hausdorff_distance()`   | Distancia de Hausdorff                | Mide el error máximo entre los contornos de las dos máscaras.                       |
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

print(f"Coeficiente de Dice: {dice:.4f}")
print(f"Índice de Jaccard (IoU): {iou:.4f}")
```
