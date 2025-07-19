# Análisis de la función `doCalculations_custom`

## Problema

La función `doCalculations_custom` en `DL_Track_US/gui_helpers/do_calculations.py` es responsable de calcular los parámetros de la arquitectura muscular a partir de imágenes de ultrasonido. Parte de este proceso implica la creación de una máscara binaria de la región de interés (ROI) entre las aponeurosis superficial y profunda.

El usuario informó que al aplicar y superponer la máscara en la imagen de ultrasonido original, la máscara parece estar desplazada hacia la izquierda.

## Causa Raíz

El error se encuentra en la sección del código que genera la `ex_mask`. La lógica asume incorrectamente que las coordenadas x de las aponeurosis superior e inferior están alineadas.

El código problemático es:

```python
ex_mask = np.zeros(thresh.shape, np.uint8)
ex_1 = 0
ex_2 = np.minimum(len(low_x), len(upp_x))

for ii in range(ex_1, ex_2):    #Barrido columna por columna
    ymin = int(np.floor(upp_y_new[ii]))
    ymax = int(np.ceil(low_y_new[ii]))

    ex_mask[:ymin, ii] = 0    #Sobre la apo. superficial
    ex_mask[ymax:, ii] = 0    #Debajo de la apo. profunda
    ex_mask[ymin:ymax, ii] = 255    #Entre las apos.
```

El bucle itera desde `0` hasta `min(len(low_x), len(upp_x))`, utilizando la variable de bucle `ii` como índice tanto para `upp_y_new` como para `low_y_new`. Sin embargo, no se garantiza que `upp_x` y `low_x` tengan la misma coordenada x inicial o la misma longitud. Esto significa que `upp_x[ii]` y `low_x[ii]` podrían corresponder a diferentes columnas en la imagen, provocando un desplazamiento en la máscara generada.

## Solución Propuesta

Para solucionar esto, la lógica de generación de la máscara debe actualizarse para mapear correctamente las coordenadas y de las aponeurosis a las coordenadas x correspondientes en la imagen.

La solución propuesta implica los siguientes pasos:

1.  Encontrar el rango superpuesto de coordenadas x entre las dos aponeurosis.
2.  Crear funciones de interpolación para ambas aponeurosis para obtener las coordenadas y para cualquier coordenada x dada.
3.  Iterar a través de las coordenadas x superpuestas y rellenar la máscara columna por columna.

Este es el código corregido:

```python
# Creacion de mascara ROI que solo contenga el Musculo limitado por sus aponeurosis
ex_mask = np.zeros(thresh.shape, np.uint8)

# Crear funciones de interpolación para ambas aponeurosis
f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

# Determinar el rango x superpuesto
start_x = int(max(np.min(upp_x), np.min(low_x)))
end_x = int(min(np.max(upp_x), np.max(low_x)))

for x in range(start_x, end_x):
    ymin = int(np.floor(f_upp(x)))
    ymax = int(np.ceil(f_low(x)))

    # Asegurarse de que ymin e ymax estén dentro de los límites de la imagen
    ymin = max(0, ymin)
    ymax = min(ex_mask.shape[0], ymax)

    ex_mask[ymin:ymax, x] = 255
```
Este cambio asegurará que la máscara se genere correctamente, alineándose con las aponeurosis en la imagen original.
