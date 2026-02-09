"""Management command to mark stuck (processing) tasks as failed so they can be retried."""

from django.core.management.base import BaseCommand

from converter.models import ConversionTask


STUCK_MESSAGE = "Processing was interrupted or stuck. Use Retry from the result/history page to try again."


class Command(BaseCommand):
    help = "Mark task(s) stuck in 'processing' as 'failed' so they can be retried from the UI."

    def add_arguments(self, parser):
        parser.add_argument(
            "task_ids",
            nargs="+",
            type=int,
            help="ConversionTask primary key(s) to reset (e.g. 7).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be reset without changing the database.",
        )

    def handle(self, *args, **options):
        task_ids = options["task_ids"]
        dry_run = options["dry_run"]

        tasks = ConversionTask.objects.filter(pk__in=task_ids)
        stuck = tasks.filter(status=ConversionTask.Status.PROCESSING)

        if not stuck.exists():
            missing = set(task_ids) - set(tasks.values_list("pk", flat=True))
            if missing:
                self.stdout.write(
                    self.style.ERROR(f"Task(s) not found: {sorted(missing)}")
                )
            for t in tasks.exclude(status=ConversionTask.Status.PROCESSING):
                self.stdout.write(
                    self.style.WARNING(
                        f"Task {t.pk} ({t.original_filename}) is not stuck: status={t.status}"
                    )
                )
            if not missing and stuck.count() == 0:
                self.stdout.write(
                    self.style.WARNING("No tasks in 'processing' state to reset.")
                )
            return

        for task in stuck:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] Would reset task {task.pk} ({task.original_filename})"
                    )
                )
                continue
            task.status = ConversionTask.Status.FAILED
            task.error_message = STUCK_MESSAGE
            task.save(update_fields=["status", "error_message"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reset task {task.pk} ({task.original_filename}) → failed. You can retry from history."
                )
            )

        if not dry_run and stuck.count():
            self.stdout.write(
                self.style.SUCCESS(f"Reset {stuck.count()} stuck task(s).")
            )
