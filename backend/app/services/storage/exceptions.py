class StorageError(Exception):
    pass


class StorageUploadError(StorageError):
    pass


class StorageDownloadError(StorageError):
    pass


class StorageDeleteError(StorageError):
    pass
