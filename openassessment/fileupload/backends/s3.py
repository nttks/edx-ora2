import boto
from boto.s3.key import Key
from boto.exception import S3ResponseError
import logging
from django.conf import settings

logger = logging.getLogger("openassessment.fileupload.api")

from .base import BaseBackend
from ..exceptions import FileUploadInternalError, FileUploadRequestError


class Backend(BaseBackend):

    def upload_file(self, key, fp):
        """
        Uploads an image file and returns the signed url for download.
        """
        bucket_name, key_name = self._retrieve_parameters(key)
        waf_proxy_enabled = hasattr(settings, 'FEATURES') and settings.FEATURES.get('ENABLE_ORA2_WAF_PROXY', False)
        try:
            conn = _connect_to_s3(waf_proxy_enabled)
            bucket = conn.get_bucket(bucket_name)
            s3_key = Key(bucket=bucket, name=key_name)
            # Note: S3ResponseError(403 Forbidden) raises if WAF proxy detects a virus in setting contents
            s3_key.set_contents_from_file(fp, size=fp.size)
            return s3_key.generate_url(expires_in=self.DOWNLOAD_URL_TIMEOUT)
        except S3ResponseError as ex:
            # Check if the specified keyword exists in ex.message
            if waf_proxy_enabled and ex.message and settings.ORA2_WAF_VIRUS_DETECTION_KEYWORD in ex.message:
                logger.warning(
                    u"WAF proxy has detected a virus while uploading a file. key_name={}".format(key_name)
                )
                raise FileUploadRequestError(ex)
            else:
                logger.exception(
                    u"An internal exception occurred while uploading a file."
                )
                raise FileUploadInternalError(ex)
        except Exception as ex:
            logger.exception(
                u"An internal exception occurred while uploading a file."
            )
            raise FileUploadInternalError(ex)

    def get_upload_url(self, key, content_type):
        bucket_name, key_name = self._retrieve_parameters(key)
        try:
            conn = _connect_to_s3()
            upload_url = conn.generate_url(
                expires_in=self.UPLOAD_URL_TIMEOUT,
                method='PUT',
                bucket=bucket_name,
                key=key_name,
                headers={'Content-Length': '5242880', 'Content-Type': content_type}
            )
            return upload_url
        except Exception as ex:
            logger.exception(
                u"An internal exception occurred while generating an upload URL."
            )
            raise FileUploadInternalError(ex)


    def get_download_url(self, key):
        bucket_name, key_name = self._retrieve_parameters(key)
        try:
            conn = _connect_to_s3()
            bucket = conn.get_bucket(bucket_name)
            s3_key = bucket.get_key(key_name)
            return s3_key.generate_url(expires_in=self.DOWNLOAD_URL_TIMEOUT) if s3_key else ""
        except Exception as ex:
            logger.exception(
                u"An internal exception occurred while generating a download URL."
            )
            raise FileUploadInternalError(ex)


def _connect_to_s3(waf_proxy_enabled=False):
    """Connect to s3

    Creates a connection to s3 for file URLs.

    """
    # Try to get the AWS credentials from settings if they are available
    # If not, these will default to `None`, and boto will try to use
    # environment vars or configuration files instead.
    aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    if waf_proxy_enabled:
        waf_proxy_ip = getattr(settings, 'ORA2_WAF_PROXY_SERVER_IP', None)
        waf_proxy_port = getattr(settings, 'ORA2_WAF_PROXY_SERVER_PORT', None)
        if not waf_proxy_ip or not waf_proxy_port:
            msg = "WAF proxy feature for ORA2 file upload is enabled, but WAF server ip or port is not configured."
            logger.exception(
                "{msg} ORA2_WAF_PROXY_SERVER_IP={waf_proxy_ip}, ORA2_WAF_PROXY_SERVER_PORT={waf_proxy_port}".format(
                    msg=msg,
                    waf_proxy_ip=waf_proxy_ip,
                    waf_proxy_port=waf_proxy_port,
                )
            )
            raise Exception(msg)
        logger.info("Connect to S3 with WAF proxy.")
        return boto.connect_s3(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            is_secure=False,
            proxy=waf_proxy_ip,
            proxy_port=waf_proxy_port
        )
    else:
        return boto.connect_s3(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
