"""
The File Upload application is designed to allow the management of files
associated with submissions. This can be used to upload new files and provide
URLs to the new location.

"""

from . import backends


def upload_file(key, fp):
    """
    Uploads an image file and returns the signed url for download.
    """
    return backends.get_backend().upload_file(key, fp)


def get_upload_url(key, content_type):
    """
    Returns a url (absolute or relative, depending on the endpoint) which can be used to upload a file to.
    """
    return backends.get_backend().get_upload_url(key, content_type)

def get_download_url(key):
    """
    Returns the url at which the file that corresponds to the key can be downloaded.
    """
    return backends.get_backend().get_download_url(key)
