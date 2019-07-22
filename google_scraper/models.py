from django.db import models

# Create your models here.

class Query(models.Model):
    ip = models.CharField(max_length=100, null=True, blank=True)
    phrase = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    num_results = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return '{} | {} | {}'.format(self.phrase, self.created, self.ip)


class Link(models.Model):
    link = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    position = models.PositiveIntegerField()
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='links')
    class Meta:
        ordering = ('position',)

    def __str__(self):
        return 'Request {}: {}'.format(self.request, self.link)