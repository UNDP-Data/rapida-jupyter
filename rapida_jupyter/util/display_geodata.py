import geopandas as gpd
import ipywidgets as widgets
from IPython.display import display
import leafmap
import rasterio
import fiona


def display_data(gpkg_path=None, gdf=None, raster=None, col=None, cmap='viridis',
                 classification_method='EqualInterval'):
    """
    Displays vector data (from GeoDataFrame or GeoPackage) or raster on a Leafmap map.
    """
    m = leafmap.Map()
    classifiers = ['EqualInterval', 'FisherJenks', 'NaturalBreaks', 'Quantiles']

    layer_selector = None
    columns = []
    gdf_cache = {}

    if gpkg_path:
        layers = fiona.listlayers(gpkg_path)
        layer_selector = widgets.Dropdown(options=layers, description="Layer:")
        gdf = gpd.read_file(gpkg_path, layer=layers[0])
        gdf_cache[layers[0]] = gdf
    elif gdf is not None:
        layers = ['Provided']
        layer_selector = widgets.Dropdown(options=layers, description="Layer:")
        gdf_cache['Provided'] = gdf
    else:
        layers = []
        gdf = None

    if gdf is not None:
        columns = [c for c in gdf.columns if c != 'geometry']

    number_of_classes = 5

    if len(gdf) < number_of_classes:
        number_of_classes = len(gdf)
    visualization_params = {
        'layer_name': 'vector_layer',
        'column': col or (columns[0] if columns else None),
        'cmap': cmap,
        'scheme': classification_method or classifiers[0],
        'add_legend': True,
        'info_mode': None,
        'raster_min': None,
        'raster_max': None,
        'k': number_of_classes,
    }

    column_selector = widgets.Dropdown(options=columns, description='Column:', value=visualization_params['column'])
    colormap_selector = widgets.Dropdown(options=leafmap.list_palettes(), description='Colormap:', value=cmap)
    classification_selector = widgets.Dropdown(options=classifiers, description='Classification:',
                                               value=classification_method)

    warning_label = widgets.Label(
        value='')

    def update_map():
        """Updates the map with the current vector or raster layer."""
        if 'vector_layer' in [ly.name for ly in m.layers]:
            m.remove(m.find_layer('vector_layer'))
        if 'raster_layer' in [ly.name for ly in m.layers]:
            m.remove(m.find_layer('raster_layer'))
        try:
            m.remove(m.legend_control)
        except:
            pass

        warning_label.value = ''

        if gdf is not None and visualization_params['column']:
            values = gdf[visualization_params['column']].dropna()
            unique_values = values.unique()

            if len(unique_values) < 2:
                warning_label.value = (
                    f"⚠️ Warning: Not enough unique values in '{visualization_params['column']}' to classify. "
                    "Showing unclassified layer."
                )
                # Display basic GeoDataFrame without classification
                m.add_gdf(gdf, layer_name='vector_layer', info_mode=visualization_params['info_mode'])
            else:
                try:
                    m.add_data(gdf, **visualization_params)
                except ValueError as e:
                    warning_label.value = f"⚠️ Error applying classification: {e}"
                    m.add_gdf(gdf, layer_name='vector_layer', info_mode=visualization_params['info_mode'])  # fallback

        if raster:
            with rasterio.open(raster) as src:
                no_data = src.nodata
                m.add_raster(
                    source=raster,
                    colormap=visualization_params['cmap'],
                    layer_name='raster_layer',
                    nodata=no_data,
                    vmax=visualization_params['raster_max'],
                    vmin=visualization_params['raster_min'],
                )

    def on_column_change(change):
        visualization_params['column'] = change['new']
        is_numeric = gdf[visualization_params['column']].apply(lambda x: isinstance(x, (int, float))).all()
        classification_selector.layout.visibility = 'visible' if is_numeric else 'hidden'
        update_map()

    def on_classification_change(change):
        visualization_params['scheme'] = change['new']
        update_map()

    def on_colormap_change(change):
        visualization_params['cmap'] = change['new']
        update_map()

    def on_layer_change(change):
        nonlocal gdf, columns
        selected_layer = change['new']
        gdf_cache.clear()
        gdf = gpd.read_file(gpkg_path, layer=selected_layer)
        gdf_cache[selected_layer] = gdf
        columns = [c for c in gdf.columns if c != 'geometry']
        new_col = columns[0] if columns else None
        visualization_params['column'] = new_col
        column_selector.options = columns
        column_selector.value = new_col
        if new_col and not gdf[new_col].apply(lambda x: isinstance(x, (int, float))).all():
            classification_selector.layout.visibility = 'hidden'
        else:
            classification_selector.layout.visibility = 'visible'
        update_map()

    column_selector.observe(on_column_change, names='value')
    classification_selector.observe(on_classification_change, names='value')
    colormap_selector.observe(on_colormap_change, names='value')

    if layer_selector:
        layer_selector.observe(on_layer_change, names='value')

    if gdf is not None:
        centroid = gdf.to_crs(4326).dissolve().geometry.centroid.iloc[0]
        m.set_center(lat=centroid.y, lon=centroid.x, zoom=10)
        update_map()

    if raster:
        with rasterio.open(raster) as src:
            no_data = src.nodata
            visualization_params['raster_min'] = src.read(1).min()
            visualization_params['raster_max'] = src.read(1).max()
            min_max_slider = widgets.FloatRangeSlider(
                min=visualization_params['raster_min'],
                max=visualization_params['raster_max'])
            min_max_label = widgets.Label(value='Min/Max:')

            def on_values_change(change):
                visualization_params['raster_min'] = change['new'][0]
                visualization_params['raster_max'] = change['new'][1]
                update_map()

            min_max_slider.observe(on_values_change, names='value')
            controls = widgets.HBox([min_max_label, min_max_slider, colormap_selector])
    else:
        controls = widgets.HBox([column_selector, colormap_selector, classification_selector])
        if layer_selector:
            controls = widgets.HBox([layer_selector, controls])

    ui = widgets.VBox([controls, warning_label])
    display(ui, m)