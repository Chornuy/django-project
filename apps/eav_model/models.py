from django.db import models


class AttributeName(models.Model):
    name = models.TextField()


class AttributeValue(models.Model):
    attribute = models.ForeignKey(AttributeName, on_delete=models.CASCADE)
    value = models.JSONField()
