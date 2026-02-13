from qgis.core import Qgis
from qgis.gui import QgsFileWidget
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from qgis.PyQt.QtWidgets import QLineEdit, QDateEdit, QComboBox, QPlainTextEdit

from datetime import datetime


DEFAULT_DATE = "9999-12-31"
COMBO_SELECT_TEXT = "(Seleccionar)"
STATIC_FIELDS = ["usuari"]


class gestor_incidencies_database:

	def __init__(self, parent, plugin_dir, param):

		self.parent = parent
		self.plugin_dir = plugin_dir
		self.param = param

		self.db_open = False
		self.last_error = None
		self.last_msg = None
		self.num_fields = None
		self.num_records = None

		DEFAULT_DATE = datetime.today().strftime('%Y-%m-%d')

		self.db = self.open_database()


	def open_database(self):
		""" Open database on server """

		if self.db_open:
			return self.db

		if self.param["service"] == "":
			self.last_error = "No s'ha definit cap servici"
			return None

		db = QSqlDatabase.addDatabase("QPSQL", self.param['service'])
		db.setConnectOptions(f"service={self.param['service']}")
		db.open()
		if db.isOpen() == 0:
			self.last_error = f"No s'ha pogut obrir la Base de Dades del servidor\n\n{db.lastError().text()}"
			return None

		#print("connected to database")

		self.db_open = True
		return db


	def close_database(self):
		"""Close database on server """

		if not self.db_open:
			return True
		self.db.close()
		self.db_open = False
		return True


	def get_user_name(self):
		""" Get the user name from the database connection """

		query = QSqlQuery(self.db)
		if query.exec("SELECT current_user"):
			if query.next():
				user_name = query.value(0)
				print(f"Connected as: {user_name}")
				return user_name

		return ""


	def reset_info(self):
		""" Reset query information values """

		self.last_error = None
		self.last_msg = None
		self.num_fields = None
		self.num_records = None


	# def get_table_fields(self):
		# """ Get all fields from table incidencies """

		# #try:
		# print(f"Obtenint llistat de camps de la taula '{self.param['table']}'")
		# sql = f"SELECT * FROM {self.param['table']} WHERE 1=0"
		# self.cursor.execute(sql)
		# self.fieldnames = [desc[0] for desc in self.cursor.description]
		# # except (Exception, psycopg2.Error) as error:
			# # print(f"Error al recuperar camps de la taula: {error}")
			# # return False
		# return True
		
	
	def prepare_insert(self, data):
		""" prepare sql query """
		
		sql = None
		list_fields = []
		list_values = []
		
		# Iterate over field names and values from dictionary data
		for field, value in data.items():
			if value in (COMBO_SELECT_TEXT, '--'):
				continue
			if value and value != '' and value != DEFAULT_DATE:
				value = value.replace("'", "''").strip()
				list_fields.append(field)
				list_values.append(value)

		str_fields = ", ".join(list_fields)
		str_values = "', '".join(list_values)

		for field in STATIC_FIELDS:
			str_fields += f", {field}"
			str_values += f"', '{self.get_user_name()}"
		
		return str_fields, str_values


	def insert_sql(self, sql):
		""" insert SQL query into database """

		print("execute:", sql)
		
		try:
			self.reset_info()
			query = QSqlQuery(self.db)
			status = query.exec(sql)

			if not status:
				self.last_error = query.lastError().text()
				return None
			
			self.parent.dlg.messageBar.pushMessage(f"Nova incidencia creada a base de dades amb id '{query.lastInsertId()}'.", level=Qgis.Success, duration=5)

			return query.lastInsertId()

		except (Exception) as error:
			self.parent.dlg.messageBar.pushMessage(f"Error actualitzant les dades a la taula de PostgreSQL: {error}", level=Qgis.Warning, duration=5)
			print("ERROR", error)
			if sql:
				print(f"SQL: {sql}")
			return False

		
	def insert_incidencia(self, selected_features):
		""" insert new incidencia """

		if not self.check_fields_mandatory(self.param['fields_mandatory']):
			return False

		data = self.prepare_data()

		str_fields, str_values = self.prepare_insert(data)

		sql = f"INSERT INTO {self.param['tbl_incidencies']} ({str_fields}) VALUES ('{str_values}') RETURNING id;"
		
		incidencia_id = self.insert_sql(sql)
		#self.reset_info()

		if incidencia_id:
			self.insert_incidencia_correlacio(incidencia_id, selected_features)
			self.insert_incidencia_foto(incidencia_id)


	def insert_incidencia_correlacio(self, incidencia_id, selected_features):
		""" insert new incidencia relations with selected features """

		#print("insert selected features into incidencia", incidencia_id)

		for layer in selected_features:
			for feature in selected_features[layer]:

				str_fields = "nom_capa, id_capa, id_incidencia"
				str_values = f"'{layer}', {feature.id()}, {incidencia_id}"
				sql = f"INSERT INTO {self.param['tbl_correlacions']} ({str_fields}) VALUES ({str_values});"

				self.insert_sql(sql)


	def insert_incidencia_foto(self, incidencia_id):
		""" insert fotos for new incidencia """

		#print("insert fotos into incidencia", incidencia_id)

		fotos = self.parent.dlg.fotos.splitFilePaths(self.parent.dlg.fotos.filePath())

		for foto in fotos:
			str_fields = "id_incidencia, link_foto"
			str_values = f"{incidencia_id}, '{foto}'"
			sql = f"INSERT INTO {self.param['tbl_fotos']} ({str_fields}) VALUES ({str_values});"

			self.insert_sql(sql)


	def prepare_data(self):
		""" Create dictionary with field names and widget values """

		data = {}
		for fieldname in self.param['fields']:
			widget, widget_data = self.get_widget_data(fieldname)
			if widget is None:
				print(f"El camp de la taula no té cap component associat: {fieldname}")
				continue
			data[fieldname] = widget_data

		return data


	def get_widget_data(self, fieldname):

		widget = None
		data = None
		if not hasattr(self.parent.dlg, fieldname):
			return None, None
		widget = getattr(self.parent.dlg, fieldname)
		if type(widget) == QLineEdit:
			data = widget.text()
		elif type(widget) == QPlainTextEdit:
			data = widget.toPlainText()
		elif type(widget) is QComboBox:
			data = widget.currentText()
		elif type(widget) is QDateEdit:
			date = widget.date()
			data = date.toString("yyyy-MM-dd")
		elif type(widget) is QgsFileWidget:
			data = widget.filePath()
		else:
			print(f"Tipus de component no suportat pel camp '{fieldname}': {type(widget)}")
		return widget, data


	def check_fields_mandatory(self, list_mandatory):

		for fieldname in list_mandatory:
			widget, widget_data = self.get_widget_data(fieldname)
			if widget is None:
				self.parent.dlg.messageBar.pushMessage(f"El camp no té cap component associat: {fieldname}", level=Qgis.Warning, duration=3)
				continue
			if widget_data in (COMBO_SELECT_TEXT, '--') or widget_data == '' or widget_data == DEFAULT_DATE:
				self.parent.dlg.messageBar.pushMessage(f"Camp obligatori sense informació: {fieldname}", level=Qgis.Warning, duration=3)
				widget.setFocus()
				return False

		return True