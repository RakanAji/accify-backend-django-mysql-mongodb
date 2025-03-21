# crash_notifier/db_router.py

class MongoDBRouter:
    """
    A router to control all database operations on models in the tracking application,
    kecuali model IoTDevice yang akan disimpan di database default (MySQL).
    """
    route_app_labels = {'tracking'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            # Jika model adalah IoTDevice, gunakan database default (MySQL)
            if model.__name__.lower() == 'iotdevice':
                return 'default'
            # Model lain di tracking diarahkan ke MongoDB
            return 'mongodb'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            if model.__name__.lower() == 'iotdevice':
                return 'default'
            return 'mongodb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            # Pastikan migrasi untuk IoTDevice hanya dilakukan di default (MySQL)
            if model_name == 'iotdevice':
                return db == 'default'
            # Model lain di tracking hanya dimigrasi ke MongoDB
            return db == 'mongodb'
        return None
