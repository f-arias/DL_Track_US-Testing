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
