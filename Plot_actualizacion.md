# Actualización de la Visualización del Músculo

Se han realizado las siguientes modificaciones en la gráfica generada por la función `doCalculations_custom`:

- **Elementos Comentados:** Se conservaron pero se comentaron las líneas de código que dibujaban los fascículos y las anotaciones de texto (longitud de fascículo, ángulo de pennación y grosor muscular) para mantener el código original como referencia.
- **Actualización de Aponeurosis:**
    - La aponeurosis superficial ahora se muestra en color **azul**.
    - La aponeurosis profunda ahora se muestra en color **verde oscuro**.
- **Máscara ROI:** Se ha añadido una superposición de la máscara de la región de interés (ROI) con un color púrpura semitransparente para resaltar el área del músculo.
- **Leyenda Mejorada:** La leyenda ha sido movida a la esquina superior izquierda y mejorada para mostrar la correspondencia entre color y término:
    - **Verde Oscuro:** Aponeurosis Profunda
    - **Azul:** Aponeurosis Superficial
    - **Púrpura:** ROI
