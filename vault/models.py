import datetime
from django.db import models

class SampleModel(models.Model):
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.created_at < datetime.datetime.now() - datetime.timedelta(days=30)


class AnotherModel(models.Model):
    document = models.ForeignKey(SampleModel, on_delete=models.CASCADE)
    expiry_date = models.DateField()

    def is_duplicate(self):
        return AnotherModel.objects.filter(expiry_date=self.expiry_date).exists()