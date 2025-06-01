# Requisitos del Proyecto: Subdivisión Automatizada de Terrenos Poligonales Irregulares

## 1. Introducción

Este documento detalla los requisitos funcionales, no funcionales, técnicos y los algoritmos clave para el desarrollo de un software profesional destinado a la subdivisión automatizada de terrenos poligonales irregulares. El sistema se desarrollará en Python utilizando el framework Django, se integrará con OpenStreetMap para la visualización y definición de terrenos, y utilizará MySQL como sistema de gestión de bases de datos. El objetivo principal es proporcionar una herramienta eficiente y precisa para urbanistas, arquitectos e ingenieros, basada en técnicas computacionales geométricas y criterios urbanísticos, tal como se describe en el perfil de proyecto de investigación proporcionado.

## 2. Requisitos Funcionales

El software deberá permitir las siguientes funcionalidades:

### 2.1. Gestión de Usuarios y Proyectos
-   **RF001:** Registro y autenticación de usuarios.
-   **RF002:** Creación, edición y eliminación de proyectos de subdivisión. Cada proyecto estará asociado a un usuario.

### 2.2. Definición y Gestión de Terrenos
-   **RF003:** Importación de terrenos poligonales irregulares a través de formatos estándar (e.g., GeoJSON, KML, Shapefile) o mediante dibujo interactivo sobre una interfaz de mapa (OpenStreetMap).
-   **RF004:** Visualización del terreno importado/dibujado sobre OpenStreetMap.
-   **RF005:** Almacenamiento de la geometría del terreno y sus metadatos asociados (nombre, descripción, ubicación).
-   **RF006:** Validación de la geometría del polígono (e.g., cierre, no auto-intersecciones).

### 2.3. Configuración de Parámetros de Subdivisión
-   **RF007:** Ingreso de criterios urbanísticos y geométricos para la subdivisión, tales como:
    -   Área mínima y máxima de los lotes resultantes.
    -   Frente mínimo de los lotes.
    -   Acceso a vías (existentes o propuestas).
    -   Orientación preferente de los lotes.
    -   Porcentaje de área destinada a vías y equipamiento (si aplica).
    -   Número deseado de lotes (opcional).
-   **RF008:** Selección del algoritmo o método de subdivisión a aplicar.

### 2.4. Proceso de Subdivisión Automatizada
-   **RF009:** Ejecución de algoritmos de subdivisión basados en los parámetros y el terreno definido.
-   **RF010:** Generación de las geometrías de los lotes resultantes.

### 2.5. Visualización y Análisis de Resultados
-   **RF011:** Visualización interactiva de los lotes subdivididos sobre el mapa de OpenStreetMap.
-   **RF012:** Presentación de estadísticas de la subdivisión (e.g., número de lotes, área promedio, desviación de áreas, área total aprovechada).
-   **RF013:** Posibilidad de ajustar manualmente los resultados de la subdivisión (edición básica de geometrías de lotes, si es factible dentro del alcance).

### 2.6. Exportación de Resultados
-   **RF014:** Exportación de los lotes subdivididos en formatos geoespaciales comunes (e.g., GeoJSON, Shapefile).
-   **RF015:** Generación de un informe básico de la subdivisión en formato PDF (resumen del proyecto, parámetros, estadísticas y visualización).

## 3. Requisitos No Funcionales

-   **RNF001 (Rendimiento):** El sistema deberá procesar subdivisiones de terrenos de complejidad moderada en un tiempo razonable (objetivo: menos de unos minutos para terrenos típicos).
-   **RNF002 (Usabilidad):** La interfaz de usuario deberá ser intuitiva y fácil de usar para profesionales del urbanismo y la ingeniería, incluso sin un conocimiento profundo en SIG avanzado.
-   **RNF003 (Fiabilidad):** El software deberá ser estable y producir resultados consistentes y geométricamente válidos.
-   **RNF004 (Mantenibilidad):** El código fuente deberá ser limpio, bien documentado, modular y seguir las mejores prácticas de desarrollo en Django y Python para facilitar futuras actualizaciones y mantenimiento.
-   **RNF005 (Escalabilidad):** La arquitectura deberá permitir la gestión de un número creciente de usuarios y proyectos. La base de datos MySQL deberá estar optimizada para consultas geoespaciales si es posible (o considerar PostGIS si las capacidades nativas de MySQL son insuficientes para operaciones complejas, aunque el requisito es MySQL).
-   **RNF006 (Seguridad):** Se implementarán medidas básicas de seguridad para la autenticación de usuarios y la protección de datos.
-   **RNF007 (Profesionalismo):** El producto final debe tener un acabado profesional, tanto en su funcionalidad como en su presentación.

## 4. Requisitos Técnicos

-   **RT001 (Plataforma):** Aplicación web desarrollada con Python y el framework Django.
-   **RT002 (Base de Datos):** MySQL para el almacenamiento de datos de usuarios, proyectos, terrenos y lotes. Se utilizarán las capacidades espaciales de MySQL si están disponibles y son adecuadas, o se manejarán geometrías como WKT/GeoJSON en campos de texto si es necesario.
-   **RT003 (Entorno Virtual):** Uso de `venv` para la gestión de dependencias del proyecto Python.
-   **RT004 (Frontend):** HTML, CSS, JavaScript. Se utilizará una librería de mapas como Leaflet.js para la integración con OpenStreetMap.
-   **RT005 (Librerías Python Clave):
    -   Django (framework web)
    -   GeoDjango (si se decide usar sus capacidades, aunque requiere PostGIS/SpatiaLite/Oracle. Para MySQL, se usarán librerías geométricas directamente)
    -   Shapely (manipulación y análisis de geometrías)
    -   GeoPandas (manejo de datos geoespaciales tabulares)
    -   Fiona (lectura y escritura de formatos vectoriales, si es necesario para importación/exportación directa)
    -   PyProj (transformaciones de coordenadas)
    -   NumPy, SciPy (para cálculos numéricos y algoritmos)
    -   `mysqlclient` (conector MySQL para Django)
    -   ReportLab o similar (para generación de PDF)
-   **RT006 (Control de Versiones):** Git.

## 5. Algoritmos y Criterios de Subdivisión

El núcleo del software residirá en la implementación de algoritmos capaces de subdividir terrenos poligonales irregulares. Se explorarán e implementarán, de forma progresiva y según viabilidad:

### 5.1. Criterios Geométricos y Urbanísticos Clave:
-   **Forma del Terreno:** Adaptación a la irregularidad del polígono original.
-   **Área de Lotes:** Cumplimiento de rangos de área especificados.
-   **Frente de Lotes:** Asegurar un frente mínimo a vía pública o acceso.
-   **Acceso:** Garantizar que cada lote tenga acceso.
-   **Regularidad de Lotes:** Intentar generar formas de lotes lo más regulares y funcionales posible (e.g., rectangulares o trapezoidales).
-   **Continuidad Vial:** Consideración de la red vial existente y/o propuesta.
-   **Pendiente del Terreno:** (Consideración avanzada, podría estar fuera del alcance inicial si no hay datos DEM fácilmente integrables).
-   **Normativas Locales:** El sistema permitirá ingresar parámetros que reflejen normativas, pero no contendrá una base de datos de normativas específicas de múltiples localidades (se enfoca en los parámetros que el usuario provee).

### 5.2. Algoritmos Potenciales (inspirados en el documento de tesis):

La implementación comenzará con enfoques más simples y podrá evolucionar hacia técnicas más complejas.

-   **A001 (Basados en Heurísticas Geométricas):**
    -   División recursiva del polígono.
    -   Métodos de barrido (sweep-line).
    -   Subdivisión basada en offset de bordes y líneas de partición.
-   **A002 (Diagramas de Voronoi / Voronoi de Laguerre):**
    -   Utilizar diagramas de Voronoi (posiblemente ponderados o de Laguerre) para generar una partición inicial, ajustando los generadores para cumplir con criterios de área y forma. Esta es una técnica mencionada prominentemente en el PDF.
-   **A003 (Optimización / Metaheurísticos - Exploración si el tiempo lo permite):
    -   **Algoritmos Genéticos (AG):** Para optimizar la configuración de los lotes según una función objetivo que combine varios criterios (área, forma, frente, etc.).
    -   **Particle Swarm Optimization (PSO), Differential Evolution (DE), Ant Colony Optimization (ACO):** Mencionados en el PDF como LRES, podrían explorarse conceptualmente o con implementaciones simplificadas si el proyecto se extiende.
    -   **Simulated Annealing (SA):** Para buscar soluciones óptimas evitando mínimos locales.
-   **A004 (Lógica Difusa - Conceptual):** Podría usarse para manejar la imprecisión en los criterios urbanísticos o para ponderar diferentes objetivos en un enfoque multiobjetivo. Su implementación completa es compleja.
-   **A005 (Optimización Bi-nivel - Conceptual):** Mencionada para integrar diseño de calles y subdivisión. Probablemente fuera del alcance de una primera versión profesional, pero la arquitectura podría no impedir futuras extensiones.

**Enfoque Inicial de Implementación:** Se priorizará un algoritmo robusto basado en heurísticas geométricas y/o una adaptación de diagramas de Voronoi, que permita cumplir con los requisitos funcionales básicos de subdivisión y criterios urbanísticos configurables.

## 6. Estructura de la Base de Datos (MySQL)

Se definirán al menos las siguientes tablas (esquema simplificado):

-   `Usuarios` (id, username, password_hash, email, ...)
-   `Proyectos` (id, usuario_id, nombre_proyecto, descripcion, fecha_creacion, ...)
-   `Terrenos` (id, proyecto_id, nombre_terreno, geometria_wkt_o_geojson, area_total, metadatos_json, ...)
-   `ParametrosSubdivision` (id, proyecto_id, area_min_lote, area_max_lote, frente_min, algoritmo_seleccionado, otros_criterios_json, ...)
-   `LotesResultantes` (id, terreno_id, geometria_lote_wkt_o_geojson, area_lote, frente_lote, numero_lote, ...)

## 7. Interfaz de Usuario (Conceptos)

-   Panel de control para gestión de proyectos.
-   Vista de mapa interactiva (basada en Leaflet/OpenStreetMap) para:
    -   Visualizar y dibujar/cargar el polígono del terreno.
    -   Mostrar los lotes resultantes.
-   Formularios para ingresar parámetros de subdivisión.
-   Visualización de estadísticas y resultados.

## 8. Consideraciones Adicionales

-   **Internacionalización (i18n):** Inicialmente en español, pero la estructura de Django facilita la futura adición de otros idiomas.
-   **Documentación:** Se generará documentación técnica y de usuario.

Este documento servirá como guía para el desarrollo del proyecto. Cualquier modificación o adición a estos requisitos será documentada y acordada.
