from ..smonitor_emit import message_from_catalog


class FileAlreadyHandledError(Exception):
    def __init__(self, filename):
        default_message = f"The file {filename} is already handled by MolSysViewer."
        full_message = message_from_catalog(
            "file_already_handled",
            extra={"filename": filename},
            default_message=default_message,
        )
        super().__init__(full_message)
