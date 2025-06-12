import json
import math
import random
import numpy as np
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, Point, MultiPoint, GeometryCollection
from shapely.ops import split, unary_union, voronoi_diagram
from shapely.validation import explain_validity
from shapely.errors import TopologicalError
from pyproj import Transformer
import logging
from shapely.ops import transform

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

# --- Funciones de Proyección y Conversión ---

def get_utm_zone_from_lon_lat(longitude, latitude):
    """Calcula la zona UTM y el hemisferio para un punto dado."""
    zone = int(math.floor((longitude + 180) / 6) + 1)
    hemisphere = 'north' if latitude >= 0 else 'south'
    return zone, hemisphere

def get_epsg_code_from_utm_zone(zone, hemisphere):
    """Devuelve el código EPSG para una zona UTM dada."""
    if hemisphere == 'north':
        return 32600 + zone
    else:
        return 32700 + zone

def convert_geojson_to_utm(geojson_data_str):
    """
    Convierte un GeoJSON (WGS84 lat/lon) a un polígono Shapely en coordenadas UTM.
    Retorna (utm_polygon, utm_epsg_code) o (None, error_message).
    """
    try:
        geojson_data = json.loads(geojson_data_str)

        polygon_geom_data = None
        if geojson_data.get("type") == "FeatureCollection" and geojson_data.get("features"):
            # Intenta obtener la primera geometría válida de la colección de features
            for feature in geojson_data["features"]:
                if feature.get("geometry") and feature["geometry"]["type"] in ["Polygon", "MultiPolygon"]:
                    polygon_geom_data = feature["geometry"]
                    break
        elif geojson_data.get("type") == "Feature":
            if geojson_data.get("geometry") and geojson_data["geometry"]["type"] in ["Polygon", "MultiPolygon"]:
                polygon_geom_data = geojson_data.get("geometry")
        elif geojson_data.get("type") in ["Polygon", "MultiPolygon"]:
            polygon_geom_data = geojson_data

        if not polygon_geom_data:
            logging.error("Estructura GeoJSON inválida o geometría de polígono no encontrada.")
            return None, "Estructura GeoJSON inválida o geometría de polígono no encontrada."

        original_geometry = shape(polygon_geom_data)

        # Si es un MultiPolygon, toma el polígono más grande para la conversión inicial
        if isinstance(original_geometry, MultiPolygon):
            original_polygon = max(original_geometry.geoms, key=lambda p: p.area)
            logging.warning("GeoJSON de entrada es un MultiPolygon. Se utilizará el polígono más grande para la conversión.")
        elif isinstance(original_geometry, Polygon):
            original_polygon = original_geometry
        else:
            logging.error(f"Geometría GeoJSON de tipo inesperado: {original_geometry.geom_type}. Se esperaba Polygon o MultiPolygon.")
            return None, "Geometría GeoJSON de tipo no soportado (se esperaba Polygon o MultiPolygon)."

        if not original_polygon.is_valid:
            logging.warning(f"Polígono original GeoJSON no válido: {explain_validity(original_polygon)}, intentando reparar con buffer(0).")
            original_polygon = original_polygon.buffer(0)
            if not original_polygon.is_valid:
                logging.error(f"Polígono original aún inválido después de buffer(0): {explain_validity(original_polygon)}.")
                return None, "El polígono original es inválido incluso después de la reparación."

        centroid = original_polygon.centroid
        longitude, latitude = centroid.x, centroid.y

        utm_zone, hemisphere = get_utm_zone_from_lon_lat(longitude, latitude)
        utm_epsg_code = get_epsg_code_from_utm_zone(utm_zone, hemisphere)

        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg_code}", always_xy=True)

        utm_polygon = transform(transformer.transform, original_polygon)

        if not utm_polygon.is_valid:
            logging.warning(f"Polígono UTM no válido después de la transformación: {explain_validity(utm_polygon)}, intentando reparar.")
            utm_polygon = utm_polygon.buffer(0)
            if not utm_polygon.is_valid:
                logging.error(f"Polígono UTM aún inválido después de la reparación post-transformación: {explain_validity(utm_polygon)}.")
                return None, "Polígono UTM inválido después de la transformación y reparación."

        logging.info(f"Convertido a UTM EPSG:{utm_epsg_code}. Área: {utm_polygon.area:.2f} m²")
        return utm_polygon, utm_epsg_code

    except json.JSONDecodeError:
        logging.error("Entrada GeoJSON no es un JSON válido.")
        return None, "Entrada GeoJSON no es un JSON válido."
    except Exception as e:
        logging.error(f"Fallo general en la conversión a UTM: {str(e)}", exc_info=True)
        return None, f"Fallo en la conversión a UTM: {str(e)}"

def convert_utm_polygon_to_geojson(utm_polygon, utm_crs_epsg, target_crs_epsg="EPSG:4326"):
    """
    Convierte un polígono Shapely en coordenadas UTM de nuevo a GeoJSON (WGS84 lat/lon).
    """
    try:
        transformer = Transformer.from_crs(f"EPSG:{utm_crs_epsg}", target_crs_epsg, always_xy=True)
        geographic_polygon = transform(transformer.transform, utm_polygon)  # ✅ CORREGIDO

        if not geographic_polygon.is_valid:
            logging.warning(f"Polígono geográfico no válido después de la transformación inversa: {explain_validity(geographic_polygon)}, intentando reparar.")
            geographic_polygon = geographic_polygon.buffer(0)
            if not geographic_polygon.is_valid:
                logging.error(f"Polígono geográfico aún inválido después de la reparación: {explain_validity(geographic_polygon)}.")
                return None

        return json.loads(json.dumps(geographic_polygon.__geo_interface__))
    except Exception as e:
        logging.error(f"Fallo en la reconversión de UTM a GeoJSON: {str(e)}", exc_info=True)
        return None

# --- Algoritmos de Subdivisión ---

def simple_subdivision_by_line(geojson_polygon_str, num_lots):
    """
    Subdivide un polígono principal en 'num_lots' lotes de forma aproximada
    mediante divisiones horizontales (paralelas al eje X).
    Retorna una FeatureCollection GeoJSON o un diccionario con "error".
    """
    logging.info(f"Iniciando subdivisión por línea para {num_lots} lotes.")
    try:
        utm_polygon, utm_epsg_code = convert_geojson_to_utm(geojson_polygon_str)
        if utm_polygon is None:
            return {"error": utm_epsg_code}

        # Asegurarse de que sea un polígono simple para el método de línea
        if isinstance(utm_polygon, MultiPolygon):
            # Tomar el polígono más grande
            utm_polygon = max(utm_polygon.geoms, key=lambda p: p.area)
            logging.warning("simple_subdivision_by_line: MultiPolygon de entrada, tomando el polígono más grande para subdividir.")

        if not isinstance(utm_polygon, Polygon):
            return {"error": "simple_subdivision_by_line: La subdivisión por línea requiere un solo polígono de entrada."}

        minx, miny, maxx, maxy = utm_polygon.bounds
        height = maxy - miny

        if height < 1.0: # Umbral mínimo de altura, ej. 1 metro
            logging.warning(f"Polígono con altura despreciable ({height:.2f}m), no se puede subdividir por líneas horizontales.")
            return {"error": "El polígono tiene una altura despreciable, no se puede subdividir por líneas horizontales."}

        # Calcular el espaciado para las líneas horizontales
        line_spacing = height / num_lots

        subdivided_lots_utm = []
        current_cut_polygons = [utm_polygon] # Empezamos con el polígono completo

        for i in range(num_lots - 1):
            next_cut_polygons = []
            cut_y = miny + (i + 1) * line_spacing
            
            # Asegurarse de que la línea de corte abarque todo el ancho del polígono
            # Añadir un margen fuera de los límites del polígono para asegurar el corte
            cut_line = LineString([(minx - 1000, cut_y), (maxx + 1000, cut_y)])

            for poly_to_cut in current_cut_polygons:
                if not poly_to_cut.is_valid:
                    poly_to_cut = poly_to_cut.buffer(0) # Intentar reparar si es necesario
                    if not poly_to_cut.is_valid:
                        logging.warning(f"Polígono inválido antes de cortar en iteración {i}, no se puede procesar.")
                        subdivided_lots_utm.append(poly_to_cut) # Añadir como está si no se puede reparar
                        continue
                
                try:
                    # Intentar cortar el polígono
                    split_result = split(poly_to_cut, cut_line)

                    # Filtrar las geometrías resultantes
                    valid_parts = []
                    for part in split_result.geoms:
                        if isinstance(part, (Polygon, MultiPolygon)):
                            if part.is_valid and part.area > 0.1: # Umbral de área 0.1 m²
                                if isinstance(part, Polygon):
                                    valid_parts.append(part)
                                else: # MultiPolygon
                                    for sub_part in part.geoms:
                                        if isinstance(sub_part, Polygon) and sub_part.is_valid and sub_part.area > 0.1:
                                            valid_parts.append(sub_part)
                        elif isinstance(part, GeometryCollection):
                            for g in part.geoms:
                                if isinstance(g, Polygon) and g.is_valid and g.area > 0.1:
                                    valid_parts.append(g)
                    
                    if len(valid_parts) == 2:
                        # Si se cortó en dos, añadir la parte inferior a los lotes finales
                        # y la parte superior para futuras subdivisiones
                        # (asumiendo que las líneas se mueven de abajo hacia arriba)
                        # Ordenamos por coordenada Y mínima para identificar la parte inferior
                        valid_parts.sort(key=lambda p: p.bounds[1]) 
                        subdivided_lots_utm.append(valid_parts[0]) # La parte inferior es un lote final
                        next_cut_polygons.append(valid_parts[1]) # La parte superior se subdividirá en la siguiente iteración
                    elif len(valid_parts) == 1:
                        # Si solo hay una parte, la línea no cortó efectivamente el polígono,
                        # o era una parte muy pequeña que fue filtrada. Re-añadir para que se procese de nuevo.
                        logging.warning(f"Corte en iteración {i} resultó en una sola parte válida. Re-añadiendo el polígono para el siguiente intento o como lote final si es el último corte.")
                        next_cut_polygons.append(poly_to_cut)
                    else:
                        # Número inesperado de partes, añadir todas las válidas que queden a los lotes.
                        logging.warning(f"Corte en iteración {i} resultó en {len(valid_parts)} partes (esperado 2). Añadiendo todas las partes válidas como lotes finales.")
                        subdivided_lots_utm.extend(valid_parts)

                except TopologicalError as e:
                    logging.error(f"TopologicalError durante el corte en iteración {i}: {e}. Polígono no subdividido.")
                    subdivided_lots_utm.append(poly_to_cut) # Añadir el polígono sin cortar si hay error
                except Exception as e:
                    logging.error(f"Error durante el corte en iteración {i}: {e}. Polígono no subdividido.", exc_info=True)
                    subdivided_lots_utm.append(poly_to_cut) # Añadir el polígono sin cortar si hay error
            
            current_cut_polygons = next_cut_polygons # Los polígonos restantes para cortar en la siguiente iteración
        
        # Añadir los últimos polígonos que no fueron cortados o que son el último lote
        subdivided_lots_utm.extend(current_cut_polygons)

        # Consolidar lotes y filtrar finales, asegurando que sean Polygons
        final_lots_utm = []
        for lot_utm in subdivided_lots_utm:
            if isinstance(lot_utm, MultiPolygon):
                for single_lot in lot_utm.geoms:
                    if isinstance(single_lot, Polygon) and single_lot.is_valid and single_lot.area > 0.1:
                        final_lots_utm.append(single_lot)
            elif isinstance(lot_utm, Polygon) and lot_utm.is_valid and lot_utm.area > 0.1:
                final_lots_utm.append(lot_utm)

        # Si se generaron más lotes de los solicitados, tomar los 'num_lots' más grandes
        if len(final_lots_utm) > num_lots:
            final_lots_utm = sorted(final_lots_utm, key=lambda p: p.area, reverse=True)[:num_lots]
            logging.info(f"Reducido a {len(final_lots_utm)} lotes por truncamiento.")
        elif len(final_lots_utm) < num_lots and len(final_lots_utm) > 0:
            logging.warning(f"Solo se generaron {len(final_lots_utm)} lotes, se solicitaron {num_lots}.")
        elif not final_lots_utm:
            logging.error("No se generaron lotes válidos con el método de línea.")
            return {"error": "No se pudieron generar lotes válidos con el algoritmo de línea."}
            
        geojson_features = []
        for i, lot_utm in enumerate(final_lots_utm):
            lot_geojson = convert_utm_polygon_to_geojson(lot_utm, utm_epsg_code)
            if lot_geojson:
                geojson_features.append({
                    "type": "Feature",
                    "geometry": lot_geojson,
                    "properties": {
                        "lot_number": i + 1,
                        "area_sqm": lot_utm.area
                    }
                })
            else:
                logging.warning(f"No se pudo convertir el lote UTM {i+1} a GeoJSON.")

        logging.info(f"Lotes GeoJSON convertidos: {len(geojson_features)}")
        return {"type": "FeatureCollection", "features": geojson_features}

    except Exception as e:
        logging.error(f"Fallo general en simple_subdivision_by_line: {str(e)}", exc_info=True)
        return {"error": f"Fallo en la subdivisión por línea: {str(e)}"}

def subdivide_by_voronoi(geojson_polygon_str, num_lots):
    """
    Subdivide un polígono usando el algoritmo de Voronoi.
    Retorna una FeatureCollection GeoJSON o un diccionario con "error".
    """
    logging.info(f"Iniciando subdivisión por Voronoi para {num_lots} lotes.")
    try:
        utm_polygon, utm_epsg_code = convert_geojson_to_utm(geojson_polygon_str)
        if utm_polygon is None:
            return {"error": utm_epsg_code}

        if isinstance(utm_polygon, MultiPolygon):
            utm_polygon = max(utm_polygon.geoms, key=lambda p: p.area)
            logging.warning("subdivide_by_voronoi: MultiPolygon de entrada, tomando el polígono más grande para subdividir.")
        
        if not utm_polygon.is_valid:
            logging.warning(f"Polígono UTM de entrada no válido: {explain_validity(utm_polygon)}, intentando reparar.")
            utm_polygon = utm_polygon.buffer(0)
            if not utm_polygon.is_valid:
                return {"error": "Polígono de entrada inválido o no reparable para subdivisión por Voronoi."}

        minx, miny, maxx, maxy = utm_polygon.bounds

        points = []
        # Intentar generar puntos dentro del polígono. 
        # Generar un número significativamente mayor de puntos para tener más opciones
        # y luego seleccionar num_lots al azar para asegurar que estén bien distribuidos.
        max_attempts = num_lots * 100 # Más intentos para polígonos complejos o muy estrechos
        
        for _ in range(max_attempts):
            x = random.uniform(minx, maxx)
            y = random.uniform(miny, maxy)
            p = Point(x, y)
            if utm_polygon.contains(p):
                points.append(p)
            if len(points) >= num_lots * 2: # Si ya tenemos el doble de puntos que necesitamos, podemos parar antes
                break

        if len(points) < num_lots:
            logging.warning(f"Solo se pudieron generar {len(points)} puntos semilla válidos, se necesitan {num_lots}. Ajustando num_lots.")
            if not points:
                return {"error": "No se pudieron generar puntos semilla para Voronoi dentro del polígono (quizás el polígono es muy pequeño/estrecho o muy complejo)."}
            num_lots = len(points)

        # Seleccionar `num_lots` puntos al azar para asegurar una distribución más aleatoria y no sesgada
        # por el orden de generación si se generaron muchos.
        voronoi_seeds = MultiPoint(random.sample(points, k=num_lots))

        if not voronoi_seeds.geoms:
            return {"error": "No hay puntos semilla válidos para crear el diagrama de Voronoi."}

        try:
            # Usar el bounding box del polígono UTM para el envelope del diagrama de Voronoi.
            diagram = voronoi_diagram(voronoi_seeds, envelope=utm_polygon.envelope)
        except Exception as e:
            logging.error(f"Fallo al crear el diagrama de Voronoi: {e}", exc_info=True)
            return {"error": f"Fallo al crear el diagrama de Voronoi: {str(e)}"}

        final_lots_utm = []
        for geom in diagram.geoms:
            if utm_polygon.intersects(geom):
                lot_utm = utm_polygon.intersection(geom)

                if isinstance(lot_utm, (Polygon, MultiPolygon)):
                    if lot_utm.is_valid and lot_utm.area > 0.1:
                        if isinstance(lot_utm, Polygon):
                            final_lots_utm.append(lot_utm)
                        else: # MultiPolygon
                            for single_poly in lot_utm.geoms:
                                if isinstance(single_poly, Polygon) and single_poly.is_valid and single_poly.area > 0.1:
                                    final_lots_utm.append(single_poly)
                elif isinstance(lot_utm, GeometryCollection):
                    for g in lot_utm.geoms:
                        if isinstance(g, Polygon) and g.is_valid and g.area > 0.1:
                            final_lots_utm.append(g)

        logging.info(f"Lotes UTM generados antes de selección final: {len(final_lots_utm)}")

        if not final_lots_utm:
            logging.error("No se generaron lotes válidos con el algoritmo de Voronoi.")
            return {"error": "No se pudieron generar lotes válidos con el algoritmo de Voronoi."}

        # Si se generaron más lotes de los solicitados, tomar los 'num_lots' más grandes
        if len(final_lots_utm) > num_lots:
            final_lots_utm = sorted(final_lots_utm, key=lambda p: p.area, reverse=True)[:num_lots]
            logging.info(f"Reducido a {len(final_lots_utm)} lotes por truncamiento.")
        elif len(final_lots_utm) < num_lots and len(final_lots_utm) > 0:
            logging.warning(f"Solo se generaron {len(final_lots_utm)} lotes, se solicitaron {num_lots}.")

        geojson_features = []
        for i, lot_utm in enumerate(final_lots_utm):
            lot_geojson = convert_utm_polygon_to_geojson(lot_utm, utm_epsg_code)
            if lot_geojson:
                geojson_features.append({
                    "type": "Feature",
                    "geometry": lot_geojson,
                    "properties": {
                        "lot_number": i + 1,
                        "area_sqm": lot_utm.area
                    }
                })
            else:
                logging.warning(f"No se pudo convertir el lote UTM {i+1} de Voronoi a GeoJSON.")

        logging.info(f"Lotes GeoJSON convertidos: {len(geojson_features)}")
        return {"type": "FeatureCollection", "features": geojson_features}

    except Exception as e:
        logging.error(f"Fallo general en subdivide_by_voronoi: {str(e)}", exc_info=True)
        return {"error": f"Fallo en la subdivisión por Voronoi: {str(e)}"}

def subdivide_by_quadtree(geojson_polygon_str, num_lots):
    """
    Subdivide un polígono usando el algoritmo de Quadtree.
    Retorna una FeatureCollection GeoJSON o un diccionario con "error".
    """
    logging.info(f"Iniciando subdivisión por Quadtree para {num_lots} lotes.")
    try:
        utm_polygon, utm_epsg_code = convert_geojson_to_utm(geojson_polygon_str)
        if utm_polygon is None:
            return {"error": utm_epsg_code}

        if isinstance(utm_polygon, MultiPolygon):
            utm_polygon = max(utm_polygon.geoms, key=lambda p: p.area)
            logging.warning("subdivide_by_quadtree: MultiPolygon de entrada, tomando el polígono más grande para subdividir.")

        if not utm_polygon.is_valid:
            logging.warning(f"Polígono UTM de entrada no válido: {explain_validity(utm_polygon)}, intentando reparar.")
            utm_polygon = utm_polygon.buffer(0)
            if not utm_polygon.is_valid:
                return {"error": "Polígono de entrada inválido o no reparable para subdivisión por Quadtree."}

        class QuadtreeNode:
            def __init__(self, bbox, depth):
                self.bbox = bbox # (minx, miny, maxx, maxy)
                self.depth = depth
                self.children = []
                self.polygon_intersection = None

            def subdivide(self, original_polygon, max_depth, min_lot_area_threshold):
                minx, miny, maxx, maxy = self.bbox
                current_quad_polygon = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)])

                # La intersección puede generar múltiples polígonos, o geometrías no poligonales
                intersection = original_polygon.intersection(current_quad_polygon)
                
                # Filtrar resultados válidos (Polygon o MultiPolygon)
                valid_intersections = []
                if isinstance(intersection, (Polygon, MultiPolygon)):
                    if intersection.is_valid and intersection.area > min_lot_area_threshold / 2: # Umbral más bajo para partes intermedias
                        if isinstance(intersection, Polygon):
                            valid_intersections.append(intersection)
                        else: # MultiPolygon
                            for p in intersection.geoms:
                                if isinstance(p, Polygon) and p.is_valid and p.area > min_lot_area_threshold / 2:
                                    valid_intersections.append(p)
                elif isinstance(intersection, GeometryCollection):
                    for g in intersection.geoms:
                        if isinstance(g, Polygon) and g.is_valid and g.area > min_lot_area_threshold / 2:
                            valid_intersections.append(g)

                if not valid_intersections:
                    return [] # El cuadrante no se intersecta o las intersecciones son inválidas/demasiado pequeñas

                # Combinar todas las partes válidas en un solo MultiPolygon o Polygon para esta rama del Quadtree
                self.polygon_intersection = unary_union(valid_intersections)
                
                # Asegurar que el resultado de unary_union sea un polígono o multipolígono válido
                if not isinstance(self.polygon_intersection, (Polygon, MultiPolygon)):
                    return [] # No se pudo formar un polígono válido después de la unión
                if not self.polygon_intersection.is_valid:
                    self.polygon_intersection = self.polygon_intersection.buffer(0)
                    if not self.polygon_intersection.is_valid:
                        logging.warning(f"Intersección de cuadrante inválida después de buffer(0): {explain_validity(self.polygon_intersection)}")
                        return []

                # Criterio de parada para la recursión:
                # 1. Si alcanza la profundidad máxima.
                # 2. Si el área del polígono de intersección es menor que un umbral.
                # 3. Si la intersección ya es muy simple (ej. un solo polígono pequeño)
                if self.depth >= max_depth or \
                   self.polygon_intersection.area < min_lot_area_threshold * 1.5 or \
                   (isinstance(self.polygon_intersection, Polygon) and self.polygon_intersection.area > 0.1 and self.polygon_intersection.area < min_lot_area_threshold * 2): # Si es un solo polígono y ya es pequeño, no subdividir más

                    if isinstance(self.polygon_intersection, MultiPolygon):
                        return [p for p in self.polygon_intersection.geoms if isinstance(p, Polygon) and p.is_valid and p.area > min_lot_area_threshold]
                    elif isinstance(self.polygon_intersection, Polygon):
                        return [self.polygon_intersection]
                    else:
                        return []

                midx = (minx + maxx) / 2
                midy = (miny + maxy) / 2

                children_bboxes = [
                    (minx, midy, midx, maxy), # Top-Left
                    (midx, midy, maxx, maxy), # Top-Right
                    (minx, miny, midx, midy), # Bottom-Left
                    (midx, miny, maxx, midy)  # Bottom-Right
                ]

                lots_from_children = []
                for child_bbox in children_bboxes:
                    # Solo subdivide si el cuadrante hijo tiene una intersección potencial con el polígono original
                    child_quad = Polygon([(child_bbox[0], child_bbox[1]), (child_bbox[2], child_bbox[1]), 
                                          (child_bbox[2], child_bbox[3]), (child_bbox[0], child_bbox[3]), (child_bbox[0], child_bbox[1])])
                    if original_polygon.intersects(child_quad):
                        child_node = QuadtreeNode(child_bbox, self.depth + 1)
                        lots_from_children.extend(child_node.subdivide(original_polygon, max_depth, min_lot_area_threshold))
                
                # Si los hijos no generaron lotes o la subdivisión no fue efectiva,
                # y el padre es un polígono válido y de tamaño aceptable, usar el lote del padre como lote final.
                if not lots_from_children and isinstance(self.polygon_intersection, Polygon) and self.polygon_intersection.area > min_lot_area_threshold:
                    return [self.polygon_intersection]

                return lots_from_children

        area_terreno_total = utm_polygon.area
        
        # Determinar max_depth: un valor más alto permite más divisiones y potencialmente más lotes.
        # Estimación: Cada nivel de profundidad puede generar hasta 4 lotes.
        # Ajustamos el +2 para dar margen de granularidad
        if num_lots <= 1:
            max_depth_calc = 0
        else:
            max_depth_calc = math.ceil(math.log(num_lots, 4)) + 2
        
        # Umbral de área mínima para un lote final (en m²)
        # Si se piden muchos lotes, el área promedio será pequeña.
        # Aseguramos un mínimo absoluto para evitar "astillas" insignificantes.
        min_area_for_lot = area_terreno_total / (num_lots * 8) if num_lots > 0 else 100 # Dividir por 8 para permitir lotes más pequeños inicialmente
        min_area_for_lot = max(min_area_for_lot, 10) # Asegurar un mínimo absoluto de 10 m2

        logging.info(f"Quadtree: max_depth_calc={max_depth_calc}, min_area_for_lot={min_area_for_lot:.2f} m²")

        root_node = QuadtreeNode(utm_polygon.bounds, 0)
        potential_lots_utm = root_node.subdivide(utm_polygon, max_depth_calc, min_area_for_lot)

        final_lots_utm = [
            lot for lot in potential_lots_utm 
            if isinstance(lot, Polygon) and lot.is_valid and lot.area >= min_area_for_lot # Re-aplicar umbral de área final
        ]

        logging.info(f"Quadtree: Lotes UTM generados antes de selección final: {len(final_lots_utm)}")

        if not final_lots_utm:
            logging.error("No se generaron lotes válidos con el algoritmo de Quadtree.")
            return {"error": "No se pudieron generar lotes válidos con el algoritmo de Quadtree."}

        if len(final_lots_utm) > num_lots:
            final_lots_utm = sorted(final_lots_utm, key=lambda p: p.area, reverse=True)[:num_lots]
            logging.info(f"Quadtree: Reducido a {len(final_lots_utm)} lotes por truncamiento.")
        elif len(final_lots_utm) < num_lots and len(final_lots_utm) > 0:
            logging.warning(f"Quadtree: Solo se generaron {len(final_lots_utm)} lotes, se solicitaron {num_lots}.")

        geojson_features = []
        for i, lot_utm in enumerate(final_lots_utm):
            lot_geojson = convert_utm_polygon_to_geojson(lot_utm, utm_epsg_code)
            if lot_geojson:
                geojson_features.append({
                    "type": "Feature",
                    "geometry": lot_geojson,
                    "properties": {
                        "lot_number": i + 1,
                        "area_sqm": lot_utm.area
                    }
                })
            else:
                logging.warning(f"No se pudo convertir el lote UTM {i+1} de Quadtree a GeoJSON.")

        logging.info(f"Quadtree: Lotes GeoJSON convertidos: {len(geojson_features)}")
        return {"type": "FeatureCollection", "features": geojson_features}

    except Exception as e:
        logging.error(f"Fallo general en subdivide_by_quadtree: {str(e)}", exc_info=True)
        return {"error": f"Fallo en la subdivisión por Quadtree: {str(e)}"}

# --- Función de selección de algoritmo ---

def get_subdivision_algorithm(method_name):
    """
    Retorna la función del algoritmo de subdivisión según el nombre.
    """
    if method_name == 'line':
        return simple_subdivision_by_line
    elif method_name == 'voronoi':
        return subdivide_by_voronoi
    elif method_name == 'quadtree':
        return subdivide_by_quadtree
    else:
        logging.error(f"Método de subdivisión no válido: {method_name}")
        return None