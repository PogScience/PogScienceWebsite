from django.core.files.storage import get_storage_class


class OverwriteStorage(get_storage_class()):
    """
    Storage class that always overwrite existing files.
    """
    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return super().get_available_name(name, max_length)
