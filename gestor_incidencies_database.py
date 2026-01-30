from PyQt5.QtSql import QSqlDatabase, QSqlQuery


DEFAULT_DATE = "9999-12-31"


class gestor_incidencies_database:

	def __init__(self, plugin_dir, param):

		self.plugin_dir = plugin_dir
		self.param = param
		self.db = None
		self.obert = False
		self.db_open = False
		self.last_error = None
		self.last_msg = None
		self.num_fields = None
		self.num_records = None


	def open_database(self):
		""" Open database on server """

		if self.db_open:
			return self.db

		if self.param["service"] == "":
			self.last_error = "No s'ha definit service"
			return None

		self.db = QSqlDatabase.addDatabase("QPSQL", self.param['database'])
		self.db.setConnectOptions(f"service={self.param['service']}")
		self.db.open()
		if self.db.isOpen() == 0:
			self.last_error = f"No s'ha pogut obrir la Base de Dades del servidor\n\n{self.db.lastError().text()}"
			return None

		self.db_open = True
		print("connected to database")
		return self.db


	def close_database(self):
		"""Close database on server """

		if not self.db_open:
			return True
		self.db.close()
		self.db_open = False
		return True


	def reset_info(self):
		""" Reset query information values """

		self.last_error = None
		self.last_msg = None
		self.num_fields = None
		self.num_records = None


	def exec_sql(self, sql):
		""" Execute SQL (Insert or Update) """

		self.reset_info()
		query = QSqlQuery(self.db)
		status = query.exec(sql)
		if not status:
			self.last_error = query.lastError().text()
		return status


	def get_rows(self, sql):
		""" Execute SQL (Select) and return rows """

		print("execute", sql)

		self.reset_info()
		query = QSqlQuery(self.db)
		status = query.exec(sql)
		if not status:
			self.last_error = query.lastError().text()
			return None

		# Get number of records
		self.num_records = query.size()
		if self.num_records == 0:
			self.last_msg = "No s'ha trobat cap registre amb els filtres seleccionats"
			return None

		# Get number of fields
		record = query.record()
		self.num_fields = record.count()
		if self.num_fields == 0:
			self.last_msg = "No s'han especificat camps a retornar"
			return None

		rows = []
		while query.next():
			row = []
			for i in range(self.num_fields):
				row.append(query.value(i))
			rows.append(row)

		return rows


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
			if value in ('(Seleccionar)', '--'):
				continue
			if value != '' and value != DEFAULT_DATE:
				value = value.replace("'", "''").strip()
				list_fields.append(field)
				list_values.append(value)

		str_fields = ", ".join(list_fields)
		str_values = "', '".join(list_values)
		
		return str_fields, str_values
		
		
	def insert_record(self, data):
		""" insert new incidencia """

		str_fields, str_values = self.prepare_insert(data)

		sql = f"INSERT INTO {self.param['schema']}.{self.param['table']} ({str_fields}) "
		values = f"VALUES ('{str_values}') RETURNING id;"
		sql += values
		
		print("execute", sql)
		
		try:
			self.reset_info()
			query = QSqlQuery(self.db)
			status = query.exec(sql)
			print(status)
			if not status:
				self.last_error = query.lastError().text()
				return None
			
			return True

		except (Exception) as error:
			#self.iface.messageBar().pushMessage("Warning", f"Error actualitzant les dades a la taula de PostgreSQL: {error}", level=Qgis.Warning, duration=5)
			print("ERROR", error)
			if sql:
				print(f"SQL: {sql}")
			return False


	def prepare_udpate(self, data):
		""" prepare sql query """
		
		sql = None
		list_fields = []
		list_values = []
		
		# Iterate over field names and values from dictionary data
		for field, value in data.items():
			if value in ('(Seleccionar)', '--'):
				continue
			if value != '' and value != DEFAULT_DATE:
				value = value.replace("'", "''").strip()
				list_fields.append(field)
				list_values.append(value)

		str_values = ""
		i = 0
		for field in list_fields:
			if str_values != "":
				str_values += ", "
			str_values += field + "=" + list_values[i]
			i+=1
			
		print(str_values)
		
		return str_values
		

	def update_record(self, data, id):
		""" update existing incidencia """
	
		str_set = self.prepare_udpate(data)

		sql = f"UPDATE {self.param['schema']}.{self.param['table']} "
		sql += f"SET {str_set} "
		sql += f"WHERE id={id};"
		
		print("execute", sql)
		self.exec_sql(sql)

				
	def delete_record(self, id):
		""" delete incidencia by id """

		sql = f"DELETE FROM {self.param['schema']}.{self.param['table']} WHERE id={id}"
		print("execute", sql)
		
		self.exec_sql(sql)