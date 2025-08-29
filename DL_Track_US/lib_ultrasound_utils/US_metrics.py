# -*- coding: utf-8 -*-
"""
Módulo `US_metrics`

Este módulo proporciona un conjunto de funciones para evaluar y comparar máscaras de segmentación
de imágenes de ultrasonido, como las generadas por modelos de Deep Learning (`DL_Track_US`)
frente a máscaras de referencia (ground truth) creadas por expertos.

Las métricas implementadas están diseñadas para cuantificar el rendimiento de la segmentación
en términos de superposición, similitud de contorno y concordancia estadística. Esto permite
una evaluación robusta tanto de máscaras de aponeurosis como de regiones de interés (ROI) musculares.

Métricas Disponibles:
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

Ejemplo de uso:
---------------
>>> import numpy as np
>>> from DL_Track_US.lib_ultrasound_utils import US_metrics
>>>
>>> # Crear máscaras de ejemplo (binarias)
>>> mascara_referencia = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]])
>>> mascara_prueba = np.array([[1, 1, 1], [1, 0, 0], [0, 0, 0]])
>>>
>>> # Calcular el Coeficiente de Dice
>>> dice_score = US_metrics.dice_coefficient(mascara_referencia, mascara_prueba)
>>> print(f"Coeficiente de Dice: {dice_score:.4f}")
>>>
>>> # Calcular la Distancia de Hausdorff
>>> hausdorff_dist = US_metrics.hausdorff_distance(mascara_referencia, mascara_prueba)
>>> print(f"Distancia de Hausdorff: {hausdorff_dist:.4f}")
"""

import numpy as np
from sklearn.metrics import cohen_kappa_score
from scipy.spatial.distance import directed_hausdorff

def dice_coefficient(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Coeficiente de Dice (Dice-Sørensen) entre dos máscaras binarias.

    Esta métrica mide la superposición entre dos áreas, normalizada por el tamaño de ambas.
    Un valor de 1 indica una superposición perfecta, mientras que 0 indica ninguna superposición.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
                                     Debe ser una matriz de NumPy con valores binarios (0 o 1).
        test_mask (np.ndarray): La máscara de prueba (generada por el modelo).
                                Debe tener las mismas dimensiones que la máscara de referencia.
        epsilon (float, optional): Un valor pequeño para evitar la división por cero si ambas
                                   máscaras están vacías. Por defecto es 1e-6.

    Returns:
        float: El valor del Coeficiente de Dice, un número flotante entre 0.0 y 1.0.
    """
    # Asegurarse de que las máscaras sean booleanas para los cálculos
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Calcular la intersección (Verdaderos Positivos)
    intersection = np.sum(reference_mask & test_mask)

    # Calcular el tamaño de cada máscara
    size_ref = np.sum(reference_mask)
    size_test = np.sum(test_mask)

    # Calcular el coeficiente de Dice
    dice = (2. * intersection + epsilon) / (size_ref + size_test + epsilon)

    return dice


def jaccard_index(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Índice de Jaccard (Intersection over Union - IoU) entre dos máscaras binarias.

    Mide la similitud entre las dos máscaras dividiendo el área de intersección por el área de unión.
    Un valor de 1 indica una superposición perfecta, y 0 indica ninguna superposición.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba (generada por el modelo).
        epsilon (float, optional): Un valor pequeño para evitar la división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor del Índice de Jaccard (IoU), un número flotante entre 0.0 y 1.0.
    """
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    # Calcular la intersección
    intersection = np.sum(reference_mask & test_mask)

    # Calcular la unión
    union = np.sum(reference_mask | test_mask)

    # Calcular el índice de Jaccard
    iou = (intersection + epsilon) / (union + epsilon)

    return iou


def sensitivity(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Sensibilidad (Recall o True Positive Rate) entre dos máscaras.

    Mide la proporción de los píxeles positivos en la máscara de referencia que fueron
    correctamente identificados por la máscara de prueba.

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
    actual_positives = np.sum(reference_mask)

    # Calcular la sensibilidad
    recall = (true_positives + epsilon) / (actual_positives + epsilon)

    return recall


def precision(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Precisión (Positive Predictive Value) entre dos máscaras.

    Mide la proporción de píxeles positivos en la máscara de prueba que son también
    positivos en la máscara de referencia.

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
    predicted_positives = np.sum(test_mask)

    # Calcular la precisión
    prec = (true_positives + epsilon) / (predicted_positives + epsilon)

    return prec


def hausdorff_distance(reference_mask: np.ndarray, test_mask: np.ndarray) -> float:
    """
    Calcula la Distancia de Hausdorff entre los contornos de dos máscaras.

    Esta métrica mide la máxima distancia entre el contorno de una máscara y el contorno de la otra.
    Es una medida del "peor error" en la delineación del borde. Un valor más bajo indica
    una mayor similitud entre los contornos.

    Nota:
        Si una de las máscaras está completamente vacía, la distancia no se puede calcular
        y la función devolverá `np.inf`.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.

    Returns:
        float: El valor de la Distancia de Hausdorff. Puede ser `np.inf` si una máscara está vacía.
    """
    # Obtener las coordenadas de los píxeles del contorno (píxeles > 0)
    coords_ref = np.argwhere(reference_mask)
    coords_test = np.argwhere(test_mask)

    # Si alguna de las máscaras no tiene píxeles positivos, la distancia es infinita
    if len(coords_ref) == 0 or len(coords_test) == 0:
        return np.inf

    # Calcular la distancia de Hausdorff dirigida en ambas direcciones
    h1 = directed_hausdorff(coords_ref, coords_test)[0]
    h2 = directed_hausdorff(coords_test, coords_ref)[0]

    # La distancia de Hausdorff es el máximo de las dos distancias dirigidas
    return max(h1, h2)


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
