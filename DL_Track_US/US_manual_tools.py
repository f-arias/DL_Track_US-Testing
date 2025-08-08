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
    # --- Validación de Parámetros de Entrada ---
    # Se verifica si la ruta de la máscara es una cadena de texto.
    if not isinstance(mask_path, str):
        # Si no es una cadena, se lanza un error de tipo (TypeError).
        raise TypeError("La ruta de la máscara (mask_path) debe ser una cadena de texto.")

    # Definidos por DL_Track_US, valor por defecto
    #APO_LENGTH_TRESH = 600
    #MIN_WIDTH = 60
    
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
        # Si no hay suficientes contornos, se retorna None.
        return None

    # Se ordenan los contornos de arriba hacia abajo.
    contours, _ = sortContours(contours)
    # Se comprueba si el ordenamiento de contornos fue exitoso.
    if contours is None:
        # Si falló, se retorna None.
        return None

#--- Obtencion de coordenadas de aponeurosis ---
    # Se extraen las coordenadas del borde inferior ("B") del primer contorno (aponeurosis superior).
    upp_x, upp_y = contourEdge("B", contours[0])
    # Se extraen las coordenadas del borde superior ("T") del segundo contorno (aponeurosis inferior).
    low_x, low_y = contourEdge("T", contours[1])

    # Se comprueba si se extrajeron correctamente las coordenadas de ambos bordes.
    if len(upp_x) == 0 or len(low_x) == 0:
        # Si falta alguno de los bordes, se retorna None.
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
    # --- Validación de Parámetros de Entrada ---
    # Se verifica si la ruta de la máscara es una cadena de texto.
    if not isinstance(mask_path, str):
        # Si no es una cadena, se lanza un error de tipo (TypeError).
        raise TypeError("La ruta de la máscara (mask_path) debe ser una cadena de texto.")

    #Definidos por DL_Track_US, valor por defecto
    APO_LENGTH_TRESH = 600     # Define el umbral de longitud para los contornos de la aponeurosis.
    MIN_WIDTH = 60     # Define el ancho mínimo entre aponeurosis.

#--- Carga y Preprocesamiento de la Máscara ---
    try:
        # Lee la imagen de la máscara desde la ruta especificada.
        mask = imageio.imread(mask_path)
    except FileNotFoundError as e: # Maneja el error si no se encuentra el archivo.
        # Imprime un mensaje de error.
        print(f"Error reading file: {e}")
        # Devuelve None si no se puede leer el archivo.
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
        # Si no hay contornos, devuelve None.
        return None 

    # Ordena los contornos de arriba (superficial) hacia abajo (profundo).
    contours, _ = sortContours(contours_re) 
    
    # Comprueba si los contornos se pudieron ordenar.
    if contours is None:
        # Devuelve None si no se pudieron ordenar.
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
    # Aplica esqueletización para obtener una representación de una sola línea.
    skeleton = skeletonize(maskT).astype(np.uint8)
    # Define un kernel rectangular para las operaciones morfológicas.
    kernel = np.ones((3, 7), np.uint8)
    # Dilata el esqueleto para engrosar las líneas.
    dilate = cv2.dilate(skeleton, kernel, iterations=15)
    # Erosiona la imagen dilatada para refinar las líneas.
    erode = cv2.erode(dilate, kernel, iterations=10)

#--- Extracción de Bordes y Suavizado ---
    # Encuentra los contornos en la imagen erosionada.
    contoursE, _ = cv2.findContours(erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # Filtra los contornos para mantener solo los que superan el umbral de longitud.
    contoursE = [c for c in contoursE if len(c) > APO_LENGTH_TRESH]

    # Comprueba si hay al menos dos contornos (aponeurosis superior e inferior).
    if len(contoursE) < 2:
        # Devuelve None si no se encuentran las dos aponeurosis.
        return None

    # Ordena los contornos.
    contoursE, _ = sortContours(contoursE)
    # Comprueba si los contornos se pudieron ordenar.
    if contoursE is None:
        # Devuelve None si no se pudieron ordenar.
        return None

    # Obtiene el borde inferior ("B") del primer contorno (aponeurosis superior).
    upp_x, upp_y = contourEdge("B", contoursE[0])

    # Comprueba si la segunda aponeurosis está lo suficientemente separada de la primera.
    if contoursE[1][0, 0, 1] > contoursE[0][0, 0, 1] + MIN_WIDTH:
        # Obtiene el borde superior ("T") del segundo contorno (aponeurosis inferior).
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
        # Devuelve None si no se encontraron los bordes.
        return None

    # Suaviza los datos del borde superior con un filtro Savitzky-Golay.
    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2)
    # Suaviza los datos del borde inferior con un filtro Savitzky-Golay.
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2)

#--- Generación de la Máscara ROI ---
    # Crea una máscara en negro para la región de interés (ROI).
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
        # Si está fuera del rango, se lanza un error de valor (ValueError).
        raise ValueError("La opacidad debe estar entre 0.0 y 1.0.")

    # Se define un diccionario para mapear los nombres de los colores a sus valores BGR.
    color_map = {
        'Rojo': [0, 0, 255],
        'Verde': [0, 255, 0],
        'Azul': [255, 0, 0]
    }
    # Se verifica si el color proporcionado es una de las claves válidas en el mapa de colores.
    if color not in color_map:
        # Si no es un color válido, se lanza un error de valor (ValueError).
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
        # Se retorna None para indicar que la operación falló.
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
