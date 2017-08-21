class Database:
    def __init__(self):
        self.host     = None
        self.schema   = None
        self.port     = None
        self.username = None
        self.password = None

    @staticmethod
    def build_from(config_json):

        db = Database()
        db.host     = config_json["database_host"]
        db.schema   = config_json["database_schema"]
        db.port     = config_json["database_port"]
        db.username = config_json["database_user"]
        db.password = config_json["database_password"]

        return db

    def snapshot_command(self, path):
        return "mysqldump --user={} --password={} --port={} --host={} --result-file={} --add-drop-database --databases {}".format(
            self.username, 
            self.password, 
            self.port, 
            self.host, 
            path, 
            self.schema)

    def restore_command(self, path):
        return "mysql --user={} --password={} --port={} --host={} < {}".format(
        self.username, 
        self.password, 
        self.port, 
        self.host, 
        path
        )

    