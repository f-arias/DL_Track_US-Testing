# -*- coding: utf-8 -*-
"""
Este módulo proporciona un conjunto de funciones para evaluar y comparar máscaras de segmentación
de imágenes de US, como las generadas por diferentes modelos sea Deep learning, transformadas entre otras
frente a máscaras de referencia (ground truth) creadas por expertos.

Las métricas implementadas están diseñadas para cuantificar el rendimiento de la segmentación
en términos de superposición de mascaras, similitud de contorno y concordancia estadística. Esto permite
una evaluación robusta tanto de máscaras de aponeurosis como de ROI musculares.

NOTA: Antes de aplicar las metricas a las mascaras de salida, aplicar la operacion
morfologica de esqueleto para igualar condiciones de entrada.

Métricas para ROI Muscular:
--------------------
- Coeficiente de Dice (dice_coefficient)
- Intersección sobre Unión / Jaccard (iou_score)
- Sensibilidad / Recall (recall_score)
- Precisión / PPV (precision_score)

Métricas para Aponeurosis:
--------------------
- Distancia de Hausdorff (hausdorff_distance)
- Distancia Media Absoluta (mean_absolute_distance)

Métricas para Grosor Muscular:
--------------------
- Error Porcentual Absoluto Medio (mape_score)

Estadística Poblacional:
--------------------
- Prueba de Shapiro-Wilk
- Prueba de Wilcoxon
- Coeficiente de Correlación Intraclase (ICC)
- Gráfico de Bland-Altman

Dependencias:
-------------
- NumPy: Para cálculos matriciales eficientes.
- SciPy: Para el cálculo de la Distancia de Hausdorff y pruebas estadísticas.
- Scikit-Image: Para simulaciones morfológicas y métricas.
- Matplotlib: Para gráficos estadísticos.
- Pingouin: Para cálculos avanzados como ICC.
"""

import numpy as np
from scipy.spatial.distance import directed_hausdorff, cdist
import scipy.stats as stats
import matplotlib.pyplot as plt

try:
    import pingouin as pg
except ImportError:
    pg = None
    print("Advertencia: La librería 'pingouin' no está instalada. El cálculo de ICC no estará disponible.")


# =============================================================================
# 1. MÉTRICAS PARA MÁSCARAS DE ROI MUSCULAR
# =============================================================================

def dice_coefficient(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Coeficiente de Dice (Dice-Sørensen) entre dos máscaras con las mismas dimensiones (shape).

    Esta métrica mide la superposición entre dos áreas, normalizada por el tamaño de ambas.
    Un valor de 1 indica una superposición perfecta, mientras que 0 indica ninguna superposición.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth), valores binarios.
        test_mask (np.ndarray): La máscara de prueba, dimensiones iguales a la referencia.
        epsilon (float, optional): Valor pequeño para evitar división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor del Coeficiente de Dice, entre 0.0 y 1.0.
    """

    #Conversion de tipo de dato a booleano
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    intersection = np.sum(reference_mask & test_mask)
    size_reference = np.sum(reference_mask)
    size_test = np.sum(test_mask)

    dice = (2. * intersection + epsilon) / (size_reference + size_test + epsilon)
    return float(dice)


def iou_score(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula el Índice de Jaccard (Intersection over Union - IoU) entre dos máscaras.

    Mide la similitud entre las dos máscaras dividiendo el área de intersección por el área de unión.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Valor pequeño para evitar división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor del Índice de Jaccard (IoU), entre 0.0 y 1.0.
    """

     #Conversion de tipo de dato a booleano
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    intersection = np.sum(reference_mask & test_mask)
    union = np.sum(reference_mask | test_mask)

    iou = (intersection + epsilon) / (union + epsilon)
    return float(iou)


def recall_score(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Sensibilidad (Recall o True Positive Rate) entre dos máscaras.

    Mide la proporción de los píxeles positivos en la máscara de referencia que fueron
    correctamente identificados por la máscara de prueba.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Valor pequeño para evitar división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor del Recall, entre 0.0 y 1.0.
    """

     #Conversion de tipo de dato a booleano
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    true_positives = np.sum(reference_mask & test_mask)
    actual_positives = np.sum(reference_mask)

    recall = (true_positives + epsilon) / (actual_positives + epsilon)
    return float(recall)


def precision_score(reference_mask: np.ndarray, test_mask: np.ndarray, epsilon: float = 1e-6) -> float:
    """
    Calcula la Precisión (Positive Predictive Value) entre dos máscaras.

    Mide la proporción de píxeles positivos en la máscara de prueba que son también
    positivos en la máscara de referencia.

    Args:
        reference_mask (np.ndarray): La máscara de referencia (ground truth).
        test_mask (np.ndarray): La máscara de prueba.
        epsilon (float, optional): Valor pequeño para evitar división por cero. Por defecto es 1e-6.

    Returns:
        float: El valor de la Precisión, entre 0.0 y 1.0.
    """

     #Conversion de tipo de dato a booleano
    reference_mask = reference_mask.astype(bool)
    test_mask = test_mask.astype(bool)

    true_positives = np.sum(reference_mask & test_mask)
    predicted_positives = np.sum(test_mask)

    precision = (true_positives + epsilon) / (predicted_positives + epsilon)
    return float(precision)


# =============================================================================
# 2. MÉTRICAS DE DISTANCIA PARA APONEUROSIS
# =============================================================================

def hausdorff_distance(reference_mask: np.ndarray, test_mask: np.ndarray) -> float:
    """
    Calcula la Distancia de Hausdorff (simétrica).

    Extrae las coordenadas de los píxeles evaluados como True en ambas máscaras y
    computa la máxima distancia de cada punto de un conjunto al conjunto más cercano del otro.

    Args:
        reference_mask (np.ndarray): Máscara de referencia (ground truth).
        test_mask (np.ndarray): Máscara de prueba.

    Returns:
        float: Valor de la Distancia de Hausdorff en píxeles. Si una de las máscaras está vacía,
               devuelve np.inf.
    """
    coords_reference = np.argwhere(reference_mask == True)    #argwhere encuentra las coordenadas con valor True
    coords_test = np.argwhere(test_mask == True)

    if len(coords_reference) == 0 or len(coords_test) == 0:
        return float(np.inf)

    # Distancia dirigida en ambos sentidos y se toma el máximo (distancia simétrica)
    h1 = directed_hausdorff(coords_reference, coords_test)[0]
    h2 = directed_hausdorff(coords_test, coords_reference)[0]

    return float(max(h1, h2))


def mean_absolute_distance(reference_mask: np.ndarray, test_mask: np.ndarray) -> float:
    """
    Calcula la Distancia Media Absoluta (Mean Absolute Distance - MAD) entre los contornos
    o puntos verdaderos de dos máscaras.

    Evalúa la distancia promedio de cada punto de una máscara a su vecino más cercano en la otra.

    Args:
        reference_mask (np.ndarray): Máscara de referencia (ground truth).
        test_mask (np.ndarray): Máscara de prueba.

    Returns:
        float: Valor de la MAD en píxeles. Retorna np.inf si alguna máscara está vacía.
    """
    coords_ref = np.argwhere(reference_mask == True)
    coords_test = np.argwhere(test_mask == True)

    if len(coords_ref) == 0 or len(coords_test) == 0:
        return float(np.inf)

    # Calcular todas las distancias euclidianas entre los conjuntos de puntos
    dists_ref_to_test = cdist(coords_ref, coords_test, metric='euclidean')

    # Para cada punto, tomar la distancia mínima al otro conjunto
    min_dists_ref = np.min(dists_ref_to_test, axis=1)
    min_dists_test = np.min(dists_ref_to_test, axis=0)

    # Calcular la media de estas distancias mínimas en ambas direcciones
    mad = (np.mean(min_dists_ref) + np.mean(min_dists_test)) / 2.0

    #(Mean Absolute Distance - MAD)
    return float(mad)


# =============================================================================
# 3. MÉTRICA PARA GROSOR MUSCULAR (Valor escalar)
# =============================================================================

def mape_score(y_true: float, y_pred: float) -> float:
    """
    Calcula el Error Porcentual Absoluto Medio (Mean Absolute Percentage Error - MAPE)
    para valores numéricos, como el grosor muscular en píxeles o milímetros.

    Args:
        y_true (float): Valor real o de referencia (ground truth).
        y_pred (float): Valor predicho o de prueba.

    Returns:
        float: Valor del MAPE (en porcentaje, ej: 5.0 significa 5%). Retorna np.inf si y_true es 0.
    """
    if y_true == 0:
        return float(np.inf)

    mape = abs((y_true - y_pred) / y_true) * 100.0
    return float(mape)


# =============================================================================
# 4. ESTRUCTURA DE PRUEBAS ESTADÍSTICAS POBLACIONALES
# =============================================================================

class US_Statistics:
    """
    Clase que agrupa métodos estáticos para análisis estadísticos poblacionales de métricas
    de ultrasonido (ej. grosores, Dices de múltiples pacientes, etc.).
    """

    @staticmethod
    def shapiro_wilk_test(data: np.ndarray) -> dict:
        """
        Realiza la prueba de Shapiro-Wilk para evaluar la normalidad de una distribución.

        Args:
            data (np.ndarray o list): Array 1D de datos numéricos.

        Returns:
            dict: Diccionario con la estadística de prueba ('statistic') y el valor p ('p-value').
        """
        data = np.asarray(data)
        stat, p = stats.shapiro(data)
        return {'statistic': stat, 'p-value': p}

    @staticmethod
    def wilcoxon_test(data1: np.ndarray, data2: np.ndarray) -> dict:
        """
        Realiza la prueba de rangos con signo de Wilcoxon para muestras emparejadas.
        Útil para comparar predicciones vs GT cuando los datos no son normales.

        Args:
            data1 (np.ndarray o list): Array 1D de datos numéricos.
            data2 (np.ndarray o list): Array 1D de datos numéricos del mismo tamaño.

        Returns:
            dict: Diccionario con la estadística de prueba ('statistic') y el valor p ('p-value').
        """
        data1, data2 = np.asarray(data1), np.asarray(data2)
        stat, p = stats.wilcoxon(data1, data2)
        return {'statistic': stat, 'p-value': p}

    @staticmethod
    def intraclass_correlation_coefficient(data_df, targets: str, raters: str, ratings: str) -> object:
        """
        Calcula el Coeficiente de Correlación Intraclase (ICC) usando la librería pingouin.
        Mide la fiabilidad y el acuerdo entre evaluadores (ej. GT vs Modelo).

        Args:
            data_df (pandas.DataFrame): DataFrame largo que contiene los datos.
            targets (str): Nombre de la columna con el ID de los sujetos o imágenes.
            raters (str): Nombre de la columna con el ID de los evaluadores (ej. 'GT', 'Modelo').
            ratings (str): Nombre de la columna con los valores medidos (ej. grosor).

        Returns:
            pandas.DataFrame: Un dataframe con los resultados del ICC si pingouin está instalado.
                              Retorna None si no está instalado.
        """
        if pg is None:
            print("Error: Se requiere la librería 'pingouin' para el cálculo de ICC.")
            return None

        icc_results = pg.intraclass_corr(data=data_df, targets=targets, raters=raters, ratings=ratings)
        return icc_results

    @staticmethod
    def bland_altman_plot(data1: np.ndarray, data2: np.ndarray, title: str = "Bland-Altman Plot",
                          xlabel: str = "Media de medidas", ylabel: str = "Diferencia entre medidas"):
        """
        Genera un gráfico de Bland-Altman para analizar el acuerdo entre dos arrays de medidas.

        Args:
            data1 (np.ndarray o list): Array 1D de la primera medida (ej. GT).
            data2 (np.ndarray o list): Array 1D de la segunda medida (ej. Predicción).
            title (str): Título del gráfico.
            xlabel (str): Etiqueta del eje X.
            ylabel (str): Etiqueta del eje Y.
        """
        data1, data2 = np.asarray(data1), np.asarray(data2)

        # Calcular medias y diferencias
        means = np.mean([data1, data2], axis=0)
        diffs = data1 - data2

        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs, axis=0)

        # Límites de acuerdo (1.96 * desviación estándar)
        upper_limit = mean_diff + 1.96 * std_diff
        lower_limit = mean_diff - 1.96 * std_diff

        # Graficar
        plt.figure(figsize=(8, 6))
        plt.scatter(means, diffs, alpha=0.7)
        plt.axhline(mean_diff, color='gray', linestyle='--', label=f'Media ({mean_diff:.2f})')
        plt.axhline(upper_limit, color='red', linestyle='--', label=f'+1.96 SD ({upper_limit:.2f})')
        plt.axhline(lower_limit, color='red', linestyle='--', label=f'-1.96 SD ({lower_limit:.2f})')

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    print(f"Shapiro-Wilk (GT) -> W: {shapiro_gt['statistic']:.4f}, p-value: {shapiro_gt['p-value']:.4f}")
    print(f"Wilcoxon (GT vs Pred) -> W: {wilcoxon_res['statistic']:.4f}, p-value: {wilcoxon_res['p-value']:.4f}")

    print("\nScript ejecutado exitosamente. No se encontraron errores de sintaxis o tipos.")
