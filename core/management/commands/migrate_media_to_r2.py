import os
import csv
import logging
import mimetypes
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from django.db.models import FileField, ImageField
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger('media_migration')

class Command(BaseCommand):
    help = 'Migrate local MEDIA files into Cloudflare R2 bucket.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Don\'t upload, just report')
        parser.add_argument('--prefix', type=str, default='', help='Only migrate files whose path starts with PREFIX')
        parser.add_argument('--log-file', type=str, default='media_migration_report.csv', help='CSV report file path')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = options['prefix']
        report_file = options['log_file']

        s3_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', os.environ.get('CLOUDFLARE_R2_ENDPOINT'))
        access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', os.environ.get('CLOUDFLARE_R2_ACCESS_KEY'))
        secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', os.environ.get('CLOUDFLARE_R2_SECRET_KEY'))
        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', os.environ.get('CLOUDFLARE_R2_BUCKET'))

        # Allow dry-run without R2 credentials so local scanning can be validated first
        if not all([s3_endpoint, access_key, secret_key, bucket]) and not dry_run:
            self.stdout.write(self.style.ERROR('Missing R2 configuration (endpoint/access/secret/bucket).'))
            return

        s3 = None
        if not dry_run:
            s3 = boto3.client(
                's3',
                endpoint_url=s3_endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', None),
            )

        rows = []
        rows.append(['model', 'pk', 'field', 'file_field_value', 'local_exists', 'r2_exists', 'action', 'error'])

        total = 0
        uploaded = 0
        skipped = 0
        failures = 0

        for model in apps.get_models():
            file_fields = [f for f in model._meta.fields if isinstance(f, (FileField, ImageField))]
            if not file_fields:
                continue
            qs = model.objects.all().iterator()
            for inst in qs:
                for field in file_fields:
                    file_field = getattr(inst, field.name)
                    if not file_field:
                        continue
                    value = file_field.name
                    if not value:
                        continue
                    if prefix and not value.startswith(prefix):
                        continue

                    total += 1
                    local_path = os.path.join(settings.MEDIA_ROOT, value)
                    r2_key = value.replace('\\', '/')

                    # check R2 existence (skip if dry-run / s3 client not configured)
                    r2_exists = False
                    if s3:
                        try:
                            s3.head_object(Bucket=bucket, Key=r2_key)
                            r2_exists = True
                        except ClientError:
                            r2_exists = False
                    else:
                        r2_exists = False

                    local_exists = os.path.exists(local_path) and os.path.getsize(local_path) > 0

                    if r2_exists:
                        skipped += 1
                        action = 'skipped_exists'
                        rows.append([model.__name__, inst.pk, field.name, value, local_exists, r2_exists, action, ''])
                        continue

                    if not local_exists:
                        failures += 1
                        action = 'missing_local'
                        rows.append([model.__name__, inst.pk, field.name, value, local_exists, r2_exists, action, 'local file not found'])
                        logger.warning('Missing local file: %s (model=%s pk=%s)', local_path, model.__name__, inst.pk)
                        continue

                    try:
                        if dry_run:
                            action = 'dry_run_upload'
                            rows.append([model.__name__, inst.pk, field.name, value, local_exists, r2_exists, action, ''])
                            continue

                        content_type, _ = mimetypes.guess_type(local_path)
                        extra_args = {}
                        if content_type:
                            extra_args['ContentType'] = content_type

                        if str(local_path).lower().endswith(('.pdf', '.docx', '.xlsx')):
                            extra_args['CacheControl'] = 'max-age=3600, s-maxage=3600, public'
                        else:
                            extra_args['CacheControl'] = 'max-age=31536000, s-maxage=31536000, public'

                        with open(local_path, 'rb') as fh:
                            s3.upload_fileobj(fh, bucket, r2_key, ExtraArgs=extra_args)

                        uploaded += 1
                        action = 'uploaded'
                        rows.append([model.__name__, inst.pk, field.name, value, local_exists, True, action, ''])
                        logger.info('Uploaded %s to s3://%s/%s', local_path, bucket, r2_key)
                    except Exception as exc:
                        failures += 1
                        action = 'error'
                        rows.append([model.__name__, inst.pk, field.name, value, local_exists, False, action, str(exc)])
                        logger.exception('Failed to upload %s: %s', local_path, exc)

        with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(f'Migration finished: total={total}, uploaded={uploaded}, skipped={skipped}, failures={failures}'))
        self.stdout.write(self.style.SUCCESS(f'Report written to {report_file}'))
