from django.contrib.auth.models import User
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


class StaffMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Customer(models.Model):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE)
    added_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} {self.surname}'


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    margin = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Quote(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date_issued = models.DateField(auto_now_add=True)
    next_follow_up = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Quote #{self.pk} for {self.customer}'
