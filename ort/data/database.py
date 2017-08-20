class Database:
  def __init__(self):
    self.host     = None
    self.schema   = None
    self.port     = None
    self.username = None
    self.password = None

  @staticmethod
  def build_from_json(config_json):
    db.host     = config_json["host"]
    db.schema   = config_json["schema"]
    db.port     = config_json["port"]
    db.username = config_json["username"]
    db.password = config_json["password"]

    return db