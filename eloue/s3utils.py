from django.utils.functional import SimpleLazyObject
from django.conf import settings
from django.contrib.staticfiles.storage import CachedFilesMixin

from pipeline.storage import PipelineMixin
from storages.backends.s3boto import S3BotoStorage
from boto.utils import parse_ts

class S3PipelineStorage(PipelineMixin, CachedFilesMixin, S3BotoStorage):
    def modified_time(self, name):
        name = self._normalize_name(self._clean_name(name))
        entry = self.entries.get(name)
        if entry is None:
            entry = self.bucket.get_key(self._encode_name(name))

        # Parse the last_modified string to a local datetime object.
     	return parse_ts(entry.last_modified)



StaticRootS3BotoStorage = lambda **kwargs: S3PipelineStorage(
	bucket=settings.AWS_STATICSTORAGE_BUCKET_NAME, 
	custom_domain=settings.AWS_S3_CUSTOM_STATIC_DOMAIN,
	**kwargs)