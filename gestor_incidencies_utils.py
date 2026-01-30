from qgis.core import Qgis, QgsVectorLayerCache, QgsProviderRegistry, QgsProject, QgsExpressionContextUtils, QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgisInterface

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QLabel, QGridLayout, QPushButton

import os.path
import json


DEFAULT_LABEL_ELEMENTS = "Elements: "


class gestor_incidencies_utils:

	def __init__(self, parent, plugin_dir):

		self.parent = parent
		self.plugin_dir = plugin_dir


	def read_config(self):
		""" read params from config.json """

		param = {}

		try:
			with open(os.path.join(self.plugin_dir, "config.json")) as f:
				config = json.load(f)
	
				param["db"] = {
					"service": config["db"]["service"],
					#"database": config["db"]["database"],
					#"schema": config["db"]["schema"]
				}
				param["layers"] = config["layers"]

		except Exception as e:
			print(e)

		return param


	def get_all_selected_features(self):
		""" Gathers all selected features across every vector layer in the project. Returns a dictionary mapping layer names to their list of selected features. """

		layers = QgsProject.instance().mapLayers().values()
		selection_dict = {}

		for layer in layers:
			if isinstance(layer, QgsVectorLayer):
				selection = layer.selectedFeatures()
				if selection:
					selection_dict[layer.name()] = selection
		
		return selection_dict


	def check_selection_validity(self, selection_dict, param):
		""" Checks if the layers containing selected features are within the allowed list. """

		selected_layer_names = set(selection_dict.keys())
		selectable_layers = set(param["layers"].keys())
		allowed_set = set(selectable_layers)
		
		invalid_layers = selected_layer_names - allowed_set
		
		if invalid_layers:
			self.iface.messageBar().pushMessage("Warning", f"Features selected in unauthorized layers: {', '.join(invalid_layers)}", level=Qgis.Warning, duration=5)
			return False

		return True


	def show_resume_groupbox_old(self, selection_dict):
		"""
		Formats the selection data and updates the UI widget.
		
		:param selection_dict: The dict from get_all_selected_features()
		:param resume_widget: The widget inside your GroupBox (e.g., a QLabel or QTextEdit)
		"""

		group_box = self.parent.dlg.resum_box
		layout = group_box.layout()
		if layout is None:
			layout = QVBoxLayout(group_box)
			group_box.setLayout(layout)

		# Generate a label for each layer
		for layer_name, features in selection_dict.items():
			layer = QgsProject.instance().mapLayersByName(layer_name)[0]
			
			count = len(features)
			
			geom_enum = layer.geometryType()
			geom_name = QgsWkbTypes.geometryDisplayString(geom_enum)
			
			label_text = f"{count} features selected in layer {layer_name} [{geom_name}]"
			
			new_label = QLabel(label_text)
			layout.addWidget(new_label)

		layout.addStretch()


	def show_resume_groupbox(self, selection_dict):
		"""
		Clears the resume_box and creates a grid of info labels and action buttons.
		"""
		group_box = self.parent.dlg.resum_box
		
		# Setup or replace the layout with a QGridLayout
		if group_box.layout() is not None:
			old_layout = group_box.layout()
			while old_layout.count():
				item = old_layout.takeAt(0)
				if item.widget():
					item.widget().deleteLater()
		
		layout = QGridLayout(group_box)
		group_box.setLayout(layout)

		def open_table_at_top(layer):
			config = layer.attributeTableConfig()
			config.setSortExpression(None) 
			#config.setSelectedOnTop(True) 

			config.setSortExpression('is_selected()')
			config.setSortOrder(Qt.DescendingOrder)

			layer.setAttributeTableConfig(config)
			self.parent.iface.showAttributeTable(layer)

		def zoom_and_show(layer):
			# Ensure the layer is visible in the layer tree
			root = QgsProject.instance().layerTreeRoot()
			layer_node = root.findLayer(layer.id())
			if layer_node and not layer_node.isVisible():
				layer_node.setItemVisibilityChecked(True)
			
			# Zoom to selection
			self.parent.iface.mapCanvas().zoomToSelected(layer)
			self.parent.iface.mapCanvas().refresh()

		# Populate the Grid
		for i, (layer_name, features) in enumerate(selection_dict.items()):
			
			# Retrieve the layer object
			layers_found = QgsProject.instance().mapLayersByName(layer_name)
			if not layers_found:
				continue
			layer = layers_found[0]
			
			# Data preparation
			count = len(features)
			geom_name = QgsWkbTypes.geometryDisplayString(layer.geometryType())
			label_text = f"{count} features selected in layer {layer_name} [{geom_name}]"
			
			# Column 0: The Info Label
			label = QLabel(label_text)
			layout.addWidget(label, i, 0)
			
			# Column 1: The Attribute Table Button
			btn_table = QPushButton("Mostra taula de atributos")
			btn_table.clicked.connect(lambda checked=False, l=layer: open_table_at_top(l))
			layout.addWidget(btn_table, i, 1)
			
			# Column 2: The Zoom Button
			btn_zoom = QPushButton("Zoom a elements seleccionats")
			btn_zoom.clicked.connect(lambda checked=False, l=layer: zoom_and_show(l))
			layout.addWidget(btn_zoom, i, 2)

		# Add a stretch row at the bottom so elements don't spread out vertically
		layout.setRowStretch(len(selection_dict), 1)
		# Ensure column 0 takes up most of the space
		layout.setColumnStretch(0, 1)


	# def check_layer_compability(self, features, param):
	# 	"""  """

	# 	uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.publicSource());

	# 	# database layer
	# 	if 'table' in uri_components and (not uri_components['table'] in param["layers"].keys() or not param["layers"][uri_components['table']]["driver"] == "postgres"):

	# 		self.parent.iface.messageBar().pushMessage("Warning", f"Capa seleccionada no permesa! Has de seleccionar al menys una capa de {param['layers']}", level=Qgis.Warning, duration=5)
	# 		return False

	# 	# file layer
	# 	if 'path' in uri_components:
	# 		self.parent.iface.messageBar().pushMessage("Warning", f"Capa seleccionada no permesa! Has de seleccionar al menys una capa de {param['layers']}", level=Qgis.Warning, duration=5)
	# 		return False

	# 	return True


	def show_selected_features(self, layer, features):
		""" Show selected trees or superficies in table view """

		# for feature in features:
			# print(feature.attributes())

		#self.tableView = QgsAttributeTableView(self)
		self.layerCache = QgsVectorLayerCache(layer, len(features))
		self.modelTrees = QgsAttributeTableModel(self.layerCache)
		self.modelTrees.loadLayer()

		self.tableFilterModel = QgsAttributeTableFilterModel(self.parent.iface.mapCanvas(), self.modelTrees, parent=self.modelTrees)
		self.tableFilterModel.setFilterMode(QgsAttributeTableFilterModel.ShowSelected)
		self.parent.dlg.tbl_elements.setModel(self.tableFilterModel)

		# show count
		self.parent.dlg.label_elements.setText(DEFAULT_LABEL_ELEMENTS + "[" + str(self.tableFilterModel.rowCount()) + "]")

		# hide columns
		# for i in range(self.model.columnCount()):
			# fieldname = self.model.headerData(i, Qt.Horizontal)
			# if fieldname not in ARBRES_TABLE_FIELDS:
				# self.dlg_create.tbl_main.setColumnHidden(i, True)

		# set column width
		# fieldindex = self.model.fieldIndex('esp_nom')
		# self.dlg_create.tbl_main.setColumnWidth(fieldindex, 300)