"""Shared workspace storage and optimistic-concurrency errors."""


class WorkspaceNotFound(Exception):
    pass


class RevisionConflict(Exception):
    pass


class UnsupportedSchema(Exception):
    pass


class StorageUnavailable(Exception):
    pass
