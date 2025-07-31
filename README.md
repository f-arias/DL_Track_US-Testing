# Aspectos Importantes de la Librería DL_Track_US

Este documento resume los componentes clave y el flujo de ejecución para el análisis automático de imágenes estáticas dentro del paquete `DL_Track_US`.
El diagrama de flujo se encuentra en 🗺️[*Diagrama de FLujo*](https://github.com/f-arias/DL_Track_US-Testing/blob/158555c5741e77336c7647cb1f360acb5229c85c/Diagrama%20de%20flujo%20DL_Track_US.html) ,al igual que en Zotero/ Su Articulo de revista Academica/ Archivos adjuntos.

**NOTA: El módulo *DL_Track_US/processing_manual_method.py* para procesar las imágenes de referencia del método manual se explica en [Descripcion](./Descripcion_processing_manual_method.md).**

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

#### Acciones detalladas de `doCalculations()`:

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

## Puntos Clave del Procesamiento de Aponeurosis y ROI:

El procesamiento central de las aponeurosis, que incluye la segmentación de la imagen, la detección de contornos con `contourEdge`, el suavizado de las coordenadas con `savgol_filter`, y la creación de la máscara `ex_mask` (ROI), se encuentra principalmente en estas secciones del código:

*   Procesamiento de imagen, obtención y suavizado de bordes de aponeurosis: [Líneas 1038-1053](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1038-L1053)
*   Creación de la máscara de la región de interés `ex_mask`: [Líneas 1062-1072](https://github.com/f-arias/DL_Track_US-Testing/blob/abbdab46f108c6431bc1b0600d36b0de9154ef1a/DL_Track_US/gui_helpers/do_calculations.py#L1062-L1072)

---
# Registro de Cambios y Guía de Uso: Función `doCalculations_custom`

Este documento sirve como un registro completo y detallado de las modificaciones realizadas a la función `doCalculations` de la librería `DL_Track_US`. Estos cambios han culminado en la creación de una nueva función, **`doCalculations_custom`**, diseñada para mejorar la funcionalidad, precisión y capacidad de análisis externo del algoritmo de detección de arquitectura muscular.

---

## 1. Introducción de `doCalculations_custom`

Para mantener la integridad de la librería original y al mismo tiempo expandir su funcionalidad, se ha creado una nueva función, `doCalculations_custom`. Esta función hereda toda la lógica central de `doCalculations` pero introduce las siguientes mejoras clave:

1.  **Nuevas Variables de Salida:** Expone datos cruciales que antes eran internos, como las coordenadas de las aponeurosis y la máscara de la región de interés (ROI).
2.  **Algoritmo de ROI Mejorado:** Implementa un método más robusto para definir el área del músculo.
3.  **Visualización Enfocada:** La figura de salida ahora muestra la máscara de ROI y el trazado de las aponeurosis, eliminando el ploteo de los fascículos para una validación más clara de la detección.
4.  **Documentación Actualizada:** Incluye un `docstring` revisado y preciso que refleja todos los cambios.

---

## 2. Expansión de las Variables de Salida

El principal motivador de esta actualización fue exponer los datos geométricos clave para análisis externos. La nueva función `doCalculations_custom` ahora devuelve una tupla con **9 elementos**.

### 2.1. Desglose de las Variables de Salida

| Índice | Variable Devuelta     | Tipo de Dato                | Descripción Detallada                                                                                                                                                             |
| :----- | :-------------------- | :-------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0      | `fasc_l`              | `list` de `float`           | Lista con las longitudes calculadas para cada fascículo válido detectado. Las unidades son píxeles o, si se proporciona calibración, milímetros.                          |
| 1      | `pennation`           | `list` de `float`           | Lista con los ángulos de pennación en **grados** para cada fascículo correspondiente.                                                                                    |
| 2      | `x_low`               | `list` de `int`             | Lista de las coordenadas X del punto de inserción de cada fascículo en la **aponeurosis profunda (inferior)**.                                                           |
| 3      | `x_high`              | `list` de `int`             | Lista de las coordenadas X del punto de inserción de cada fascículo en la **aponeurosis superficial (superior)**.                                                          |
| 4      | `midthick`            | `float`                     | Valor único que representa el **grosor del músculo** medido en la región central de la imagen.                                                                            |
| 5      | `ex_mask`             | `np.ndarray`  |               **(Nuevo)** La máscara binaria (`uint8`) que representa la **Región de Interés (ROI)** del músculo, delimitada por las aponeurosis. Los píxeles del músculo tienen valor 255. |
| 6      | `[upp_x, upp_y_new, len(upp_x)]`  | `list`          | **(Nuevo)** Lista con 3 elementos: [array de X, array de Y suavizado, número de puntos] para la **aponeurosis superficial**.                                      |
| 7      | `[low_x, low_y_new, len(low_x)]`  | `list`          | **(Nuevo)** Lista con 3 elementos: [array de X, array de Y suavizado, número de puntos] para la **aponeurosis profunda**.                                        |
| 8      | `fig`                 | `matplotlib.figure.Figure`  | Objeto de la figura de Matplotlib que contiene la visualización completa del análisis. |

---

## 3. Mejora del Algoritmo de la Máscara de Región de Interés (ROI)

La generación de la máscara `ex_mask`, que define el área del músculo, ha sido rediseñada para ser más precisa y robusta. A continuación se detalla y compara el método antiguo con el nuevo.

### 3.1. Método Original (Comentado en el código)

El enfoque original se basaba en iterar directamente sobre los índices de los arrays de coordenadas de las aponeurosis.

#### Código Original:
```python
# ex_mask = np.zeros(thresh.shape, np.uint8)
# ex_1 = 0
# ex_2 = np.minimum(len(low_x), len(upp_x))

# for ii in range(ex_1, ex_2):
#     ymin = int(np.floor(upp_y_new[ii]))
#     ymax = int(np.ceil(low_y_new[ii]))
#     ex_mask[ymin:ymax, ii] = 255
```
#### Análisis del Método Original:
-   **Lógica:** Rellena el área verticalmente, columna por columna, basándose en la correspondencia de los índices de los arrays `upp_y_new` y `low_y_new`.
-   **Debilidad Principal:** La línea `ex_2 = np.minimum(len(low_x), len(upp_x))` limita el rellenado al largo del array de aponeurosis más corto. Si una aponeurosis es detectada en una sección más corta del eje X que la otra, el área donde no se superponen se ignora, resultando en una máscara incompleta.

### 3.2. Nuevo Método Implementado

El nuevo método utiliza un enfoque basado en modelos matemáticos para definir los límites de la máscara, solucionando las limitaciones del método anterior.

#### Código Nuevo y Explicación:
```python
# Inicializa una máscara negra del mismo tamaño que la imagen de entrada.
ex_mask = np.zeros(thresh.shape, np.uint8)

# 1. Se ajusta un polinomio de grado 2 (una parábola) a los puntos de cada aponeurosis.
#    'np.polyfit' encuentra los coeficientes de la curva que mejor se ajusta.
#    'np.poly1d' convierte estos coeficientes en una función matemática.
#    Ahora 'f_upp(x)' devolverá la coordenada Y de la aponeurosis superior para cualquier X.
f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

# 2. Se determina el rango de superposición espacial real en el eje X.
#    'start_x' es la coordenada X más a la izquierda donde AMBAS aponeurosis existen.
#    'end_x' es la coordenada X más a la derecha donde AMBAS aponeurosis existen.
start_x = int(max(np.min(upp_x), np.min(low_x)))
end_x = int(min(np.max(upp_x), np.max(low_x)))

# 3. Se itera píxel por píxel a lo largo del eje X dentro del rango de superposición.
for x in range(start_x, end_x):
    # Para cada columna 'x', se usan las funciones polinómicas para obtener
    # las coordenadas Y interpoladas y suaves de los límites superior (ymin) e inferior (ymax).
    ymin = int(np.floor(f_upp(x)))    # floor redondea hacia abajo
    ymax = int(np.ceil(f_low(x)))     # ceil redondea hacia arriba

    # 4. Salvaguarda para asegurar que las coordenadas no se salgan de los límites de la imagen.
    ymin = max(0, ymin)
    ymax = min(ex_mask.shape, ymax)

    # 5. Se rellena la columna 'x' entre los límites ymin e ymax con el valor 255 (blanco).
    ex_mask[ymin:ymax, x] = 255
```

---

## 4. Nueva Visualización de Salida: Enfoque en Aponeurosis y ROI

La figura generada por `doCalculations_custom` ha sido modificada para centrarse en la validación de las detecciones de las aponeurosis y la Región de Interés (ROI).
Se conservaron pero se comentaron las líneas de código que dibujaban los fascículos y las anotaciones de texto (longitud de fascículo, ángulo de pennación y grosor muscular) para mantener el código original como referencia.

### 4.1. Composición de la Figura

1.  **Fondo:** La imagen de ultrasonido (`img_copy`) se muestra en escala de grises (`cmap='gray'`) como base.
2.  **Trazado de Aponeurosis:** Las líneas de las aponeurosis se superponen a la imagen.
    -   **Función:** `ax.plot()`
    -   **Datos:** Se utilizan los arrays `(upp_x, upp_y_new)` y `(low_x, low_y_new)`.
    -   **Estilo:** La aponeurosis sup. se dibujan con `color="blue"` y la aponeurosis prof. se dibuja con `color="darkgreen" y un grosor de línea de `linewidth=1` para un trazado fino y claro.
3.  **Superposición de la Máscara ROI:** La máscara del músculo se visualiza como una capa semi-transparente para resaltar el area del musculo.
    -   **Lógica:** Se crea una imagen a color vacía (`roi_colored`). Los píxeles correspondientes a la máscara `ex_mask` se colorean de **púrpura** (`[128, 0, 128]`).
    -   **Función:** `ax.imshow(roi_colored, alpha=0.3, ...)`
    -   **Estilo:** La máscara púrpura se superpone con una opacidad del 30% (`alpha=0.3`), permitiendo ver tanto el área de la ROI como la imagen de ultrasonido subyacente.
4.  **Leyenda Mejorada:** La leyenda ha sido movida a la esquina superior izquierda y mejorada para mostrar la correspondencia entre color y término:
    - **Verde Oscuro:** Aponeurosis Profunda
    - **Azul:** Aponeurosis Superficial
    - **Púrpura:** ROI
---
