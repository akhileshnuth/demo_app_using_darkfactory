import datetime
from django.db import models

class DuplicateModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('name', 'created_at'),)

    def is_duplicate(self):
        return DuplicateModel.objects.filter(name=self.name, created_at__date=datetime.date.today()).exists()