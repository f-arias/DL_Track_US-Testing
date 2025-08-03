# -*- coding: utf-8 -*-
"""
Description
-----------
Este módulo proporciona un conjunto de herramientas y funciones de ayuda
para el análisis manual y el etiquetado de imágenes de ultrasonido musculoesquelético.

Este módulo complementa los métodos de análisis automático (basados en CNN) 
de DL_Track_US, ofreciendo una alternativa o un método de validación 
("gold standard") controlado por el usuario.

Por ultimo, este modulo se baso en gran medida al repositorio DL_Track_US
Ritsche, P., Seynnes, O., & Cronin, N. (2023). 
DL_Track_US: a python package to analyse muscle ultrasonography images. 
Journal of Open Source Software, 8(85), 5206. https://doi.org/10.21105/joss.05206

Functions Scope
---------------
get_manual_polyline(image, window_name="Seleccionar Puntos")
    Muestra una imagen y permite al usuario trazar una polilínea haciendo clic.
    Devuelve las coordenadas (x, y) de la línea trazada.

select_manual_points(image, num_points=2, window_name="Seleccionar Puntos")
    Permite al usuario seleccionar un número específico de puntos en la imagen.
    Ideal para marcar puntos de calibración o extremos de fascículos.

calculate_thickness_from_lines(line_upper, line_lower)
    Calcula el grosor muscular promedio entre dos líneas (aponeurosis).

calculate_angle_between_lines(line1, line2)
    Calcula el ángulo de intersección entre dos líneas, útil para el
    ángulo de pennación.

Notes
-----
- Las funciones interactivas (como `get_manual_polyline`) dependen de un backend
  de GUI que pueda manejar eventos de mouse (ej. la ventana de HighGUI de OpenCV).
- Todas las coordenadas devueltas están en unidades de píxeles, con el origen
  (0,0) en la esquina superior izquierda de la imagen.
- Una diferencia se observa que la funcion mas robusta "_comprehensive"
abarca mas area en la imagen, y no necesariamente pertenece al area del ROI
del musculoesqueletico(ME). Sino, de los costados, es decir del marco de informacion
que no forma parte como tal de la imagen de US del paciente.
----

@author: Felipe Arias
"""
# --- Importaciones de Dependencias ---
import cv2
import numpy as np
import imageio
from scipy.signal import savgol_filter
from skimage.morphology import skeletonize
from DL_Track_US.gui_helpers.do_calculations import sortContours, contourEdge

# --- Definición de Funciones ---
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
    
#--- Carga de imagen ---
    try:
        mask = imageio.imread(mask_path)
    except FileNotFoundError as e:
        print(f"Error reading file: {e}")
        return None

#--- Proprocesamiento de imagen ---
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    thresh = thresh.astype("uint8")

#--- Obtencion y ordenamiento de contornos
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    #contours = [c for c in contours if len(c) > APO_LENGTH_TRESH]
    if len(contours) < 2:
        return None

    contours, _ = sortContours(contours)    # Ordena los contornos de arriba hacia abajo
    if contours is None:
        return None

#--- Obtencion de coordenadas de aponeurosis ---
    upp_x, upp_y = contourEdge("B", contours[0])     # B = Bottom
    low_x, low_y = contourEdge("T", contours[1])     # T = Top

    if len(upp_x) == 0 or len(low_x) == 0:
        return None

    # Suaviza los datos de los bordes con un filtro Savitzky-Golay.
    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2)
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2)

#--- Generación de la Máscara ROI ---
    ex_mask = np.zeros(thresh.shape, np.uint8)
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

    start_x = int(max(np.min(upp_x), np.min(low_x)))
    end_x = int(min(np.max(upp_x), np.max(low_x)))

    for x in range(start_x, end_x):
        ymin = int(np.floor(f_upp(x)))
        ymax = int(np.ceil(f_low(x)))
        ymin = max(0, ymin)
        ymax = min(ex_mask.shape[0], ymax)
        ex_mask[ymin:ymax, x] = 255

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

#--- Carga y Preprocesamiento de la Máscara ---
    try:
        mask = imageio.imread(mask_path) # Lee la imagen de la máscara desde la ruta especificada, sin importar el formato de imagen.
    except FileNotFoundError as e: # Maneja el error si no se encuentra el archivo.
        print(f"Error reading file: {e}") # Imprime un mensaje de error.
        return None # Devuelve None si no se puede leer el archivo.

    if mask.ndim == 3:     # Comprueba si la imagen es a color (3-dimensiones).
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY) # Convierte la máscara a escala de grises.

    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY) # Aplica un umbral(>0 = valor 255) para binarizar la imagen.
    thresh = thresh.astype("uint8")     # Convierte la imagen a tipo de dato de 8 bits sin signo.
    
#--- Detección y Fusión de Contornos ---
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) # Encuentra los contornos en la imagen binarizada.

    contours_re = [c for c in contours if len(c) > APO_LENGTH_TRESH] # Filtra los contornos para mantener solo los que superan el umbral de longitud.
    if len(contours_re) < 1: # Comprueba si hay al menos un contorno.
        return None 

    # Ordena los contornos de arriba(superfial) hacia abajo(profundo), NO las coordenadas.
    contours, _ = sortContours(contours_re) 
    
    if contours is None: # Comprueba si los contornos se pudieron ordenar.
        return None     # Devuelve None si no se pudieron ordenar los contornos.

    contours_re2 = [] # Inicializa una lista para almacenar los nuevos contornos.
    for contour in contours: # Itera sobre los contornos ordenados.
        pts = list(contour) # Convierte el contorno a una lista de puntos.
        ptsT = sorted(pts, key=lambda k: [k[0][0], k[0][1]]) # Ordena los puntos del contorno por su coordenada x y luego por la y.
        allx = [p[0, 0] for p in ptsT] # Extrae todas las coordenadas x de los puntos.
        ally = [p[0, 1] for p in ptsT] # Extrae todas las coordenadas y de los puntos.
        app = np.array(list(zip(allx, ally))) # Crea un nuevo contorno con los puntos ordenados.
        contours_re2.append(app) # Añade el nuevo contorno a la lista.

    maskT = np.zeros(thresh.shape, np.uint8) # Crea una máscara en negro del mismo tamaño que la imagen binarizada.
    for cnt in contours_re2: # Itera sobre los nuevos contornos.
    #drawContours(imagen_de_destino,contornos,indice de contorno a dibujar, valor de pixel, thickness=-1 rellena todo el area del contorno)
        cv2.drawContours(maskT, [cnt], 0, 255, -1) # Dibuja los contornos en la máscara.

    # Conectando contornos muy cercanos para fusionarlos  
    xs1 = [c[0][0] for c in contours_re2] # Obtiene las coordenadas x iniciales de cada contorno.
    xs2 = [c[-1][0] for c in contours_re2] # Obtiene las coordenadas x finales de cada contorno.
    ys1 = [c[0][1] for c in contours_re2] # Obtiene las coordenadas y iniciales de cada contorno.
    ys2 = [c[-1][1] for c in contours_re2] # Obtiene las coordenadas y finales de cada contorno.

    for i in range(len(contours_re2) - 1): # Itera sobre los contornos para conectar los que están cerca.
        if xs1[i + 1] > xs2[i]: # Comprueba si el siguiente contorno comienza después de que termina el actual.
            y1, y2 = ys2[i], ys1[i + 1] # Obtiene las coordenadas y del final del contorno actual y el inicio del siguiente.
            if y1 - 10 <= y2 <= y1 + 10: # Comprueba si las coordenadas y están dentro de un rango de 10 píxeles.
                m = np.vstack((contours_re2[i], contours_re2[i + 1])) # Concatena los dos contornos.
                cv2.drawContours(maskT, [m], 0, 255, -1) # Dibuja una línea entre los dos contornos en la máscara.

    maskT[maskT > 0] = 1 # Convierte la máscara a binaria (0 y 1).

#--- Refinamiento de Aponeurosis ---
    skeleton = skeletonize(maskT).astype(np.uint8) # Aplica esqueletización a la máscara para obtener una representación de una sola línea.
    kernel = np.ones((3, 7), np.uint8) # Define un kernel para las operaciones morfológicas.
    dilate = cv2.dilate(skeleton, kernel, iterations=15) # Dilata el esqueleto para engrosar las líneas.
    # A pesar que se usa erode, hizo que las aponeurosis sean un poco mas largas
    erode = cv2.erode(dilate, kernel, iterations=10) # Erosiona la imagen dilatada para refinar las líneas.

#--- Extracción de Bordes y Suavizado ---
    contoursE, _ = cv2.findContours(erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) # Encuentra los contornos en la imagen erosionada.
    contoursE = [c for c in contoursE if len(c) > APO_LENGTH_TRESH] # Filtra los contornos para mantener solo los que superan el umbral de longitud.

    if len(contoursE) < 2: # Comprueba si hay al menos dos contornos (aponeurosis superior e inferior).
        return None # Devuelve None si no se encuentran las dos aponeurosis.

    contoursE, _ = sortContours(contoursE) # Ordena los contornos.
    if contoursE is None: # Comprueba si los contornos se pudieron ordenar.
        return None # Devuelve None si no se pudieron ordenar los contornos.

    upp_x, upp_y = contourEdge("B", contoursE[0]) # Obtiene los bordes superior (Bottom) del primer contorno.

    if contoursE[1][0, 0, 1] > contoursE[0][0, 0, 1] + MIN_WIDTH: # Comprueba si la segunda aponeurosis está lo suficientemente separada de la primera.
        low_x, low_y = contourEdge("T", contoursE[1]) # Obtiene los bordes inferior (T) del segundo contorno.
    else: # Si no están suficientemente separadas.
        if len(contoursE) > 2: # Comprueba si hay un tercer contorno.
            low_x, low_y = contourEdge("T", contoursE[2]) # Obtiene los bordes inferior (Top) del tercer contorno.
        else: # Si no hay un tercer contorno.
            return None # Devuelve None (osea Exit).

    if len(upp_x) == 0 or len(low_x) == 0: # Comprueba si se encontraron los bordes superior e inferior.
        return None # Devuelve None si no se encontraron los bordes.

    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2) # Suaviza los datos del borde superior con un filtro Savitzky-Golay.
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2) # Suaviza los datos del borde inferior con un filtro Savitzky-Golay.

#--- Generación de la Máscara ROI ---
    ex_mask_comprehensive = np.zeros(thresh.shape, np.uint8) # Crea una máscara en negro para la región de interés (ROI).
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2)) # Ajusta un polinomio de segundo grado a los datos del borde superior.
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2)) # Ajusta un polinomio de segundo grado a los datos del borde inferior.

    start_x = int(max(np.min(upp_x), np.min(low_x))) # Determina la coordenada x inicial para la ROI.
    end_x = int(min(np.max(upp_x), np.max(low_x))) # Determina la coordenada x final para la ROI.

    for x in range(start_x, end_x): # Itera a lo largo del eje x de la ROI.
        ymin = int(np.floor(f_upp(x))) # Calcula la coordenada y mínima (borde superior).
        ymax = int(np.ceil(f_low(x))) # Calcula la coordenada y máxima (borde inferior).
        ymin = max(0, ymin) # Asegura que ymin no sea menor que 0.
        ymax = min(ex_mask_comprehensive.shape[0], ymax) # Asegura que ymax no exceda la altura de la imagen.
        ex_mask_comprehensive[ymin:ymax, x] = 255 # Rellena la región entre los dos bordes en la máscara de ROI.

    return ex_mask_comprehensive

def overlay_apo_mask (image_apo_path: str ,mask_apo_path: str ,opacity = 0.5) -> np.ndarray:
    """    
    Parameters
    ----------
    image_apo_path : str
        DESCRIPTION.
    mask_apo_path : str
        DESCRIPTION.
    opacity : TYPE, optional
        DESCRIPTION. The default is 0.5.

    Returns
    -------
    None.

    """
#--- Carga de imagen ---
    try:
        mask_apo = imageio.imread(mask_apo_path)
        image_apo = imageio.imread (image_apo_path)
    except FileNotFoundError as e:
        print(f"Error reading file: {e}")
        return None

#--- Proprocesamiento de imagen ---
    if mask_apo.ndim == 3:  #Si es de 3-canal
        mask_apo = cv2.cvtColor(mask_apo, cv2.COLOR_BGR2GRAY)
        
    if image_apo.ndim == 3:  #Si es de 3-canal
        image_apo = cv2.cvtColor(image_apo, cv2.COLOR_BGR2GRAY)
    
    
    # Ensure both images have the same dimensions by resizing the mask
    image_apo = cv2.resize (image_apo, (mask_apo.shape[1], mask_apo.shape[0]))
                                            
    # Create a colored mask with green color for the white regions in the mask
    colored_mask_apo = cv2.cvtColor (mask_apo, cv2.COLOR_GRAY2BGR)
    colored_mask_apo [mask_apo > 0] = [0, 255, 0]  # Green color for mask regions

    # Convert the ultrasound image to color
    colored_image_apo = cv2.cvtColor(image_apo, cv2.COLOR_GRAY2BGR)

    # Overlay the colored mask on the ultrasound image
    overlaid_image = cv2.addWeighted (colored_image_apo, 1, colored_mask_apo, opacity, 0)

    return overlaid_image
