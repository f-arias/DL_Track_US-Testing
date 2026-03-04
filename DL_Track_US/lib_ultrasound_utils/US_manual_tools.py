# -*- coding: utf-8 -*-
"""
Descripción
-----------
Este módulo proporciona un conjunto de herramientas y funciones de ayuda
para el análisis manual y el etiquetado de imágenes de ultrasonido musculoesquelético.

Este módulo complementa los métodos de análisis automático (basados en CNN) 
de DL_Track_US, ofreciendo una alternativa o un método de validación 
("gold standard") controlado por el usuario.

Este modulo se baso en gran medida al repositorio DL_Track_US
Ritsche, P., Seynnes, O., & Cronin, N. (2023). 
DL_Track_US: a python package to analyse muscle ultrasonography images. 
Journal of Open Source Software, 8(85), 5206. https://doi.org/10.21105/joss.05206

Alcance de las Funciones
------------------------
calculate_musa_thickness(aponeurosis_sup, aponeurosis_deep, scale='pp', pixel_spacing=1.0)
    Calcula el Grosor Muscular utilizando el método MUSA (Muscle Ultrasound Analysis).

process_aponeurosis_mask(mask_path)
    Procesa una máscara de aponeurosis para crear una máscara de ROI.

process_aponeurosis_mask_comprehensive(mask_path)
    Procesa una máscara de aponeurosis con preprocesamiento completo.

overlay_apo_mask(image_apo_path, mask_apo_path, opacity=0.5, color='Verde')
    Superpone una máscara de aponeurosis sobre una imagen de ultrasonido.

Notas
-----
- Una diferencia se observa que la funcion mas robusta "_comprehensive"
abarca mas area en la imagen, y no necesariamente pertenece al area del ROI
del musculoesqueletico(ME). Sino, de los costados, es decir del marco de informacion
que no forma parte como tal de la imagen de US del paciente.

@author: Felipe Arias
"""
# --- Importaciones de Dependencias ---
import cv2
import numpy as np
import imageio
from scipy.signal import savgol_filter
from skimage.morphology import skeletonize
from DL_Track_US.gui_helpers.do_calculations import sortContours, contourEdge
import warnings

# --- Definición de Funciones ---

def calculate_musa_thickness(aponeurosis_sup, aponeurosis_deep, scale='pp', pixel_spacing=1.0):
    """
    Calcula el Grosor Muscular utilizando el método MUSA (Muscle Ultrasound Analysis).
    Basado en la "Métrica de Distancia de Línea Central" descrita por Caresio et al. (2017).

    El algoritmo realiza los siguientes pasos detallados:
    1. Ajusta modelos lineales (líneas rectas) a los puntos de aponeurosis proporcionados.
       Se usa la regresión lineal para obtener la pendiente (m) y el intercepto (c) de la forma y = mx + c.
       (Nota: Caresio et al. usan polinomios; actualmente ASSIST usa líneas Hough, por lo que el ajuste lineal es exacto).

    2. Calcula la línea central geométrica (bisectriz) entre las dos líneas.
       - Se obtienen los ángulos de inclinación de ambas aponeurosis con respecto al eje X usando arctan(m).
       - El ángulo de la línea central es el promedio de estos dos ángulos: theta_c = (theta_s + theta_d) / 2.
       - Si las líneas son paralelas, el intercepto c_c es el promedio de los interceptos.
       - Si las líneas se cruzan, se calcula el punto de intersección y se fuerza a la línea central a pasar por él.

    3. Define cuerdas perpendiculares a la línea central a intervalos regulares.
       - Se muestrea la línea central a lo largo del eje X (x_samples).
       - En cada punto muestreado, se define una recta perpendicular. La pendiente perpendicular es el inverso negativo
         de la pendiente de la línea central: m_perp = -1 / m_c.
       - Se calcula el intercepto de cada cuerda perpendicular (c_perp) usando el punto actual de la línea central.

    4. Encuentra las intersecciones de estas cuerdas con las aponeurosis superficial y profunda.
       - Se resuelve el sistema de ecuaciones lineales para encontrar dónde la recta perpendicular cruza a la aponeurosis superficial
         y a la profunda.
       - x_int = (c_aponeurosis - c_perp) / (m_perp - m_aponeurosis)

    5. Calcula la longitud de cada cuerda y retorna el promedio.
       - Se usa la distancia Euclidiana entre los puntos de intersección superior e inferior.

    Glosario de Variables Internas:
    - m_s, c_s: Pendiente (slope) y Intercepto (y-intercept) de la aponeurosis superficial (y = m_s * x + c_s).
    - m_d, c_d: Pendiente y Intercepto de la aponeurosis profunda.
    - theta_s, theta_d: Ángulos de inclinación (en radianes) de las aponeurosis respecto al eje X.
    - theta_c: Ángulo de inclinación (en radianes) de la línea central (bisectriz).
    - m_c, c_c: Pendiente e Intercepto de la línea central.
    - x_samples: Array con las coordenadas X donde se realizarán las mediciones (muestreo).
    - m_perp: Pendiente de las cuerdas perpendiculares a la línea central.
    - y_samples_c: Coordenadas Y correspondientes a x_samples en la línea central.
    - c_perps: Array de interceptos para cada cuerda perpendicular generada.
    - x_is, y_is: Coordenadas (X, Y) de intersección entre la cuerda y la aponeurosis superficial.
    - x_id, y_id: Coordenadas (X, Y) de intersección entre la cuerda y la aponeurosis profunda.
    - distances: Array con las distancias Euclidianas calculadas para cada cuerda.

    Argumentos:
        aponeurosis_sup (np.ndarray): Matriz (N, 2) de coordenadas (x, y) para la aponeurosis superficial.
                                      También puede ser una tupla de matrices (x, y).
        aponeurosis_deep (np.ndarray): Matriz (M, 2) de coordenadas (x, y) para la aponeurosis profunda.
                                       También puede ser una tupla de matrices (x, y).
        scale (str): Escala de salida. 'pp' para píxeles (por defecto) o 'mm' para milímetros.
        pixel_spacing (float): Factor de calibración en mm/píxel. Requerido si scale='mm'. Por defecto es 1.0.

    Retorna:
        dict: Un diccionario que contiene:
            'mean_thickness': Grosor medio en la escala seleccionada.
            'std_thickness': Desviación estándar del grosor en la escala seleccionada.
            'scale': La escala utilizada ('pp' o 'mm').
            'centerline_coords': Matriz (K, 2) de puntos en la línea central (para visualización).
            'chords': Lista de pares de tuplas [((x1,y1), (x2,y2)), ...] definiendo las cuerdas (para visualización).
    """

    # Ayuda para estandarizar la entrada
    def parse_input(data):
        if isinstance(data, (tuple, list)):
            if len(data) == 2 and isinstance(data[0], (np.ndarray, list)):
                 # Asumiendo (x_array, y_array)
                 return np.column_stack((data[0], data[1]))
        if isinstance(data, np.ndarray):
            if data.shape[1] == 2:
                return data
            elif data.shape[0] == 2:
                return data.T
        raise ValueError("Formato de entrada inválido para coordenadas de aponeurosis. Se espera matriz (N, 2) o tupla (x, y).")

    pts_sup = parse_input(aponeurosis_sup)
    pts_deep = parse_input(aponeurosis_deep)

    # 1. Ajustar Líneas (y = mx + c)
    # Usando np.polyfit con deg=1
    if len(pts_sup) < 2 or len(pts_deep) < 2:
         warnings.warn("No hay suficientes puntos para calcular el grosor.")
         return {'mean_thickness': 0, 'std_thickness': 0, 'scale': scale}

    m_s, c_s = np.polyfit(pts_sup[:, 0], pts_sup[:, 1], 1)
    m_d, c_d = np.polyfit(pts_deep[:, 0], pts_deep[:, 1], 1)

    # Definir el rango de X para evaluar (intersección de los rangos X de ambas líneas)
    min_x = max(np.min(pts_sup[:, 0]), np.min(pts_deep[:, 0]))
    max_x = min(np.max(pts_sup[:, 0]), np.max(pts_deep[:, 0]))

    if min_x >= max_x:
        warnings.warn("Las aponeurosis no se superponen en el eje X.")
        return {'mean_thickness': 0, 'std_thickness': 0, 'scale': scale}

    # 2. Calcular Línea Central
    # La línea central es la bisectriz angular.
    # Ángulo de las líneas
    theta_s = np.arctan(m_s)
    theta_d = np.arctan(m_d)

    # Ángulo de la bisectriz
    theta_c = (theta_s + theta_d) / 2.0
    m_c = np.tan(theta_c)

    # Para encontrar c_c (intersección), necesitamos un punto en la bisectriz.
    # Si las líneas se cruzan, la bisectriz pasa a través de la intersección.
    # Intersección X: m_s * x + c_s = m_d * x + c_d => x (m_s - m_d) = c_d - c_s
    if np.isclose(m_s, m_d):
        # Líneas paralelas
        c_c = (c_s + c_d) / 2.0
        # Línea central es y = m_c * x + c_c (donde m_c aprox m_s aprox m_d)
    else:
        x_int = (c_d - c_s) / (m_s - m_d)
        y_int = m_s * x_int + c_s
        # La línea central pasa por (x_int, y_int) con pendiente m_c
        # y - y_int = m_c (x - x_int) => y = m_c * x + (y_int - m_c * x_int)
        c_c = y_int - m_c * x_int

    # 3. & 4. Cuerdas Perpendiculares e Intersecciones
    # Muestreamos puntos a lo largo de la línea central dentro del rango X
    x_samples = np.linspace(min_x, max_x, num=int(max_x - min_x + 1))

    # Pendiente perpendicular
    if np.isclose(m_c, 0):
        m_perp = 1e9 # Vertical
    else:
        m_perp = -1.0 / m_c

    distances = []
    chords = []
    centerline_coords = []

    # ¿Enfoque vectorizado para eficiencia?
    # Intersección de Línea 1 (y = m1 x + c1) y Línea 2 (y = m2 x + c2)
    # x = (c2 - c1) / (m1 - m2)
    # Aquí Línea 1 es la cuerda: y - y_c = m_perp (x - x_c) => y = m_perp * x + (y_c - m_perp * x_c)
    # Sea c_perp = y_c - m_perp * x_c

    y_samples_c = m_c * x_samples + c_c
    c_perps = y_samples_c - m_perp * x_samples

    # Intersecciones con Sup (y = m_s x + c_s)
    # m_perp * x + c_perp = m_s * x + c_s
    # x * (m_perp - m_s) = c_s - c_perp
    # x_is = (c_s - c_perp) / (m_perp - m_s)

    # Manejamos el caso vertical (m_perp grande) por separado o aseguramos robustez
    if np.abs(m_perp) > 1e5:
        # Cuerdas verticales (aprox)
        x_is = x_samples
        y_is = m_s * x_is + c_s

        x_id = x_samples
        y_id = m_d * x_id + c_d
    else:
        denom_s = m_perp - m_s
        x_is = (c_s - c_perps) / denom_s
        y_is = m_s * x_is + c_s

        denom_d = m_perp - m_d
        x_id = (c_d - c_perps) / denom_d
        y_id = m_d * x_id + c_d

    # Calcular Distancias
    dx = x_is - x_id
    dy = y_is - y_id
    dists = np.sqrt(dx**2 + dy**2)

    distances = dists

    # Almacenar datos de visualización (submuestreados para claridad)
    step = max(1, len(x_samples) // 20) # Mostrar ~20 cuerdas
    for i in range(0, len(x_samples), step):
        chords.append(((x_is[i], y_is[i]), (x_id[i], y_id[i])))
        centerline_coords.append((x_samples[i], y_samples_c[i]))

    # 5. Promedio
    mean_dist_px = np.mean(distances)
    std_dist_px = np.std(distances)

    final_mean = mean_dist_px
    final_std = std_dist_px

    if scale == 'mm':
        final_mean = mean_dist_px * pixel_spacing
        final_std = std_dist_px * pixel_spacing

    return {
        'mean_thickness': final_mean,
        'std_thickness': final_std,
        'scale': scale,
        'centerline_coords': np.column_stack((x_samples, y_samples_c)), # Retornar todos los puntos
        'chords': chords # Cuerdas muestreadas
    }

def process_aponeurosis_mask(mask_path: str):
    """
    Procesa una máscara de aponeurosis para crear una máscara de ROI.

    Esta función es una versión simplificada de `process_aponeurosis_mask_comprehensive`.
    Está optimizada para máscaras de aponeurosis generadas manualmente, que son
    generalmente más limpias y no requieren un preprocesamiento extenso.

    Parameters:
    ----------
        mask_path (str): Ruta a la máscara de aponeurosis.

    Returns:
    ----------
        np.ndarray: La máscara de ROI.

    Nota :  - Para más compresion leer Descripcion_processing_manual_method.md
            en el repositorio personal GitHub DL_Track_US-Testing/Custom-MT.
            - Esta funcion esta basado en gran medida en el contenido 
            de DL_Track_US/doCalculations.
    """
    # Definidos por DL_Track_US, valor por defecto
    #APO_LENGTH_TRESH = 600
    #MIN_WIDTH = 60
    
# --- Validación de Parámetros de Entrada ---
    # Se verifica si la ruta de la máscara es una cadena de texto.
    if not isinstance(mask_path, str):
        raise TypeError("La ruta de la máscara (mask_path) debe ser una cadena de texto.")
    
#--- Carga de imagen ---
    try:
        # Se intenta leer la imagen desde la ruta proporcionada.
        mask = imageio.imread(mask_path)
    except FileNotFoundError as e:
        # Si el archivo no se encuentra, se imprime un mensaje de error.
        print(f"Error reading file: {e}")
        # Se retorna None para indicar que la operación falló.
        return None

#--- Proprocesamiento de imagen ---
    # Se comprueba si la imagen tiene 3 canales (es decir, si es a color).
    if mask.ndim == 3:
        # Si es a color, se convierte a escala de grises.
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    # Se aplica un umbral para binarizar la imagen. Los píxeles con valor > 0 se convierten en 255.
    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    # Se convierte el tipo de datos de la imagen a entero de 8 bits sin signo.
    thresh = thresh.astype("uint8")

#--- Obtencion y ordenamiento de contornos
    # Se encuentran los contornos externos en la imagen binarizada.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # (Opcional) Se filtra los contornos por longitud.
    #contours = [c for c in contours if len(c) > APO_LENGTH_TRESH]
    # Se comprueba si se encontraron al menos dos contornos (aponeurosis superior e inferior).
    if len(contours) < 2:
        return None

    # Se ordenan los contornos de arriba hacia abajo.
    contours, _ = sortContours(contours)
    # Se comprueba si el ordenamiento de contornos fue exitoso.
    if contours is None:
        return None

#--- Obtencion de coordenadas de aponeurosis ---
    # Se extraen las coordenadas del borde inferior ("Bottom") del primer contorno (aponeurosis superior).
    upp_x, upp_y = contourEdge("B", contours[0])
    # Se extraen las coordenadas del borde superior ("Top") del segundo contorno (aponeurosis inferior).
    low_x, low_y = contourEdge("T", contours[1])

    # Se comprueba si se extrajeron correctamente las coordenadas de ambos bordes.
    if len(upp_x) == 0 or len(low_x) == 0:
        return None

    # Se suavizan las coordenadas 'y' de los bordes usando un filtro Savitzky-Golay.
    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2)
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2)

#--- Generación de la Máscara ROI ---
    # Se crea una máscara en negro con las mismas dimensiones que la imagen umbralizada.
    ex_mask = np.zeros(thresh.shape, np.uint8)
    # Se ajusta un polinomio de segundo grado a los puntos del borde superior.
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
    # Se ajusta un polinomio de segundo grado a los puntos del borde inferior.
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

    # Se determina el rango de 'x' para la región de interés (ROI).
    start_x = int(max(np.min(upp_x), np.min(low_x)))
    end_x = int(min(np.max(upp_x), np.max(low_x)))

    # Se itera sobre el rango de 'x' para rellenar la máscara de ROI.
    for x in range(start_x, end_x):
        # Se calcula la coordenada 'y' mínima a partir del polinomio superior.
        ymin = int(np.floor(f_upp(x)))
        # Se calcula la coordenada 'y' máxima a partir del polinomio inferior.
        ymax = int(np.ceil(f_low(x)))
        # Se asegura que 'ymin' no sea menor que 0.
        ymin = max(0, ymin)
        # Se asegura que 'ymax' no exceda la altura de la imagen.
        ymax = min(ex_mask.shape[0], ymax)
        # Se rellenan los píxeles entre ymin e ymax para la 'x' actual.
        ex_mask[ymin:ymax, x] = 255

    # Se retorna la máscara de ROI generada.
    return ex_mask


def process_aponeurosis_mask_comprehensive(mask_path: str):
    """
    Procesa una máscara de aponeurosis para crear una máscara de ROI con un preprocesamiento completo.

    Esta función es adecuada para máscaras de aponeurosis que pueden contener ruido o
    discontinuidades, como las generadas automáticamente. Incluye pasos adicionales
    de fusión de contornos y refinamiento morfológico.

    Parameters:
    ----------
        mask_path (str): Ruta a la máscara de aponeurosis.

    Returns:
    ----------
        np.ndarray (uint8): La máscara de ROI.
    
    Nota :  - Para más compresion leer Descripcion_processing_manual_method.md
            en el repositorio personal GitHub DL_Track_US-Testing/Custom-MT.
            - Esta funcion esta basado en gran medida en el contenido 
            de DL_Track_US/doCalculations.
    """
    #Definidos por DL_Track_US, valor por defecto
    APO_LENGTH_TRESH = 600     # Define el umbral de longitud para los contornos de la aponeurosis.
    MIN_WIDTH = 60     # Define el ancho mínimo entre aponeurosis.
    
    # --- Validación de Parámetros de Entrada ---
    # Se verifica si la ruta de la máscara es una cadena de texto.
    if not isinstance(mask_path, str):
        raise TypeError("La ruta de la máscara (mask_path) debe ser una cadena de texto.")

#--- Carga y Preprocesamiento de la Máscara ---
    try:
        # Lee la imagen de la máscara desde la ruta especificada.
        mask = imageio.imread(mask_path)
    except FileNotFoundError as e: # Maneja el error si no se encuentra el archivo.
        # Imprime un mensaje de error.
        print(f"Error reading file: {e}")
        return None

    # Comprueba si la imagen es a color (3-dimensiones).
    if mask.ndim == 3:
        # Convierte la máscara a escala de grises.
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    # Aplica un umbral para binarizar la imagen (>0 se convierte en 255).
    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    # Convierte la imagen a tipo de dato de 8 bits sin signo.
    thresh = thresh.astype("uint8")
    
#--- Detección y Fusión de Contornos ---
    # Encuentra los contornos en la imagen binarizada.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Filtra los contornos para mantener solo los que superan el umbral de longitud.
    contours_re = [c for c in contours if len(c) > APO_LENGTH_TRESH]
    # Comprueba si hay al menos un contorno.
    if len(contours_re) < 1:
        return None 

    # Ordena los contornos de arriba (superficial) hacia abajo (profundo).
    contours, _ = sortContours(contours_re) 
    
    # Comprueba si los contornos se pudieron ordenar.
    if contours is None:
        return None

    # Inicializa una lista para almacenar los nuevos contornos ordenados.
    contours_re2 = []
    # Itera sobre los contornos ordenados.
    for contour in contours:
        # Convierte el contorno a una lista de puntos.
        pts = list(contour)
        # Ordena los puntos del contorno por su coordenada x y luego por la y.
        ptsT = sorted(pts, key=lambda k: [k[0][0], k[0][1]])
        # Extrae todas las coordenadas x de los puntos.
        allx = [p[0, 0] for p in ptsT]
        # Extrae todas las coordenadas y de los puntos.
        ally = [p[0, 1] for p in ptsT]
        # Crea un nuevo contorno con los puntos ordenados.
        app = np.array(list(zip(allx, ally)))
        # Añade el nuevo contorno a la lista.
        contours_re2.append(app)

    # Crea una máscara en negro del mismo tamaño que la imagen binarizada.
    maskT = np.zeros(thresh.shape, np.uint8)
    # Itera sobre los nuevos contornos.
    for cnt in contours_re2:
        # Dibuja los contornos en la máscara, rellenando el área.
        cv2.drawContours(maskT, [cnt], 0, 255, -1)

    # Conectando contornos muy cercanos para fusionarlos
    # Obtiene las coordenadas x iniciales de cada contorno.
    xs1 = [c[0][0] for c in contours_re2]
    # Obtiene las coordenadas x finales de cada contorno.
    xs2 = [c[-1][0] for c in contours_re2]
    # Obtiene las coordenadas y iniciales de cada contorno.
    ys1 = [c[0][1] for c in contours_re2]
    # Obtiene las coordenadas y finales de cada contorno.
    ys2 = [c[-1][1] for c in contours_re2]

    # Itera sobre los contornos para conectar los que están cerca.
    for i in range(len(contours_re2) - 1):
        # Comprueba si el siguiente contorno comienza después de que termina el actual.
        if xs1[i + 1] > xs2[i]:
            # Obtiene las coordenadas 'y' del final del contorno actual y el inicio del siguiente.
            y1, y2 = ys2[i], ys1[i + 1]
            # Comprueba si las coordenadas 'y' están dentro de un rango de 10 píxeles.
            if y1 - 10 <= y2 <= y1 + 10:
                # Concatena los dos contornos.
                m = np.vstack((contours_re2[i], contours_re2[i + 1]))
                # Dibuja una línea entre los dos contornos en la máscara.
                cv2.drawContours(maskT, [m], 0, 255, -1)

    # Convierte la máscara a binaria (0 y 1).
    maskT[maskT > 0] = 1

#--- Refinamiento de Aponeurosis ---
    skeleton = skeletonize(maskT).astype(np.uint8)
    kernel = np.ones((3, 7), np.uint8)
    dilate = cv2.dilate(skeleton, kernel, iterations=15)
    erode = cv2.erode(dilate, kernel, iterations=10)

#--- Extracción de Bordes y Suavizado ---
    # Encuentra los contornos en la imagen erosionada.
    contoursE, _ = cv2.findContours(erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # Filtra los contornos para mantener solo los que superan el umbral de longitud.
    contoursE = [c for c in contoursE if len(c) > APO_LENGTH_TRESH]

    # Comprueba si hay al menos dos contornos (aponeurosis superior e inferior).
    if len(contoursE) < 2:
        return None

    # Ordena los contornos.
    contoursE, _ = sortContours(contoursE)
    # Comprueba si los contornos se pudieron ordenar.
    if contoursE is None:
        return None

    # Obtiene el borde inferior ("B") del primer contorno (aponeurosis superior).
    upp_x, upp_y = contourEdge("B", contoursE[0])

    # Comprueba si la segunda aponeurosis está lo suficientemente separada de la primera.
    if contoursE[1][0, 0, 1] > contoursE[0][0, 0, 1] + MIN_WIDTH:
        # Obtiene el borde superior ("Top") del segundo contorno (aponeurosis inferior).
        low_x, low_y = contourEdge("T", contoursE[1])
    else: # Si no están suficientemente separadas.
        # Comprueba si hay un tercer contorno.
        if len(contoursE) > 2:
            # Obtiene el borde superior ("T") del tercer contorno.
            low_x, low_y = contourEdge("T", contoursE[2])
        else: # Si no hay un tercer contorno.
            # Devuelve None.
            return None

    # Comprueba si se encontraron los bordes superior e inferior.
    if len(upp_x) == 0 or len(low_x) == 0:
        return None

    # Suaviza los datos del borde superior con un filtro Savitzky-Golay.
    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2)
    # Suaviza los datos del borde inferior con un filtro Savitzky-Golay.
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2)

#--- Generación de la Máscara ROI ---
    ex_mask_comprehensive = np.zeros(thresh.shape, np.uint8)
    # Ajusta un polinomio de segundo grado a los datos del borde superior.
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
    # Ajusta un polinomio de segundo grado a los datos del borde inferior.
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

    # Determina la coordenada x inicial para la ROI.
    start_x = int(max(np.min(upp_x), np.min(low_x)))
    # Determina la coordenada x final para la ROI.
    end_x = int(min(np.max(upp_x), np.max(low_x)))

    # Itera a lo largo del eje x de la ROI.
    for x in range(start_x, end_x):
        # Calcula la coordenada y mínima (borde superior).
        ymin = int(np.floor(f_upp(x)))
        # Calcula la coordenada y máxima (borde inferior).
        ymax = int(np.ceil(f_low(x)))
        # Asegura que ymin no sea menor que 0.
        ymin = max(0, ymin)
        # Asegura que ymax no exceda la altura de la imagen.
        ymax = min(ex_mask_comprehensive.shape[0], ymax)
        # Rellena la región entre los dos bordes en la máscara de ROI.
        ex_mask_comprehensive[ymin:ymax, x] = 255

    # Devuelve la máscara de ROI generada.
    return ex_mask_comprehensive

def overlay_apo_mask(image_apo_path: str, mask_apo_path: str, opacity: float = 0.5, color: str = 'Verde') -> np.ndarray:
    """
    Superpone una máscara de aponeurosis sobre una imagen de ultrasonido con una opacidad y color personalizables.

    Parameters
    ----------
    image_apo_path : str
        Ruta a la imagen de ultrasonido.
    mask_apo_path : str
        Ruta a la máscara de aponeurosis.
    opacity : float, optional
        Nivel de opacidad para la superposición de la máscara. Debe ser un valor entre 0.0 y 1.0.
        Por defecto es 0.5.
    color : str, optional
        Color para la superposición de la máscara. Los valores permitidos son 'Rojo', 'Verde' o 'Azul'.
        Por defecto es 'Verde'.

    Returns
    -------
    np.ndarray
        La imagen con la máscara superpuesta.

    Nota :  
    ----------
        - Las lineas de codigo principales fueron extraidos del modulo 
        DL_Track_US/gui_helpers/file_analysis.py
    """
    # --- Validación de Parámetros ---
    # Se verifica si la ruta de la imagen y la máscara son cadenas de texto.
    if not isinstance(image_apo_path, str) or not isinstance(mask_apo_path, str):
        # Si alguna no es una cadena, se lanza un error de tipo (TypeError).
        raise TypeError("Las rutas de la imagen y la máscara deben ser cadenas de texto.")

    # Se verifica que el valor de opacidad esté en el rango de 0.0 a 1.0.
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("La opacidad debe estar entre 0.0 y 1.0.")

    # Se define un diccionario para mapear los nombres de los colores a sus valores BGR.
    color_map = {
        'Rojo': [0, 0, 255],
        'Verde': [0, 255, 0],
        'Azul': [255, 0, 0]
    }
    # Se verifica si el color proporcionado es una de las claves válidas en el mapa de colores.
    if color not in color_map:
        raise ValueError("El color debe ser 'Rojo', 'Verde' o 'Azul'.")

    # --- Carga de Imágenes ---
    try:
        # Se lee la imagen de la máscara desde su ruta.
        mask_apo = imageio.imread(mask_apo_path)
        # Se lee la imagen de ultrasonido desde su ruta.
        image_apo = imageio.imread(image_apo_path)
    except FileNotFoundError as e:
        # Si no se encuentra alguno de los archivos, se imprime un mensaje de error.
        print(f"Error al leer el archivo: {e}")
        return None

    # --- Preprocesamiento de Imágenes ---
    # Se comprueba si la máscara es una imagen a color (3 canales).
    if mask_apo.ndim == 3:
        # Si es a color, se convierte a escala de grises.
        mask_apo = cv2.cvtColor(mask_apo, cv2.COLOR_BGR2GRAY)
        
    # Se comprueba si la imagen de ultrasonido es a color (3 canales).
    if image_apo.ndim == 3:
        # Si es a color, se convierte a escala de grises.
        image_apo = cv2.cvtColor(image_apo, cv2.COLOR_BGR2GRAY)
    
    # Se redimensiona la imagen de ultrasonido para que coincida con las dimensiones de la máscara.
    image_apo = cv2.resize(image_apo, (mask_apo.shape[1], mask_apo.shape[0]))
                                            
    # Se convierte la máscara de escala de grises a una imagen a color (BGR).
    colored_mask_apo = cv2.cvtColor(mask_apo, cv2.COLOR_GRAY2BGR)
    # Se aplica el color seleccionado a las regiones blancas (píxeles > 0) de la máscara.
    colored_mask_apo[mask_apo > 0] = color_map[color]

    # Se convierte la imagen de ultrasonido (originalmente en escala de grises) a color (BGR).
    colored_image_apo = cv2.cvtColor(image_apo, cv2.COLOR_GRAY2BGR)

    # Se superpone la máscara coloreada sobre la imagen de ultrasonido.
    overlaid_image = cv2.addWeighted(colored_image_apo, 1, colored_mask_apo, opacity, 0)

    # Se retorna la imagen resultante con la superposición.
    return overlaid_image
