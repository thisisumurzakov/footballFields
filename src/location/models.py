from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    region = models.ForeignKey(Region, related_name='cities', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('region', 'name')
        verbose_name = 'City'
        verbose_name_plural = 'Cities'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.region.name}'


class District(models.Model):
    city = models.ForeignKey(City, related_name='districts', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('city', 'name')
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.city.name}'
