# Documentación del Código Fuente: Sistema de Subdivisión Automatizada de Terrenos

## 1. Introducción

Este documento proporciona una visión general de la estructura del código fuente del Sistema de Subdivisión Automatizada de Terrenos. El proyecto está desarrollado en Python utilizando el framework Django.

## 2. Estructura General del Proyecto

El proyecto sigue la estructura estándar de Django:

```
land_subdivision_project/
├── manage.py
├── subdivision_project/         # Directorio de configuración del proyecto Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py          # Configuración principal del proyecto
│   ├── urls.py              # URLs principales del proyecto
│   └── wsgi.py
├── core/                      # Aplicación principal de Django
│   ├── __init__.py
│   ├── admin.py             # Configuración del panel de administración (no usado extensivamente)
│   ├── apps.py              # Configuración de la aplicación
│   ├── migrations/          # Migraciones de la base de datos
│   ├── models.py            # Modelos de datos (ORM de Django)
│   ├── serializers.py       # Serializadores para la API REST
│   ├── subdivision_logic.py # Lógica de los algoritmos de subdivisión
│   ├── templates/
│   │   └── core/
│   │       └── map_interface.html # Plantilla HTML para la interfaz de usuario
│   ├── tests.py             # Archivo para pruebas (no implementadas en detalle)
│   ├── urls.py              # URLs específicas de la aplicación 'core'
│   └── views.py             # Vistas de Django y ViewSets de la API
├── venv/                      # Entorno virtual de Python (si se crea dentro del proyecto)
├── architecture_documentation.md # Documentación de la arquitectura
├── user_manual.md             # Manual de usuario
├── code_documentation.md      # Este archivo
├── project_requirements.md    # Requisitos del proyecto
└── todo.md                    # Lista de tareas del proyecto (seguimiento interno)
```

## 3. Componentes Clave del Código

### 3.1. Configuración del Proyecto (`subdivision_project/`)

-   **`settings.py`**: Contiene toda la configuración del proyecto Django.
    -   `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`.
    -   `INSTALLED_APPS`: Lista las aplicaciones que componen el proyecto, incluyendo `django.contrib.admin`, `django.contrib.auth`, `rest_framework`, y la aplicación personalizada `core`.
    -   `MIDDLEWARE`: Configuración de los middlewares de Django.
    -   `ROOT_URLCONF`: Apunta al archivo de URLs principal (`subdivision_project.urls`).
    -   `TEMPLATES`: Configuración del motor de plantillas.
    -   `DATABASES`: Configuración de la conexión a la base de datos MySQL (`land_subdivision_db`, usuario `land_user`).
    -   `STATIC_URL`: URL para los archivos estáticos.
-   **`urls.py`**: Define el enrutamiento principal del proyecto. Incluye las URLs de la aplicación `admin` y las URLs de la aplicación `core` bajo el prefijo `/core/`.

### 3.2. Aplicación Principal (`core/`)

-   **`models.py`**: Define los modelos de datos que se mapean a tablas en la base de datos MySQL.
    -   `Proyecto`: Representa un proyecto de subdivisión, asociado a un usuario (aunque la gestión de usuarios no está completamente integrada en el frontend).
    -   `Terreno`: Almacena la información de un terreno, incluyendo su `nombre_terreno`, la `geometria_geojson` (como `TextField`), el `proyecto` al que pertenece, y `area_total` (calculable).
    -   `ParametrosSubdivision`: Modelo para almacenar parámetros específicos de una subdivisión (e.g., número de lotes, tipo de algoritmo). No se utiliza extensivamente en la lógica actual del frontend, pero está disponible para futuras mejoras.
    -   `LoteResultante`: Modelo para almacenar la geometría y otros datos de cada lote generado por una subdivisión. La lógica actual de subdivisión no guarda automáticamente los lotes en este modelo desde el frontend, pero el modelo está preparado.
-   **`views.py`**: Contiene la lógica para manejar las peticiones HTTP y generar respuestas.
    -   `map_view(request)`: Una vista simple basada en función que renderiza la plantilla `map_interface.html`.
    -   `ProyectoViewSet`, `TerrenoViewSet`, `ParametrosSubdivisionViewSet`, `LoteResultanteViewSet`: Son `ModelViewSet` de Django REST Framework que proporcionan automáticamente acciones CRUD (Listar, Crear, Recuperar, Actualizar, Destruir) para los modelos correspondientes a través de una API RESTful.
    -   **Acciones Personalizadas en `TerrenoViewSet`**:
        -   `subdivide_terreno(self, request, pk=None)`: Un endpoint POST en `/core/api/terrenos/<pk>/subdivide/` que toma el ID de un terreno y un número de lotes, invoca la lógica de subdivisión y devuelve los lotes resultantes como GeoJSON.
        -   `export_terreno_geojson(self, request, pk=None)`: Un endpoint GET en `/core/api/terrenos/<pk>/export/` que permite descargar la geometría del terreno original como un archivo GeoJSON.
-   **`serializers.py`**: Define cómo los datos de los modelos se convierten a representaciones JSON (y viceversa) para ser utilizados por la API REST.
    -   Se utiliza `serializers.ModelSerializer` para cada modelo (`ProyectoSerializer`, `TerrenoSerializer`, etc.), lo que simplifica la creación de serializadores basados en los campos del modelo.
    -   Incluye manejo de relaciones (e.g., `PrimaryKeyRelatedField` para `proyecto_id` en `TerrenoSerializer`).
-   **`urls.py` (en `core/`)**: Define las rutas específicas para la aplicación `core`.
    -   Una ruta para `map_view`.
    -   Utiliza `DefaultRouter` de Django REST Framework para registrar automáticamente las URLs para los `ViewSet` (e.g., `/api/terrenos/`, `/api/terrenos/<pk>/`).
-   **`subdivision_logic.py`**: Módulo Python independiente que contiene la lógica pura de los algoritmos de subdivisión.
    -   `simple_subdivision_by_line(geojson_polygon_str, num_lots=2)`: Implementa un algoritmo básico de subdivisión. Toma un string GeoJSON de un polígono y el número de lotes deseado. Utiliza la librería `shapely` para:
        -   Convertir el GeoJSON a un objeto `shapely.geometry.Polygon`.
        -   Validar la geometría y intentar repararla (e.g., con `buffer(0)`).
        -   Calcular los límites del polígono.
        -   Crear una `LineString` horizontal para dividir el polígono.
        -   Utilizar `shapely.ops.split()` para dividir el polígono con la línea.
        -   Convertir los polígonos resultantes de nuevo a formato GeoJSON.
        -   Maneja varios casos de error y tipos de entrada GeoJSON (Feature, FeatureCollection, Geometry).
-   **`templates/core/map_interface.html`**: Plantilla HTML que define la interfaz de usuario.
    -   Incluye las librerías Leaflet.js y Leaflet.Draw para la funcionalidad del mapa.
    -   Contiene el `div` para el mapa (`<div id="map"></div>`) y el panel de información (`<div id="info-panel"></div>`).
    -   **JavaScript Embebido**:
        -   Inicializa el mapa Leaflet centrado en Juliaca, Perú.
        -   Configura las capas de teselas de OpenStreetMap.
        -   Configura los controles de dibujo de Leaflet.Draw para polígonos.
        -   Maneja eventos del mapa: `L.Draw.Event.CREATED` (cuando se dibuja un nuevo polígono) y `L.Draw.Event.EDITED` (cuando se edita un polígono existente).
        -   Actualiza un `textarea` con el GeoJSON del polígono actual.
        -   Función `getCookie(name)` para obtener el token CSRF necesario para las peticiones POST a Django.
        -   Función `savePolygon()`: Envía el GeoJSON del polígono dibujado al endpoint `/core/api/terrenos/` (POST) para guardarlo.
        -   Función `loadPolygon()`: Obtiene un terreno por su ID desde el endpoint `/core/api/terrenos/<id>/` (GET) y lo muestra en el mapa.
        -   Función `subdivideCurrentPolygon()`: Envía una solicitud al endpoint `/core/api/terrenos/<id>/subdivide/` (POST) con el número de lotes y muestra los lotes resultantes en el mapa.

## 4. Librerías Externas Clave

-   **Django**: Framework web principal para el backend.
-   **Django REST Framework**: Para construir la API RESTful de manera eficiente.
-   **Shapely**: Librería Python para la manipulación y análisis de geometrías planas. Es fundamental para la validación de polígonos y la lógica de subdivisión.
-   **mysqlclient**: Adaptador de Python para la base de datos MySQL.
-   **Leaflet.js**: Librería JavaScript de código abierto para mapas interactivos.
-   **Leaflet.Draw**: Plugin para Leaflet que añade controles para dibujar y editar geometrías en el mapa.

## 5. Flujo de Trabajo de Desarrollo

1.  **Definición de Modelos (`models.py`):** Se definen las estructuras de datos.
2.  **Migraciones:** Se ejecutan `python manage.py makemigrations` y `python manage.py migrate` para aplicar los cambios de los modelos a la base de datos MySQL.
3.  **Serializadores (`serializers.py`):** Se crean para convertir los modelos a JSON para la API.
4.  **Vistas y ViewSets (`views.py`):** Se implementa la lógica de negocio y los endpoints de la API.
5.  **URLs (`urls.py`):** Se definen las rutas para acceder a las vistas y endpoints.
6.  **Lógica de Negocio Específica (e.g., `subdivision_logic.py`):** Se implementan algoritmos y funciones auxiliares.
7.  **Plantillas HTML y JavaScript (`templates/`):** Se desarrolla la interfaz de usuario que consume la API.

## 6. Consideraciones Adicionales

-   **Pruebas:** El archivo `core/tests.py` está presente pero no contiene pruebas exhaustivas. En un proyecto de producción, se deberían añadir pruebas unitarias y de integración para asegurar la calidad del código.
-   **Seguridad:** Se utiliza el token CSRF de Django para proteger contra ataques CSRF en las peticiones POST. Para una aplicación de producción, se deberían revisar otras consideraciones de seguridad (e.g., XSS, SQL injection - aunque el ORM de Django protege contra esto último en gran medida, validación de entradas, HTTPS).
-   **Manejo de Errores:** Se ha implementado un manejo básico de errores tanto en el frontend (JavaScript `alert`s, mensajes en consola) como en el backend (respuestas HTTP con códigos de error y mensajes JSON). Esto podría mejorarse con un sistema de logging más robusto y mensajes de error más amigables para el usuario.

Esta documentación del código fuente tiene como objetivo proporcionar una guía para entender la organización y los componentes principales del proyecto.
