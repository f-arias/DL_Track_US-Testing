# Ajuste de Salida y Docstring

En el archivo `DL_Track_US/gui_helpers/do_calculations.py`, la función `doCalculations_custom` ha sido modificada para mejorar la estructura de sus salidas y la claridad de su documentación.

## Cambios Realizados

### 1. Modificación en el Orden de las Salidas

Se ha intercambiado el orden de dos salidas para agruparlas de una manera más lógica. Específicamente:

-   El **grosor muscular (`midthick`)** ahora se encuentra en la posición de salida `[4]`.
-   La **máscara de la región de interés (`mask_roi`)** ahora se encuentra en la posición de salida `[5]`.

Este cambio fue realizado en la declaración `return` de la función.

### 2. Ampliación de las Salidas de las Aponeurosis

Las salidas correspondientes a las coordenadas de las aponeurosis superficial y profunda (`aponeurosis_sup` y `aponeurosis_inf`) han sido ampliadas. Anteriormente, cada una de estas salidas era una lista de dos arrays (`[x_coords, y_coords]`). Ahora, se ha añadido un tercer elemento:

-   Un **entero que representa el número de coordenadas (X, Y)** que componen la aponeurosis.

La nueva estructura de estas salidas es `[x_coords, y_coords, num_coords]`.

### 3. Actualización del Docstring

El docstring de la función `doCalculations_custom` ha sido actualizado para reflejar estos cambios:

-   Se ha corregido la descripción del orden de las salidas en la sección `Returns`.
-   Se ha añadido una **enumeración numérica (de 0 a 8)** al inicio de la descripción de cada salida para facilitar su identificación por índice.
-   Se ha documentado la adición del número de coordenadas a las salidas de las aponeurosis.
