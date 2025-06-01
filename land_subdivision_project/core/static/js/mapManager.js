const MapManager = (() => {
    let map;
    let drawnItems;
    let resultLotsLayer;
    let drawControl;
    let currentPolygonLayer;
    let resultLots = [];

    const initMap = () => {
        map = L.map('map').setView([-15.49, -70.13], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        resultLotsLayer = new L.FeatureGroup();
        map.addLayer(resultLotsLayer);

        setupDrawControl();

        map.on(L.Draw.Event.CREATED, handleDrawCreated);
        map.on(L.Draw.Event.EDITED, handleDrawEdited);

        if (typeof TerrainManager !== 'undefined' && typeof UIManager !== 'undefined') {
            TerrainManager.setCurrentTerreno(null, '', null);
            UIManager.updateStatus(false);
        } else {
            console.warn("TerrainManager o UIManager no definidos al inicializar MapManager.");
        }
    };

    const setupDrawControl = () => {
        if (drawControl) {
            map.removeControl(drawControl);
        }

        drawControl = new L.Control.Draw({
            edit: { 
                featureGroup: drawnItems,
                edit: false
            },
            draw: {
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    metric: true,
                    shapeOptions: {
                        color: '#3388ff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.3
                    }
                },
                polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false
            }
        });
        map.addControl(drawControl);
    };

    const handleDrawCreated = (e) => {
        const layer = e.layer;
        drawnItems.clearLayers();
        drawnItems.addLayer(layer);
        currentPolygonLayer = layer;
    };

    const handleDrawEdited = (e) => {
        e.layers.eachLayer(layer => {
            currentPolygonLayer = layer;
        });
    };

    const clearMap = () => {
        drawnItems.clearLayers();
        resultLotsLayer.clearLayers();
        currentPolygonLayer = null;
        resultLots = [];
    };

    const zoomToLot = (latlngs) => {
        if (!map) return;
        const bounds = L.latLngBounds(latlngs);
        map.fitBounds(bounds);
    };

    const addResultLots = (lots) => {
        if (!resultLotsLayer) return;

        resultLotsLayer.clearLayers();
        lots.forEach(lot => {
            const layer = L.polygon(lot.coordinates, {
                color: '#ff7800',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.3
            }).addTo(resultLotsLayer);
            lot.layer = layer;
        });
        resultLots = lots;
    };

    const getResultLots = () => resultLots;

    return {
        initMap,
        clearMap,
        zoomToLot,
        addResultLots,
        getDrawnItems: () => drawnItems,
        getMap: () => map,
        getResultLotsLayer: () => resultLotsLayer,
        getCurrentPolygonLayer: () => currentPolygonLayer,
        getResultLots: getResultLots,
        setupDrawControl // 👈 disponible para llamar cuando lo necesites
    };
})();
