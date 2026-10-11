from django.db import models
from django_countries.fields import CountryField


class EventType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Company(models.Model):
    company_name = models.CharField(max_length=255)
    company_address = models.CharField(max_length=255)
    company_state = models.CharField(max_length=255)
    company_city = models.CharField(max_length=255)
    company_zippostal = models.CharField(max_length=10)
    company_country = CountryField()
    company_email = models.EmailField()
    company_phone = models.CharField(max_length=20, blank=True, null=True)
    company_region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.company_name
