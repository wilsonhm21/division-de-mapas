# Manual de Usuario: Sistema de Subdivisión Automatizada de Terrenos

## 1. Introducción

Bienvenido al Sistema de Subdivisión Automatizada de Terrenos. Esta aplicación web está diseñada para permitir a los usuarios definir terrenos poligonales irregulares en un mapa interactivo, solicitar su subdivisión en un número específico de lotes y visualizar los resultados. Actualmente, la aplicación utiliza un algoritmo de subdivisión simple como prueba de concepto.

## 2. Requisitos Previos (Para Ejecución Local)

Para ejecutar esta aplicación localmente, necesitará:

-   Python 3.11 o superior.
-   MySQL Server instalado y en ejecución.
-   Las librerías Python especificadas en el proyecto (Django, Django REST Framework, Shapely, mysqlclient, etc.).
-   Un navegador web moderno (Chrome, Firefox, Edge).

## 3. Inicio de la Aplicación (Ejecución Local)

1.  **Clonar el Repositorio:** Obtenga el código fuente del proyecto.
2.  **Configurar Base de Datos:** Asegúrese de que MySQL esté configurado con la base de datos `land_subdivision_db` y el usuario `land_user` con la contraseña `LandPassword123` (o modifique `subdivision_project/settings.py` con sus credenciales).
3.  **Entorno Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    ```
4.  **Instalar Dependencias:**
    ```bash
    pip install Django djangorestframework mysqlclient Shapely
    # (y otras si fueran necesarias, como GeoPandas, Fiona, PyProj para funcionalidades extendidas)
    ```
5.  **Aplicar Migraciones:**
    ```bash
    python manage.py makemigrations core
    python manage.py migrate
    ```
6.  **Crear un Superusuario (Opcional, para acceder al admin de Django):
    ```bash
    python manage.py createsuperuser
    ```
7.  **Ejecutar el Servidor de Desarrollo:**
    ```bash
    python manage.py runserver
    ```
8.  **Acceder a la Aplicación:** Abra su navegador web y vaya a `http://127.0.0.1:8000/core/map/`.

## 4. Funcionalidades Principales

La interfaz principal consta de un mapa interactivo a la izquierda y un panel de información y controles a la derecha.

### 4.1. Interacción con el Mapa

-   **Navegación:** Puede hacer clic y arrastrar para moverse por el mapa.
-   **Zoom:** Utilice la rueda del ratón o los controles +/- en el mapa para acercar o alejar.

### 4.2. Dibujar un Nuevo Terreno

1.  En la barra de herramientas de dibujo del mapa (generalmente en el lado izquierdo), seleccione la herramienta de dibujo de polígonos (icono de polígono).
2.  Haga clic en el mapa para definir los vértices de su terreno.
3.  Haga clic en el primer vértice para cerrar el polígono y finalizar el dibujo.
4.  El GeoJSON correspondiente al polígono dibujado aparecerá en el `textarea` "GeoJSON del polígono dibujado" en el panel de información.
5.  El ID del terreno actual se mostrará como "Nuevo (no guardado)".

### 4.3. Editar un Terreno Dibujado

1.  Si ya ha dibujado un polígono, la herramienta de edición (icono de polígono con un lápiz) en la barra de herramientas de dibujo debería estar activa.
2.  Haga clic en el polígono en el mapa para seleccionar sus vértices.
3.  Arrastre los vértices existentes para modificar la forma del polígono.
4.  Haga clic en "Guardar" en los controles de edición del mapa para aplicar los cambios.
5.  El GeoJSON en el `textarea` se actualizará.

### 4.4. Guardar un Terreno

1.  Después de dibujar o editar un terreno, haga clic en el botón **"Guardar Polígono"** en el panel de información.
2.  Se le pedirá que ingrese un nombre para el terreno. Escriba un nombre y haga clic en "Aceptar".
3.  Si se guarda correctamente, recibirá una alerta con el ID del terreno guardado. Este ID también se actualizará en "ID del Terreno actual".
    *Nota: Actualmente, todos los terrenos se guardan bajo un ID de proyecto simulado (ID=1). Se necesitaría una gestión de proyectos y usuarios más completa para una aplicación de producción.*

### 4.5. Cargar un Terreno Existente

1.  En la sección "Cargar Terreno Existente" del panel de información, ingrese el ID de un terreno previamente guardado en el campo "ID del Terreno".
2.  Haga clic en el botón **"Cargar Polígono"**.
3.  Si el ID es válido, el polígono correspondiente se cargará y se mostrará en el mapa. El GeoJSON y el ID del terreno actual se actualizarán.

### 4.6. Subdividir un Terreno

1.  Asegúrese de tener un terreno cargado o recién guardado (el "ID del Terreno actual" debe mostrar un número).
2.  En la sección "Subdividir Terreno Cargado", ingrese el número deseado de lotes en el campo "Número de Lotes" (por defecto es 2).
3.  Haga clic en el botón **"Subdividir Terreno"**.
4.  La aplicación enviará la solicitud al backend. El panel "Lotes Resultantes" mostrará "Procesando...".
5.  Si la subdivisión es exitosa, los lotes resultantes se dibujarán en el mapa (con colores diferentes para distinguirlos) y se mostrará información sobre ellos (número de lotes y área aproximada) en el panel "Lotes Resultantes".
6.  Si hay un error durante la subdivisión (e.g., la geometría es demasiado compleja para el algoritmo simple, o el número de lotes no es válido), se mostrará un mensaje de error.

### 4.7. Exportar Geometría del Terreno (Funcionalidad Básica)

-   La funcionalidad de exportación está implementada en el backend en la ruta `/core/api/terrenos/<id_terreno>/export/`.
-   Para usarla, necesitaría acceder a esta URL directamente en su navegador (reemplazando `<id_terreno>` con el ID del terreno deseado) o integrar un botón en el frontend que active esta descarga.
-   La exportación genera un archivo `terreno_<id>_export.geojson` que contiene la geometría del terreno original.
    *Nota: La exportación de los lotes subdivididos no está completamente integrada en este flujo simple; el endpoint actual solo exporta el polígono original. Los lotes generados por la subdivisión se muestran en el mapa pero no se guardan persistentemente en la base de datos de forma automática en la versión actual.*

## 5. Limitaciones Conocidas

-   **Algoritmo de Subdivisión Simple:** El algoritmo actual (`simple_subdivision_by_line`) es muy básico y solo realiza una división horizontal. No garantiza un número exacto de lotes si se solicitan más de dos, ni considera criterios urbanísticos complejos (frentes, áreas mínimas, acceso a vías, etc.). Es una prueba de concepto.
-   **Gestión de Proyectos y Usuarios:** La aplicación no cuenta con un sistema completo de gestión de usuarios o proyectos. Todas las operaciones se realizan de forma anónima o bajo un proyecto simulado.
-   **Persistencia de Lotes Subdivididos:** Los lotes generados por la subdivisión se visualizan en el mapa pero no se guardan automáticamente en la base de datos como entidades `LoteResultante` en la interacción actual del frontend. El modelo existe, pero la lógica de guardado automático desde el endpoint de subdivisión no está completamente implementada.
-   **Manejo de Errores Geométricos:** Aunque se intenta validar geometrías, polígonos muy complejos o auto-intersectantes podrían no ser manejados correctamente por el algoritmo simple.
-   **Proyecciones y Áreas:** El cálculo de áreas es aproximado y depende de la proyección de las coordenadas de OpenStreetMap (Web Mercator). Para cálculos de área precisos, se requeriría una gestión de CRS (Sistemas de Referencia de Coordenadas) más sofisticada.

## 6. Solución de Problemas

-   **El mapa no carga:** Verifique su conexión a internet y que no haya bloqueadores de contenido afectando a `openstreetmap.org`.
-   **Error al guardar/cargar/subdividir:** Revise la consola del navegador (usualmente F12) para mensajes de error de JavaScript. Revise también la consola donde se ejecuta el servidor Django para errores del backend.
-   **La subdivisión no produce el resultado esperado:** Recuerde las limitaciones del algoritmo actual. Para subdivisiones complejas, el algoritmo actual no será suficiente.

Gracias por utilizar el Sistema de Subdivisión Automatizada de Terrenos.
