#!/usr/bin/env python3
"""
Backup MEDIA_ROOT to a timestamped ZIP and optionally upload to Cloudflare R2.
Usage examples (production):
  EXPORT env vars or use systemd service that sets them, then:
  python3 backup_and_upload_media.py --upload --remove-local-zip

Requirements:
  pip install boto3 python-dotenv

Security: keep R2 credentials in a secrets manager or environment variables.
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import shutil
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backup")


def make_backup(media_root: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base_name = backup_dir / f"media_backup_{ts}"
    # shutil.make_archive will create base_name + .zip
    logger.info("Creating zip archive for %s", media_root)
    archive_path = shutil.make_archive(str(base_name), 'zip', root_dir=str(media_root))
    archive_path = Path(archive_path)
    logger.info("Archive created: %s (size=%d bytes)", archive_path, archive_path.stat().st_size)
    return archive_path


def upload_to_r2(archive_path: Path, bucket: str, key_prefix: str, endpoint: str, access_key: str, secret_key: str, remove_after: bool = False) -> str:
    key_name = f"{key_prefix.rstrip('/')}/{archive_path.name}" if key_prefix else archive_path.name
    logger.info("Uploading %s to s3://%s/%s via endpoint %s", archive_path, bucket, key_name, endpoint)
    s3 = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    try:
        s3.upload_file(str(archive_path), bucket, key_name, ExtraArgs={
            'ContentType': 'application/zip',
            'CacheControl': 'private, max-age=2592000'
        })
    except ClientError as exc:
        logger.exception("Upload failed: %s", exc)
        raise
    url = f"https://{os.environ.get('CLOUDFLARE_CDN_DOMAIN') or endpoint.split('//')[-1]}/{key_name}"
    logger.info("Uploaded archive accessible (via CDN if configured): %s", url)
    if remove_after:
        try:
            archive_path.unlink()
            logger.info("Removed local archive %s", archive_path)
        except Exception:
            logger.exception("Failed to remove local archive")
    return url


def remove_media(media_root: Path):
    # Caution: This deletes everything under media_root
    logger.warning("Removing all files under %s", media_root)
    for child in media_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    logger.info("MEDIA_ROOT cleaned")


def main():
    parser = argparse.ArgumentParser(description="Backup MEDIA_ROOT and optionally upload to Cloudflare R2")
    parser.add_argument("--media-root", default=os.environ.get('MEDIA_ROOT', 'media'), help="Path to MEDIA_ROOT")
    parser.add_argument("--backup-dir", default=os.environ.get('BACKUP_DIR', '/var/backups/bolayetu'), help="Backup directory")
    parser.add_argument("--upload", action="store_true", help="Upload the created archive to R2")
    parser.add_argument("--r2-bucket", default=os.environ.get('CLOUDFLARE_R2_BUCKET'), help="R2 bucket name")
    parser.add_argument("--r2-endpoint", default=os.environ.get('CLOUDFLARE_R2_ENDPOINT'), help="R2 endpoint URL")
    parser.add_argument("--r2-access-key", default=os.environ.get('CLOUDFLARE_R2_ACCESS_KEY'), help="R2 access key")
    parser.add_argument("--r2-secret-key", default=os.environ.get('CLOUDFLARE_R2_SECRET_KEY'), help="R2 secret key")
    parser.add_argument("--r2-prefix", default=os.environ.get('R2_BACKUP_PREFIX', 'backups'), help="Prefix inside bucket")
    parser.add_argument("--remove-local-zip", action="store_true", help="Remove local zip after upload")
    parser.add_argument("--purge-media", action="store_true", help="Remove original media files AFTER successful upload (dangerous)")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except writing the archive and uploading")

    args = parser.parse_args()

    media_root = Path(args.media_root)
    backup_dir = Path(args.backup_dir)

    if not media_root.exists() or not any(media_root.iterdir()):
        logger.error("MEDIA_ROOT (%s) does not exist or is empty. Aborting.", media_root)
        sys.exit(2)

    if args.dry_run:
        logger.info("Dry-run: would create backup from %s into %s", media_root, backup_dir)
    try:
        if args.dry_run:
            # still create a report of files
            files = list(media_root.rglob('*'))
            logger.info("Dry-run: found %d files", len(files))
            for f in files[:20]:
                logger.info(" - %s", f)
            logger.info("Dry-run complete")
            return

        archive = make_backup(media_root, backup_dir)

        uploaded_url = None
        if args.upload:
            if not all([args.r2_bucket, args.r2_endpoint, args.r2_access_key, args.r2_secret_key]):
                logger.error("R2 configuration missing. Set env vars or provide arguments.")
                sys.exit(3)
            uploaded_url = upload_to_r2(archive, args.r2_bucket, args.r2_prefix, args.r2_endpoint, args.r2_access_key, args.r2_secret_key, remove_after=args.remove_local_zip)

        if args.purge_media:
            if not args.upload or not uploaded_url:
                logger.error("Refusing to purge media unless upload completed successfully")
                sys.exit(4)
            remove_media(media_root)

        logger.info("Backup process completed. archive=%s uploaded_url=%s", str(archive), str(uploaded_url))
    except Exception as exc:
        logger.exception("Backup/upload failed: %s", exc)
        sys.exit(10)


if __name__ == '__main__':
    main()
