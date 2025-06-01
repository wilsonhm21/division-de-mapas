# Documentación de Arquitectura: Sistema de Subdivisión Automatizada de Terrenos

## 1. Introducción

Este documento describe la arquitectura del sistema de subdivisión automatizada de terrenos poligonales irregulares. El sistema está diseñado como una aplicación web utilizando el framework Django para el backend, una interfaz de usuario basada en HTML, CSS y JavaScript con Leaflet.js para la interacción con mapas de OpenStreetMap, y MySQL como base de datos.

## 2. Objetivos de la Arquitectura

Los principales objetivos que guiaron el diseño de la arquitectura son:

-   **Modularidad:** Separar las preocupaciones en componentes bien definidos para facilitar el desarrollo, mantenimiento y la escalabilidad.
-   **Usabilidad:** Proporcionar una interfaz de usuario intuitiva para profesionales del urbanismo y la ingeniería.
-   **Rendimiento:** Asegurar que las operaciones de subdivisión y manipulación geométrica se realicen en tiempos razonables.
-   **Fiabilidad:** Garantizar la consistencia y validez de los datos y los resultados de la subdivisión.
-   **Escalabilidad:** Permitir el crecimiento futuro en términos de usuarios, datos y funcionalidades (como algoritmos de subdivisión más complejos).

## 3. Vista General de la Arquitectura

El sistema sigue una arquitectura de tres capas típica de aplicaciones web:

1.  **Capa de Presentación (Frontend):** Responsable de la interacción con el usuario. Construida con HTML, CSS y JavaScript. Utiliza Leaflet.js para la visualización de mapas (OpenStreetMap) y la interacción con geometrías (dibujo, edición de polígonos).
2.  **Capa de Aplicación (Backend):** Implementada con Django. Contiene la lógica de negocio, gestión de datos, API RESTful para la comunicación con el frontend, y la orquestación de los algoritmos de subdivisión.
3.  **Capa de Datos (Persistencia):** Utiliza MySQL para almacenar toda la información persistente, incluyendo datos de usuarios, proyectos, terrenos (geometrías), parámetros de subdivisión y lotes resultantes.

## 4. Componentes Detallados

### 4.1. Frontend

-   **Interfaz de Mapa (`map_interface.html`):
    -   Utiliza **Leaflet.js** para mostrar teselas de OpenStreetMap.
    -   Integra **Leaflet.Draw** para permitir al usuario dibujar, editar y eliminar polígonos de terreno directamente en el mapa.
    -   Muestra los lotes resultantes de la subdivisión.
    -   Se comunica con el backend a través de llamadas AJAX a la API RESTful para guardar/cargar terrenos y solicitar subdivisiones.
-   **Panel de Información:** Muestra información relevante como el GeoJSON del polígono actual, ID del terreno, y permite ingresar parámetros para la subdivisión (e.g., número de lotes).
-   **Lógica JavaScript (`map_interface.html` embutido):
    -   Maneja eventos del mapa (creación, edición de geometrías).
    -   Construye y envía peticiones a la API del backend.
    -   Procesa las respuestas de la API y actualiza la interfaz (e.g., muestra los lotes subdivididos).

### 4.2. Backend (Django)

-   **Proyecto Django (`subdivision_project`):
    -   `settings.py`: Configuración del proyecto, incluyendo la base de datos MySQL, aplicaciones instaladas (como `rest_framework` y `core`), middleware, etc.
    -   `urls.py`: Enrutamiento principal del proyecto, que incluye las URLs de la aplicación `core`.
-   **Aplicación Principal (`core`):
    -   `models.py`: Define los modelos de datos ORM de Django:
        -   `User` (de `django.contrib.auth`): Para la gestión de usuarios.
        -   `Proyecto`: Agrupa terrenos y parámetros bajo un proyecto específico de un usuario.
        -   `Terreno`: Almacena la geometría del polígono del terreno (como GeoJSON en un `TextField`), su nombre, proyecto asociado, y metadatos.
        -   `ParametrosSubdivision`: Almacena los criterios y parámetros que el usuario define para una subdivisión (e.g., número de lotes, algoritmo a usar, áreas mínimas/máximas - aunque no todos implementados en la versión actual).
        -   `LoteResultante`: Almacena las geometrías de los lotes generados por el proceso de subdivisión.
    -   `views.py`:
        -   `map_view`: Vista simple que renderiza la plantilla HTML de la interfaz del mapa.
        -   **API ViewSets (usando Django REST Framework):**
            -   `ProyectoViewSet`, `TerrenoViewSet`, `ParametrosSubdivisionViewSet`, `LoteResultanteViewSet`: Proveen endpoints CRUD (Crear, Leer, Actualizar, Eliminar) para los modelos correspondientes.
            -   `TerrenoViewSet` incluye una acción personalizada `@action(detail=True, methods=["post"], url_path="subdivide")` para invocar la lógica de subdivisión para un terreno específico.
            -   `TerrenoViewSet` también incluye una acción personalizada `@action(detail=True, methods=["get"], url_path="export")` para exportar la geometría del terreno y sus lotes (si existieran y estuvieran guardados) como un archivo GeoJSON.
    -   `serializers.py`: Define cómo los modelos de Django se convierten a/desde formatos como JSON para la API RESTful. Se utilizan `ModelSerializer` de Django REST Framework.
    -   `urls.py` (de la app `core`): Define las rutas para la vista del mapa y registra los ViewSets de la API con un `DefaultRouter`.
    -   `subdivision_logic.py`: Módulo separado que contiene la lógica de los algoritmos de subdivisión. Actualmente implementa `simple_subdivision_by_line` que utiliza la librería **Shapely** para la manipulación geométrica (validación, buffer, split).
    -   `admin.py`: Configuración para registrar los modelos en la interfaz de administración de Django (no detallada en el desarrollo actual, pero es una capacidad estándar de Django).
-   **Librerías Python Clave (además de Django y DRF):
    -   `mysqlclient`: Conector para la base de datos MySQL.
    -   `Shapely`: Para operaciones geométricas robustas (validación, cálculo de área, división de polígonos).
    -   `GeoPandas`, `Fiona`, `PyProj`: Instaladas para futuras capacidades geoespaciales más avanzadas, aunque no se utilizan extensivamente en la lógica de subdivisión simple actual.

### 4.3. Capa de Datos

-   **Base de Datos MySQL:**
    -   Almacena los datos definidos en `core/models.py`.
    -   Las geometrías se guardan como cadenas de texto en formato GeoJSON en campos `TextField`. Para operaciones espaciales complejas directamente en la base de datos, se requeriría el uso de tipos de datos espaciales de MySQL y funciones espaciales, o preferiblemente una base de datos con mejor soporte geoespacial como PostGIS (si se usara GeoDjango de forma más intensiva).
    -   Se crea una base de datos (`land_subdivision_db`) y un usuario (`land_user`) con los privilegios necesarios.

## 5. Flujo de Datos y Procesos

### 5.1. Carga/Dibujo de un Terreno

1.  Usuario dibuja un polígono en la interfaz de Leaflet o carga uno existente por ID.
2.  El GeoJSON del polígono se muestra en un `textarea`.
3.  Usuario hace clic en "Guardar Polígono".
4.  JavaScript envía una petición POST AJAX a la API (`/core/api/terrenos/`) con el GeoJSON, nombre del terreno y ID del proyecto.
5.  `TerrenoViewSet` en Django recibe la petición, valida los datos usando `TerrenoSerializer`.
6.  Si es válido, se crea un nuevo objeto `Terreno` y se guarda en la base de datos MySQL.
7.  La API responde con el ID del terreno guardado.
8.  El frontend actualiza la interfaz.

### 5.2. Subdivisión de un Terreno

1.  Usuario carga un terreno existente o utiliza el recién dibujado/guardado.
2.  Usuario ingresa el número de lotes deseados.
3.  Usuario hace clic en "Subdividir Terreno".
4.  JavaScript envía una petición POST AJAX a la API (`/core/api/terrenos/<id_terreno>/subdivide/`) con el número de lotes.
5.  `TerrenoViewSet` (acción `subdivide_terreno`) recibe la petición.
6.  Se recupera el objeto `Terreno` de la base de datos.
7.  Se invoca la función `simple_subdivision_by_line` de `subdivision_logic.py`, pasándole el GeoJSON del terreno y el número de lotes.
8.  La lógica de subdivisión utiliza Shapely para procesar la geometría y generar los lotes.
9.  La API responde con un JSON que contiene los GeoJSON de los lotes resultantes o un mensaje de error.
10. El frontend recibe la respuesta y dibuja los lotes resultantes en una nueva capa de Leaflet en el mapa.

### 5.3. Exportación de Terreno

1.  Usuario carga un terreno.
2.  (Funcionalidad a añadir en el frontend) Un botón "Exportar GeoJSON" llamaría a la API.
3.  JavaScript enviaría una petición GET a `/core/api/terrenos/<id_terreno>/export/`.
4.  `TerrenoViewSet` (acción `export_terreno_geojson`) recupera el terreno.
5.  Construye un `FeatureCollection` GeoJSON que incluye la geometría del terreno original (y potencialmente los lotes subdivididos si estuvieran guardados y se implementara esa lógica).
6.  La API responde con el archivo GeoJSON para su descarga.

## 6. Consideraciones de Despliegue (No implementado)

-   Para un entorno de producción, se necesitaría un servidor WSGI (como Gunicorn o uWSGI) y un servidor web (como Nginx) para servir la aplicación Django y los archivos estáticos.
-   La base de datos MySQL debería estar configurada para producción (seguridad, backups, etc.).
-   La variable `DEBUG` en `settings.py` debería ser `False`.
-   `SECRET_KEY` debería ser gestionada de forma segura.
-   `ALLOWED_HOSTS` debería configurarse adecuadamente.

## 7. Posibles Mejoras y Extensiones Futuras

-   Implementación de algoritmos de subdivisión más avanzados (e.g., basados en Voronoi, optimización heurística) como se menciona en el documento de tesis.
-   Integración completa de criterios urbanísticos en los algoritmos (frente mínimo, acceso a vías, etc.).
-   Uso de una base de datos con capacidades geoespaciales más potentes (e.g., PostGIS con GeoDjango) para consultas y análisis espaciales en el backend.
-   Mejoras en la interfaz de usuario: selección de proyectos, gestión de parámetros de subdivisión más detallada, visualización 3D (si se integran datos DEM).
-   Autenticación de usuarios y gestión de permisos más robusta.
-   Pruebas unitarias y de integración más completas.
-   Capacidad de importar/exportar en más formatos (Shapefile, KML).

Este documento proporciona una visión general de la arquitectura actual del sistema. Está sujeto a cambios y evoluciones a medida que el proyecto se desarrolle y se refinen los requisitos.
