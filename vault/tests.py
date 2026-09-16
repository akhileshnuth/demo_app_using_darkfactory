import datetime
from django.test import TestCase
from .models import SampleModel, AnotherModel

class SampleModelTests(TestCase):
    def setUp(self):
        self.sample = SampleModel.objects.create(title='Test Title')

    def test_is_expired(self):
        self.sample.created_at = datetime.datetime.now() - datetime.timedelta(days=31)
        self.sample.save()
        self.assertTrue(self.sample.is_expired())

class AnotherModelTests(TestCase):
    def setUp(self):
        self.sample = SampleModel.objects.create(title='Test Title')
        self.another = AnotherModel.objects.create(document=self.sample, expiry_date=datetime.date.today())

    def test_is_duplicate(self):
        duplicate = AnotherModel(document=self.sample, expiry_date=self.another.expiry_date)
        self.assertTrue(duplicate.is_duplicate())