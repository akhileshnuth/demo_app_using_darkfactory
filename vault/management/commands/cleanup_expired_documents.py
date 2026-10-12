from django.core.management.base import BaseCommand

from vault.services import cleanup_expired_documents


class Command(BaseCommand):
    help = "Remove stored bytes for expired protected documents."

    def handle(self, *args, **options):
        count = cleanup_expired_documents()
        self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} expired document(s)."))
