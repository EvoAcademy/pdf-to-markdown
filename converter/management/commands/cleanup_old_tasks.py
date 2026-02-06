"""Management command to delete old ConversionTask records and their files."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from converter.models import ConversionTask


class Command(BaseCommand):
    help = "Delete ConversionTask records (and associated files) older than N days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete tasks older than this many days (default: 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        tasks = ConversionTask.objects.filter(created_at__lt=cutoff)
        count = tasks.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No tasks older than {days} days."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} task(s) older than {days} days."
                )
            )
            for task in tasks:
                self.stdout.write(f"  - {task.original_filename} ({task.created_at})")
            return

        # Delete files from disk, then delete the DB records
        for task in tasks:
            if task.pdf_file:
                try:
                    task.pdf_file.delete(save=False)
                except Exception:
                    pass
            if task.markdown_file:
                try:
                    task.markdown_file.delete(save=False)
                except Exception:
                    pass

        tasks.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} task(s) older than {days} days."
            )
        )
