# -*- coding: utf-8 -*-
"""
Este módulo proporciona un conjunto de funciones para evaluar y comparar máscaras de segmentación
de imágenes de US, como las generadas por diferentes modelos sea Deep learning, transformadas entre otras
frente a máscaras de referencia (ground truth) creadas por expertos.

Las métricas implementadas están diseñadas para cuantificar el rendimiento de la segmentación
en términos de superposición de mascaras, similitud de contorno y concordancia estadística. Esto permite
una evaluación robusta tanto de máscaras de aponeurosis como de ROI musculares.

Métricas:
--------------------
- Coeficiente de Dice (Dice-Sørensen)
- Índice de Jaccard (Intersection over Union - IoU)
- Sensibilidad (Recall / True Positive Rate)
- Precisión (Precision / Positive Predictive Value)
- Distancia de Hausdorff
- Kappa de Cohen

Dependencias:
-------------
- NumPy: Para cálculos matriciales eficientes.
- Scikit-learn: Para el cálculo del Kappa de Cohen.
- SciPy: Para el cálculo de la Distancia de Hausdorff.
- Scikit-Image: Alternativa para el cálculo de la Distancia de Hausdorff y sus variantes.
"""

import numpy as np
from sklearn.metrics import cohen_kappa_score
from scipy.spatial.distance import directed_hausdorff as hausdorff_distance_scipy
from skimage.metrics import hausdorff_distance as hausdorff_distance_skimage

def dice_coefficient (reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Coeficiente de Dice (Dice-Sørensen) entre dos máscaras con las mismas dimensiones(shape).

    Esta métrica mide la superposición entre dos áreas, normalizada por el tamaño de ambas.
    Un valor de 1 indica una superposición perfecta, mientras que 0 indica ninguna superposición.
    Es el estándar de oro, mide el rendimiento global en un solo número.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
                                     Debe ser una matriz de NumPy con valores binarios (0 o 1).
        test_mask (np.ndarray): La máscara de prueba.
                                Debe tener las mismas dimensiones que la máscara de referencia.
        epsilon (float, optional): Un valor pequeño para evitar la división por cero si ambas
                                   máscaras están vacías. Por defecto es 1e-6.

    Returns:
        float: El valor del Coeficiente de Dice, un número flotante entre 0.0 y 1.0.
    """
    # Asegurarse de que las máscaras sean booleanas para los cálculos
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Calcular la intersección pixel per pixel(Verdaderos Positivos)
    intersection = np.sum(reference_mask & test_mask)

    # Calcular el tamaño de cada máscara
    size_reference = np.sum(reference_mask)
    size_test = np.sum(test_mask)

    # Calcular el coeficiente de Dice
    # 2* (Area de superposicion) / (Area referencia + Area test)
    dice = (2. * intersection + epsilon) / (size_reference + size_test + epsilon)

    return dice


def jaccard_index (reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Índice de Jaccard (Intersection over Union - IoU) entre dos máscaras.

    Mide la similitud entre las dos máscaras dividiendo el área de intersección por el área de unión.
    Un valor de 1 indica una superposición perfecta y 0 indica ninguna superposición.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Un valor pequeño para evitar la división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor del Índice de Jaccard (IoU), un número flotante entre 0.0 y 1.0.
    """
    # Pasar las mascaras a bool
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Calcular la intersección
    intersection = np.sum(reference_mask & test_mask)

    # Calcular la unión
    union = np.sum(reference_mask | test_mask)

    # Calcular el índice de Jaccard
    # iou =(A ∩ B) / (A ∪ B)
    iou = (intersection + epsilon) / (union + epsilon)

    return iou


def sensitivity(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Sensibilidad (Recall o True Positive Rate) entre dos máscaras.

    Mide la proporción de los píxeles positivos en la máscara de referencia que fueron
    correctamente identificados por la máscara de prueba.
    Diagnostica si tu algoritmo omite partes (sub-segmentación).

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Un valor pequeño para evitar la división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor de la Sensibilidad, entre 0.0 y 1.0.
    """
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Verdaderos Positivos (intersección)
    true_positives = np.sum(reference_mask & test_mask)

    # Total de positivos reales (píxeles en la máscara de referencia)
    # actual_positives = (veraderos positivos + falsos negativos)
    actual_positives = np.sum(reference_mask)

    # Calcular la sensibilidad
    # sensitivity(recall) = verdaderos positivos / (veraderos positivos + falsos negativos)
    recall = (true_positives + epsilon) / (actual_positives + epsilon)

    return recall


def precision(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Precisión (Positive Predictive Value) entre dos máscaras.

    Mide la proporción de píxeles positivos en la máscara de prueba que son también
    positivos en la máscara de referencia.
    Diagnostica si tu algoritmo añade ruido (sobre-segmentación).

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Un valor pequeño para evitar la división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor de la Precisión, entre 0.0 y 1.0.
    """
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Verdaderos Positivos (intersección)
    true_positives = np.sum(reference_mask & test_mask)

    # Total de positivos predichos (píxeles en la máscara de prueba)
    # predicted_positives = Verdaderos positivos + Falsos positivos
    predicted_positives = np.sum(test_mask)

    # Calcular la precisión
    # precision (prec) = Verdaderos positivos / (Verdaderos positivos + Falsos positivos)
    prec = (true_positives + epsilon) / (predicted_positives + epsilon)

    return prec


def hausdorff_distance(reference_mask: np.ndarray, test_mask: np.ndarray, library: str = 'scipy', method: str = 'standard') -> float:
    """
    Calcula la Distancia de Hausdorff entre los contornos de dos máscaras, permitiendo
    seleccionar la biblioteca de cálculo (`scipy` o `skimage`) y el método.

    Esta métrica mide la máxima distancia entre el contorno de una máscara y el de la otra,
    siendo útil para evaluar la precisión geométrica, especialmente en estructuras finas
    como las aponeurosis.

    Args:
        reference_mask (np.ndarray): Máscara de referencia (ground truth).
        test_mask (np.ndarray): Máscara de prueba.
        library (str, optional): Biblioteca a utilizar. Puede ser 'scipy' o 'skimage'.
                                 Por defecto es 'scipy'.
        method (str, optional): Método para `skimage`. Puede ser 'standard' o 'modified'.
                                Ignorado si `library` es 'scipy'. Por defecto es 'standard'.

    Returns:
        float: Valor de la Distancia de Hausdorff. Puede ser `np.inf` si una máscara está vacía.

    Raises:
        ValueError: Si la `library` o el `method` no son válidos.
    """
    coords_reference = np.argwhere(reference_mask)
    coords_test = np.argwhere(test_mask)

    if len(coords_reference) == 0 or len(coords_test) == 0:
        return np.inf

    if library == 'scipy':
        h1 = hausdorff_distance_scipy(coords_reference, coords_test)[0]
        h2 = hausdorff_distance_scipy(coords_test, coords_reference)[0]
        return max(h1, h2)

    elif library == 'skimage':
        if method not in ['standard', 'modified']:
            raise ValueError("El método para 'skimage' debe ser 'standard' o 'modified'.")

        dist = hausdorff_distance_skimage(coords_reference, coords_test, method=method)
        return dist

    else:
        raise ValueError("La biblioteca debe ser 'scipy' o 'skimage'.")


def cohen_kappa(reference_mask: np.ndarray, test_mask: np.ndarray) -> float:
    """
    Calcula el coeficiente Kappa de Cohen entre dos máscaras.

    Esta métrica mide la concordancia entre dos evaluadores (la máscara de referencia y la de prueba),
    corrigiendo el acuerdo que podría ocurrir por azar.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.

    Returns:
        float: El valor del Kappa de Cohen, típicamente entre -1.0 y 1.0.
               1 indica acuerdo perfecto, 0 acuerdo por azar, y valores negativos
               un acuerdo peor que el azar.
    """
    # Aplanar las máscaras a 1D para la comparación
    ref_flat = reference_mask.ravel()
    test_flat = test_mask.ravel()

    # Calcular el Kappa
    kappa = cohen_kappa_score(ref_flat, test_flat)

    return kappa
