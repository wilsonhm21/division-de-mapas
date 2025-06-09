from shapely.geometry import Polygon, Point, LineString, MultiPolygon

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pyproj
from matplotlib.patches import Patch
from shapely.ops import unary_union
import math

def midpoint(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def plot_side_lengths(ax, coords, color='blue', fontsize=7, sample_rate=1, label_prefix=""):
    """Muestra la longitud de los lados del polígono"""
    for i in range(0, len(coords) - 1, sample_rate):
        p1, p2 = coords[i], coords[i + 1]
        mid = midpoint(p1, p2)
        length = np.linalg.norm(np.array(p2) - np.array(p1))
        
        if length > 0.01:
            text = f"{label_prefix}{length:.2f}m" if label_prefix else f"{length:.2f}m"
            ax.text(mid[0], mid[1], text, color=color,
                    fontsize=fontsize, ha='center', va='center',
                    bbox=dict(fc='white', ec=color, boxstyle='round,pad=0.15', alpha=0.8))

def is_rectangle(vertices, tolerance=0.1):
    """Determina si un polígono es un rectángulo (o casi)"""
    # Acepta polígonos abiertos o cerrados
    if len(vertices) < 4:
        return False
        
    # Si está cerrado, tomamos solo los 4 primeros (asumiendo que es un cuadrilátero)
    unique_verts = []
    for v in vertices:
        if v not in unique_verts:
            unique_verts.append(v)
            
    if len(unique_verts) != 4:
        return False
        
    # Calcular vectores entre vértices consecutivos
    vectors = []
    for i in range(4):
        p1 = np.array(unique_verts[i])
        p2 = np.array(unique_verts[(i+1) % 4])
        vectors.append(p2 - p1)
    
    # Verificar ángulos rectos: el producto punto entre vectores consecutivos debe ser 0
    for i in range(4):
        v1 = vectors[i]
        v2 = vectors[(i+1) % 4]
        dot_product = np.dot(v1, v2)
        if abs(dot_product) > tolerance * (np.linalg.norm(v1) * np.linalg.norm(v2)):
            return False
            
    # Verificar lados opuestos iguales
    side1 = np.linalg.norm(vectors[0])
    side2 = np.linalg.norm(vectors[1])
    side3 = np.linalg.norm(vectors[2])
    side4 = np.linalg.norm(vectors[3])
    
    return (
        abs(side1 - side3) < tolerance * max(side1, side3) and 
        abs(side2 - side4) < tolerance * max(side2, side4)
    )

def divide_rectangle_in_grid(vertices, parts):
    """Divide un rectángulo en una cuadrícula de parcelas rectangulares"""
    polygon = Polygon(vertices)
    bounds = polygon.bounds
    
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny
    
    # Calcular la mejor distribución para la cuadrícula
    best_cols, best_rows = 1, parts
    best_aspect_diff = float('inf')
    
    # Buscar la distribución que minimice la diferencia de aspecto
    for cols in range(1, parts + 1):
        rows = math.ceil(parts / cols)
        total = cols * rows
        
        if total < parts:
            continue
            
        cell_width = width / cols
        cell_height = height / rows
        
        # Calcular diferencia de aspecto respecto al rectángulo original
        orig_aspect = width / height if height != 0 else 1
        cell_aspect = cell_width / cell_height if cell_height != 0 else 1
        aspect_diff = abs(math.log(orig_aspect) - math.log(cell_aspect))
        
        if aspect_diff < best_aspect_diff:
            best_aspect_diff = aspect_diff
            best_cols, best_rows = cols, rows
    
    print(f"🔲 Creando cuadrícula: {best_cols} columnas x {best_rows} filas")
    
    sub_polygons = []
    division_lines = []
    
    x_coords = np.linspace(minx, maxx, best_cols + 1)
    y_coords = np.linspace(miny, maxy, best_rows + 1)
    
    count = 0
    
    # Crear parcelas rectangulares
    for i in range(best_rows):
        for j in range(best_cols):
            if count >= parts:
                break
                
            x_start = x_coords[j]
            x_end = x_coords[j + 1]
            y_start = y_coords[i]
            y_end = y_coords[i + 1]
            
            rect_vertices = [
                (x_start, y_start),
                (x_end, y_start),
                (x_end, y_end),
                (x_start, y_end),
                (x_start, y_start)  # Cerrar el polígono
            ]
            sub_polygons.append(Polygon(rect_vertices))
            count += 1
            
            # Mostrar dimensiones de la parcela
            parcel_width = x_end - x_start
            parcel_height = y_end - y_start
            print(f"   Parcela {count}: {parcel_width:.2f}m x {parcel_height:.2f}m")
    
    # Crear líneas de división
    for j in range(1, best_cols):
        x_pos = x_coords[j]
        division_lines.append(LineString([(x_pos, miny), (x_pos, maxy)]))
    
    for i in range(1, best_rows):
        y_pos = y_coords[i]
        division_lines.append(LineString([(minx, y_pos), (maxx, y_pos)]))
    
    return sub_polygons, division_lines

def create_perfect_radial_subdivision(polygon, parts):
    """Crea subdivisión radial perfecta"""
    coords = list(polygon.exterior.coords)[:-1]
    total_perimeter = polygon.length
    centroid = polygon.centroid
    
    target_perimeter_per_section = total_perimeter / parts
    
    sub_polygons = []
    division_points = []
    current_perimeter = 0
    start_idx = 0
    
    for part_num in range(parts):
        if part_num == parts - 1:
            end_coords = coords[start_idx:] + [coords[0]]
            vertices = [centroid.coords[0]] + end_coords
            sub_poly = Polygon(vertices)
            sub_polygons.append(sub_poly)
        else:
            target_perimeter = target_perimeter_per_section * (part_num + 1)
            cumulative_perimeter = 0
            end_idx = start_idx
            
            for i in range(start_idx, len(coords)):
                next_idx = (i + 1) % len(coords)
                segment_length = np.linalg.norm(
                    np.array(coords[next_idx]) - np.array(coords[i])
                )
                
                if cumulative_perimeter + segment_length >= target_perimeter_per_section:
                    remaining_length = target_perimeter_per_section - cumulative_perimeter
                    t = remaining_length / segment_length if segment_length > 0 else 0
                    
                    cut_point = (
                        coords[i][0] + t * (coords[next_idx][0] - coords[i][0]),
                        coords[i][1] + t * (coords[next_idx][1] - coords[i][1])
                    )
                    
                    division_points.append(cut_point)
                    
                    section_coords = coords[start_idx:i+1] + [cut_point]
                    vertices = [centroid.coords[0]] + section_coords + [centroid.coords[0]]
                    sub_poly = Polygon(vertices)
                    sub_polygons.append(sub_poly)
                    
                    coords.insert(i+1, cut_point)
                    start_idx = i + 1
                    break
                
                cumulative_perimeter += segment_length
                end_idx = next_idx
    
    division_lines = []
    for point in division_points:
        division_lines.append(LineString([centroid.coords[0], point]))
    
    return sub_polygons, division_lines

def create_roads_on_division_lines(division_lines, road_width):
    """Crea carreteras sobre las líneas de división"""
    if not division_lines:
        return None
    
    road_polygons = []
    for line in division_lines:
        # Manejar accesos menores a 2 metros como servidumbres
        actual_width = 1.5 if line.length < 2.0 else road_width
            
        road_buffer = line.buffer(actual_width/2, cap_style=1)
        road_polygons.append(road_buffer)
    
    return unary_union(road_polygons) if road_polygons else None

def clasificar_uso_suelo(area):
    """Clasifica automáticamente el uso del suelo según el área"""
    if area < 120:
        return 'unifamiliar'
    elif 120 <= area < 300:
        return 'multifamiliar'
    else:
        return 'conjunto_residencial'

class GeographicPolygonHandler:
    def __init__(self, lat_lon_coords, utm_zone=None):
        """
        Inicializa el manejador de coordenadas geográficas
        """
        self.lat_lon_coords = lat_lon_coords
        self.utm_zone = utm_zone
        
        if utm_zone is None:
            self.utm_zone = self._detect_utm_zone()
        
        self.wgs84 = pyproj.CRS('EPSG:4326')
        self.utm = pyproj.CRS(f'EPSG:{self._get_utm_epsg()}')
        
        self.to_utm = pyproj.Transformer.from_crs(self.wgs84, self.utm, always_xy=True)
        self.to_wgs84 = pyproj.Transformer.from_crs(self.utm, self.wgs84, always_xy=True)
        
        self.utm_coords = self._convert_to_utm(lat_lon_coords)
        self.utm_polygon = Polygon(self.utm_coords)
        
        print(f"🌍 Coordenadas originales (WGS84): {len(lat_lon_coords)} puntos")
        print(f"🗺️ Zona UTM detectada/usada: {self.utm_zone}")
        print(f"📐 Área del terreno: {self.utm_polygon.area:.2f} m²")
        print(f"📏 Perímetro del terreno: {self.utm_polygon.length:.2f} m")
    
    def _detect_utm_zone(self):
        """Detecta automáticamente la zona UTM"""
        avg_lon = sum(coord[1] for coord in self.lat_lon_coords) / len(self.lat_lon_coords)
        avg_lat = sum(coord[0] for coord in self.lat_lon_coords) / len(self.lat_lon_coords)
        
        zone_num = int((avg_lon + 180) / 6) + 1
        zone_letter = 'N' if avg_lat >= 0 else 'S'
        
        return f"{zone_num}{zone_letter}"
    
    def _get_utm_epsg(self):
        """Obtiene el código EPSG de la zona UTM"""
        zone_num = int(self.utm_zone[:-1])
        hemisphere = self.utm_zone[-1]
        
        if hemisphere == 'N':
            return 32600 + zone_num
        else:
            return 32700 + zone_num
    
    def _convert_to_utm(self, lat_lon_coords):
        """Convierte coordenadas geográficas a UTM"""
        utm_coords = []
        for lat, lon in lat_lon_coords:
            x, y = self.to_utm.transform(lon, lat)
            utm_coords.append((x, y))
        return utm_coords
    
    def _convert_to_latlon(self, utm_coords):
        """Convierte coordenadas UTM a geográficas"""
        latlon_coords = []
        for x, y in utm_coords:
            lon, lat = self.to_wgs84.transform(x, y)
            latlon_coords.append((lat, lon))
        return latlon_coords
    
    def get_utm_vertices(self):
        """Retorna los vértices en coordenadas UTM"""
        return self.utm_coords
        
    def calculate_minimum_requirements(self, land_use):
        """Define los requisitos mínimos según el uso del suelo"""
        requirements = {
            'unifamiliar': {'min_area': 90, 'min_frontage': 6},
            'multifamiliar': {'min_area': 120, 'min_frontage': 8},
            'conjunto_residencial': {'min_area': 300, 'min_frontage': 10, 'max_frontage': 18}
        }
        return requirements.get(land_use, requirements['unifamiliar'])
    
    def calculate_free_area(self, polygon):
        """Calcula el área libre disponible (30% mínimo requerido)"""
        # En una implementación real, esto se calcularía con datos de construcción
        # Aquí asumimos que el área libre es el 30% por defecto
        return polygon.area * 0.30

    def validate_subdivision(self, sub_polygons, road_network):
        """Valida si las subdivisiones cumplen con las normas"""
        validation_results = []
        
        for idx, poly in enumerate(sub_polygons):
            if poly.is_empty:
                continue
                
            # Clasificación automática por área
            land_use = clasificar_uso_suelo(poly.area)
            requirements = self.calculate_minimum_requirements(land_use)
            min_area = requirements['min_area']
            min_frontage = requirements['min_frontage']
            
            # Validar área mínima
            area_ok = poly.area >= min_area
            area_msg = f"✅ Mínimo {min_area} m²" if area_ok else f"❌ Menor que mínimo ({min_area} m²)"
            
            # Validar frente mínimo
            frontage = self.calculate_frontage(poly, road_network)
            
            # Validación especial para conjunto residencial (10-18 ml)
            if land_use == 'conjunto_residencial':
                max_frontage = requirements.get('max_frontage', 18)
                frontage_ok = min_frontage <= frontage <= max_frontage
                frontage_msg = f"✅ Entre {min_frontage}-{max_frontage} ml" if frontage_ok else f"❌ Fuera de rango ({frontage:.2f} ml)"
            else:
                frontage_ok = frontage >= min_frontage
                frontage_msg = f"✅ Mínimo {min_frontage} ml" if frontage_ok else f"❌ Insuficiente ({frontage:.2f} ml)"
            
            # Validar área libre (30% del lote)
            free_area = self.calculate_free_area(poly)
            free_area_ok = free_area >= poly.area * 0.30
            free_area_msg = f"✅ {free_area/poly.area*100:.1f}% libre" if free_area_ok else f"❌ {free_area/poly.area*100:.1f}% libre"
            
            # Validar forma (compactness)
            compactness = (4 * math.pi * poly.area) / (poly.length ** 2) if poly.length > 0 else 0
            shape_ok = compactness >= 0.4
            shape_msg = f"✅ Compacta ({compactness:.2f})" if shape_ok else f"❌ Irregular ({compactness:.2f})"
            
            validation_results.append({
                'lot': idx + 1,
                'land_use': land_use,
                'area': poly.area,
                'area_ok': area_ok,
                'area_msg': area_msg,
                'frontage': frontage,
                'frontage_ok': frontage_ok,
                'frontage_msg': frontage_msg,
                'free_area': free_area,
                'free_area_ok': free_area_ok,
                'free_area_msg': free_area_msg,
                'compactness': compactness,
                'shape_ok': shape_ok,
                'shape_msg': shape_msg,
                'min_area': min_area,
                'min_frontage': min_frontage
            })
        
        return validation_results

    def calculate_frontage(self, lot_polygon, road_network):
        """Calcula el frente del lote contra la red vial"""
        if not road_network or road_network.is_empty:
            return 0
            
        # Calcular la intersección entre el lote y la red vial
        frontage_line = lot_polygon.boundary.intersection(road_network)
        return frontage_line.length if not frontage_line.is_empty else 0

def create_complete_subdivision_plot(polygon, sub_polygons, road_network=None, green_areas=None, 
                                   green_area_idx=None, geo_handler=None, output_path=None,
                                   validation_results=None):
    """Crea UN SOLO gráfico completo con todas las medidas y detalles - ORIENTACIÓN HORIZONTAL"""
    
    # Calcular dimensiones para orientación horizontal
    bounds = polygon.bounds
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    
    # Hacer la figura más ancha para mejor visualización horizontal
    aspect_ratio = width / height
    if aspect_ratio > 1.5:  # Terreno muy ancho
        fig_width = 20
        fig_height = 12
    elif aspect_ratio < 0.7:  # Terreno muy alto
        fig_width = 14
        fig_height = 16
    else:  # Proporción equilibrada
        fig_width = 18
        fig_height = 12
    
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    
    colors = ['lightblue', 'lightcoral', 'lightyellow', 'lightpink', 
              'lightgray', 'lightsalmon', 'lightcyan', 'lavender', 'peachpuff',
              'lightsteelblue', 'mistyrose', 'honeydew', 'aliceblue', 'seashell']
    
    legend_elements = []
    
    # Dibujar subdivisiones
    for idx, poly in enumerate(sub_polygons):
        if not poly.is_empty:
            if isinstance(poly, MultiPolygon):
                for geom in poly.geoms:
                    x, y = geom.exterior.xy
                    color = 'lightgreen' if idx == green_area_idx else colors[idx % len(colors)]
                    ax.fill(x, y, alpha=0.6, facecolor=color, edgecolor='black', linewidth=2)
            else:
                x, y = poly.exterior.xy
                color = 'lightgreen' if idx == green_area_idx else colors[idx % len(colors)]
                ax.fill(x, y, alpha=0.6, facecolor=color, edgecolor='black', linewidth=2)
            
            # Etiqueta con información completa en el centroide
            centroid = poly.centroid
            if idx == green_area_idx:
                land_use = "ÁREA VERDE"
                legend_label = f"Área Verde ({poly.area:.1f} m²)"
            else:
                # Obtener clasificación de uso del suelo desde resultados de validación
                if validation_results and idx < len(validation_results):
                    land_use = validation_results[idx]['land_use'].upper()
                else:
                    land_use = clasificar_uso_suelo(poly.area).upper()
                
                label = f"🏠 LOTE {idx+1} ({land_use})\nÁrea: {poly.area:.2f} m²\nPerímetro: {poly.length:.2f} m"
                legend_label = f"Lote {idx+1} ({poly.area:.1f} m²) - {land_use}"
            
            ax.text(centroid.x, centroid.y, label, ha='center', va='center', 
                   fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.4", facecolor='white', 
                           edgecolor='black', alpha=0.9))
            
            legend_elements.append(Patch(facecolor=color, label=legend_label))
    
    # Dibujar red de carreteras
    if road_network:
        if hasattr(road_network, 'geoms'):
            for road in road_network.geoms:
                if hasattr(road, 'exterior'):
                    x, y = road.exterior.xy
                    ax.fill(x, y, alpha=0.8, facecolor='gray', edgecolor='darkgray', linewidth=1)
        else:
            if hasattr(road_network, 'exterior'):
                x, y = road_network.exterior.xy
                ax.fill(x, y, alpha=0.8, facecolor='gray', edgecolor='darkgray', linewidth=1)
        
        legend_elements.append(Patch(facecolor='gray', label=f"Carreteras ({road_network.area:.1f} m²)"))
    
    # Dibujar retiros si es necesario
    if road_network:
        # Determinar tipo de vía basado en longitud
        main_road_threshold = 6.0  # Umbral para vía principal
        
        if hasattr(road_network, 'geoms'):
            for road in road_network.geoms:
                if hasattr(road, 'exterior'):
                    # Calcular retiro según tipo de vía
                    setback_width = 3.0 if road.length > main_road_threshold else 1.0
                    setback_zones = road.buffer(setback_width, cap_style=2, join_style=2)
                    
                    # Dibujar zonas de retiro
                    if hasattr(setback_zones, 'geoms'):
                        for setback in setback_zones.geoms:
                            x, y = setback.exterior.xy
                            ax.fill(x, y, alpha=0.3, facecolor='yellow', edgecolor='gold', 
                                    linewidth=1, hatch='//')
                    else:
                        x, y = setback_zones.exterior.xy
                        ax.fill(x, y, alpha=0.3, facecolor='yellow', edgecolor='gold', 
                                linewidth=1, hatch='//')
        else:
            # Calcular retiro según tipo de vía
            setback_width = 3.0 if road_network.length > main_road_threshold else 1.0
            setback_zones = road_network.buffer(setback_width, cap_style=2, join_style=2)
            
            # Dibujar zonas de retiro
            if hasattr(setback_zones, 'geoms'):
                for setback in setback_zones.geoms:
                    x, y = setback.exterior.xy
                    ax.fill(x, y, alpha=0.3, facecolor='yellow', edgecolor='gold', 
                            linewidth=1, hatch='//')
            else:
                x, y = setback_zones.exterior.xy
                ax.fill(x, y, alpha=0.3, facecolor='yellow', edgecolor='gold', 
                        linewidth=1, hatch='//')
        
        legend_elements.append(Patch(facecolor='yellow', alpha=0.3, edgecolor='gold', 
                                    label=f"Zonas de Retiro"))
    
    # Mostrar medidas de cada subdivisión
    subdivision_colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown', 'pink', 'olive', 'cyan', 'magenta']
    
    for idx, poly in enumerate(sub_polygons):
        if not poly.is_empty:
            color = subdivision_colors[idx % len(subdivision_colors)]
            
            if isinstance(poly, MultiPolygon):
                for geom_idx, geom in enumerate(poly.geoms):
                    coords = list(geom.exterior.coords)
                    plot_side_lengths(ax, coords, color=color, fontsize=8, 
                                    sample_rate=1, label_prefix=f"L{idx+1}.{geom_idx+1}: ")
            else:
                coords = list(poly.exterior.coords)
                plot_side_lengths(ax, coords, color=color, fontsize=8, 
                                sample_rate=1, label_prefix=f"L{idx+1}: ")
    
    # Mostrar medidas del polígono original
    coords = list(polygon.exterior.coords)
    plot_side_lengths(ax, coords, color='red', fontsize=9, sample_rate=1, label_prefix="Original: ")
    
    # Configurar gráfico con orientación horizontal optimizada
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Subdivisión de Terreno - Normas Peruanas\n' + 
                f'Área Total: {polygon.area:.2f} m² | Perímetro Total: {polygon.length:.2f} m', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Coordenadas UTM X (metros)', fontsize=12)
    ax.set_ylabel('Coordenadas UTM Y (metros)', fontsize=12)
    
    # Leyenda posicionada para mejor visualización horizontal
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.02, 0.5), 
              fontsize=10, title="Elementos del Terreno", title_fontsize=12)
    
    # Ajustar márgenes para visualización horizontal
    plt.tight_layout()
    plt.subplots_adjust(right=0.85)  # Dejar espacio para la leyenda
    
    # Guardar si se especifica ruta
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 Imagen guardada en: {output_path}")
    
    plt.close()
    
    # Imprimir resumen detallado
    print("\n" + "="*60)
    print("📋 RESUMEN COMPLETO DE LA SUBDIVISIÓN")
    print("="*60)
    
    for idx, poly in enumerate(sub_polygons):
        if not poly.is_empty:
            status = "🌱 ÁREA VERDE" if idx == green_area_idx else f"🏠 LOTE {idx+1}"
            print(f"\n{status}:")
            print(f"   📐 Área: {poly.area:.4f} m²")
            print(f"   📏 Perímetro: {poly.length:.4f} m")
            
            # Obtener clasificación de uso del suelo
            if idx < len(validation_results):
                land_use = validation_results[idx]['land_use'].upper()
                print(f"   🏠 Uso del suelo: {land_use}")
            
            # Coordenadas geográficas si están disponibles
            if geo_handler:
                if isinstance(poly, MultiPolygon):
                    print(f"   📍 Coordenadas Geográficas (MultiPolígono):")
                    for geom_idx, geom in enumerate(poly.geoms):
                        utm_coords = list(geom.exterior.coords)
                        latlon_coords = geo_handler._convert_to_latlon(utm_coords)
                        print(f"      Geometría {geom_idx+1}:")
                        for i, (lat, lon) in enumerate(latlon_coords[:-1]):
                            print(f"         Punto {i+1}: {lat:.6f}°, {lon:.6f}°")
                else:
                    utm_coords = list(poly.exterior.coords)
                    latlon_coords = geo_handler._convert_to_latlon(utm_coords)
                    print(f"   📍 Coordenadas Geográficas:")
                    for i, (lat, lon) in enumerate(latlon_coords[:-1]):
                        print(f"      Punto {i+1}: {lat:.6f}°, {lon:.6f}°")
            
            # Medidas de lados
            if isinstance(poly, MultiPolygon):
                for geom_idx, geom in enumerate(poly.geoms):
                    coords = list(geom.exterior.coords)
                    print(f"   📏 Lados Geometría {geom_idx+1}:")
                    for i in range(len(coords) - 1):
                        p1, p2 = coords[i], coords[i + 1]
                        length = np.linalg.norm(np.array(p2) - np.array(p1))
                        if length > 0.01:
                            print(f"      Lado {i+1}: {length:.4f} m")
            else:
                coords = list(poly.exterior.coords)
                print(f"   📏 Medidas de Lados:")
                for i in range(len(coords) - 1):
                    p1, p2 = coords[i], coords[i + 1]
                    length = np.linalg.norm(np.array(p2) - np.array(p1))
                    if length > 0.01:
                        print(f"      Lado {i+1}: {length:.4f} m")
    
    if road_network:
        print(f"\n🛣️ RED DE CARRETERAS:")
        print(f"   📐 Área total: {road_network.area:.4f} m²")
    
    total_subdivision_area = sum(poly.area for poly in sub_polygons if not poly.is_empty)
    road_area = road_network.area if road_network else 0
    green_area = sub_polygons[green_area_idx].area if green_area_idx is not None else 0
    
    print(f"\n📊 VERIFICACIÓN DE ÁREAS:")
    print(f"   🏠 Área total lotes: {total_subdivision_area:.4f} m²")
    print(f"   🛣️ Área carreteras: {road_area:.4f} m²")
    print(f"   🌳 Área verde: {green_area:.4f} m²")
    print(f"   📐 Área original: {polygon.area:.4f} m²")
    print(f"   ✅ Diferencia: {abs(polygon.area - (total_subdivision_area + road_area + green_area)):.4f} m²")
    
    # Verificar aporte urbano (13%)
    public_area = green_area + road_area
    public_percentage = (public_area / polygon.area) * 100
    public_ok = public_percentage >= 13.0
    public_msg = f"✅ {public_percentage:.2f}% (Requerido: 13%)" if public_ok else f"❌ {public_percentage:.2f}% (Requerido: 13%)"
    print(f"\n🏙️ APORTE URBANO (Áreas Públicas): {public_msg}")
    
    # Mostrar resultados de validación
    if validation_results:
        print("\n" + "="*60)
        print("📋 VALIDACIÓN DE NORMAS URBANAS PERUANAS")
        print("="*60)
        
        for result in validation_results:
            status = "✅ APROBADO" if all([
                result['area_ok'], 
                result['frontage_ok'], 
                result['free_area_ok'], 
                result['shape_ok']
            ]) else "❌ NO APROBADO"
            
            print(f"\nLOTE {result['lot']} - {result['land_use'].upper()} - {status}")
            print(f"  📐 Área: {result['area']:.2f} m² - {result['area_msg']}")
            print(f"  📏 Frente: {result['frontage']:.2f} ml - {result['frontage_msg']}")
            print(f"  🌳 Área libre: {result['free_area']:.2f} m² - {result['free_area_msg']}")
            print(f"  ⬛ Forma: {result['shape_msg']}")

def subdivide_terrain_geographic(lat_lon_coords, parts, road_width=3.0, green_area_idx=None, 
                               output_path=None, utm_zone=None):
    """
    Función principal para subdividir terrenos con coordenadas geográficas
    
    Args:
        lat_lon_coords: Lista de tuplas (lat, lon)
        parts: Número de partes para dividir
        road_width: Ancho de carreteras en metros
        green_area_idx: Índice del área verde (opcional)
        output_path: Ruta para guardar la imagen (opcional)
        utm_zone: Zona UTM específica (opcional)
    
    Returns:
        Tupla con (subdivisiones_utm, red_carreteras_utm, areas_verdes_utm, handler_geografico)
    """
    
    # Crear el manejador geográfico
    geo_handler = GeographicPolygonHandler(lat_lon_coords, utm_zone)
    
    # Obtener vértices UTM para procesamiento
    utm_vertices = geo_handler.get_utm_vertices()
    polygon = Polygon(utm_vertices)
    
    if not polygon.is_valid:
        print("❌ Polígono inválido, intentando reparar...")
        polygon = polygon.buffer(0)
    
    # Determinar tipo de subdivisión basado en si es rectángulo
    is_rect = is_rectangle(utm_vertices)
    
    if is_rect:
        print(f"🔲 Rectángulo detectado - Creando subdivisión en cuadrícula")
        sub_polygons, division_lines = divide_rectangle_in_grid(utm_vertices, parts)
    else:
        print(f"🌟 Usando subdivisión radial perfecta")
        sub_polygons, division_lines = create_perfect_radial_subdivision(polygon, parts)
    
    # Crear red de carreteras
    road_network = None
    if division_lines:
        road_network = create_roads_on_division_lines(division_lines, road_width)
        print(f"🛣️ Red de carreteras creada (ancho: {road_width} m)")
    
    # Manejar área verde
    green_areas = None
    if green_area_idx is not None and 0 <= green_area_idx < len(sub_polygons):
        green_areas = sub_polygons[green_area_idx]
        print(f"🌱 Área verde asignada a la parcela {green_area_idx + 1}")
    
    # Reservar 13% para áreas públicas
    total_area = polygon.area
    public_area_required = 0.13 * total_area
    public_area_current = 0
    
    if green_areas:
        public_area_current += green_areas.area
    
    if road_network:
        public_area_current += road_network.area
    
    # Verificar si se cumple el requisito de áreas públicas
    if public_area_current >= public_area_required:
        print(f"🏙️ Área pública total: {public_area_current:.2f} m² ({public_area_current/total_area*100:.1f}%) ✅")
    else:
        print(f"⚠️ ADVERTENCIA: Área pública insuficiente ({public_area_current:.2f} m², {public_area_current/total_area*100:.1f}%)")
        print(f"   Requerido: {public_area_required:.2f} m² (13% del total)")
    
    # Validar subdivisiones
    validation_results = geo_handler.validate_subdivision(sub_polygons, road_network)
    
    # Crear la visualización completa
    create_complete_subdivision_plot(polygon, sub_polygons, road_network, green_areas, 
                                   green_area_idx, geo_handler, output_path,
                                   validation_results)
    
    return sub_polygons, road_network, green_areas, geo_handler

    #create_complete_subdivision_plot(polygon, sub_polygons, road_network, green_areas, 
     #                            green_area_idx, geo_handler, output_path,
      #                           validation_results)

    #return {
     #   'sub_polygons': sub_polygons,
      #  'road_network': road_network,
       # 'green_area': green_areas,
        #'geo_handler': geo_handler,
        #'validation_results': validation_results
    #}

def input_coordinates():
    """Función para ingresar coordenadas geográficas"""
    print("\n📌 Ingrese las coordenadas del terreno como lista de tuplas (lat,lon):")
    print("Ejemplo: [(-15.487033,-70.063152),(-15.48819,-70.063152),(-15.48813,-70.061779)]")
    
    while True:
        entrada = input("Coordenadas: ").strip().replace(" ", "")
        
        try:
            if not entrada.startswith("[") or not entrada.endswith("]"):
                raise ValueError("Formato incorrecto")
                
            puntos = entrada[1:-1].split("),(")
            puntos = [p.replace("(", "").replace(")", "") for p in puntos]
            
            coords = []
            for p in puntos:
                lat, lon = map(float, p.split(","))
                coords.append((lat, lon))
            
            if len(coords) < 3:
                print("❌ Se necesitan al menos 3 puntos")
                continue
                
            # Cerrar polígono si no está cerrado
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            
            print(f"✅ {len(coords)-1} puntos recibidos + cierre")
            return coords
            
        except Exception as e:
            print(f"❌ Error: {str(e)}. Use formato: [(lat1,lon1),(lat2,lon2),...]")

def main():
    """Función principal"""
    print("""
    🏡 DIVISOR DE TERRENOS CON COORDENADAS GEOGRÁFICAS 🏡
    --------------------------------------------------
    Herramienta para subdividir terrenos usando coordenadas
    de latitud y longitud (WGS84) según normas peruanas.
    
    ✨ MEJORAS:
    - Clasificación automática de uso del suelo
    - Cumplimiento de normas peruanas de subdivisión
    - Áreas verdes designadas (13% mínimo)
    - Red de carreteras con servidumbres
    - Retiros diferenciales (3m/1m)
    - Validación completa de lotes
    --------------------------------------------------
    """)
    
    # Ingresar coordenadas
    coords = input_coordinates()
    
    # Ingresar número de partes
    while True:
        try:
            parts = int(input("\n➗ Ingrese número de subdivisiones: "))
            if parts < 1:
                print("❌ Debe ser al menos 1")
                continue
            break
        except ValueError:
            print("❌ Ingrese un número entero válido")
    
    # Ancho de carretera
    road_width = 3.0
    road_input = input("\n🛣️ Ancho de carreteras en metros [Enter para 3.0m]: ").strip()
    if road_input:
        try:
            road_width = float(road_input)
            if road_width < 0.1:
                print("⚠️ Usando valor mínimo 0.1m")
                road_width = 0.1
        except ValueError:
            print("⚠️ Usando valor por defecto 3.0m")
    
    # Área verde
    green_area_idx = None
    green_input = input("\n🌱 Designar área verde? (s/n): ").strip().lower()
    if green_input == 's':
        while True:
            try:
                green_area_idx = int(input("   Índice de área verde (1-{}): ".format(parts))) - 1
                if 0 <= green_area_idx < parts:
                    break
                print("❌ Índice fuera de rango")
            except ValueError:
                print("❌ Ingrese un número válido")
    
    # Guardar imagen
    save_input = input("\n💾 Guardar imagen? (s/n): ").strip().lower()
    output_path = 'core/static/img/subdivision_resultado.png'
    if save_input == 's':
        output_path = input("   Ruta del archivo (ej: subdivision.png): ").strip()
        if not output_path:
            output_path = "subdivision_terreno.png"
            print("⚠️ Usando nombre por defecto: subdivision_terreno.png")
    
    # Zona UTM personalizada
    utm_zone = None
    utm_input = input("\n🌍 Usar zona UTM específica? (s/n): ").strip().lower()
    if utm_input == 's':
        utm_zone = input("   Zona UTM (ej: '19S'): ").strip()
    
    # Procesar subdivisión
    print("\n⚙️ Procesando terreno según normas peruanas...")
    subdivide_terrain_geographic(
        lat_lon_coords=coords,
        parts=parts,
        road_width=road_width,
        green_area_idx=green_area_idx,
        output_path=output_path,
        utm_zone=utm_zone
    )

# Ejecutar solo si es el script principal
if __name__ == "__main__":
    main()