from django.db import models

class SearchHistory(models.Model):
    search_query = models.CharField(max_length=255, unique=True)
    wordcloud_image = models.ImageField(upload_to='wordclouds/', null=True, blank=True)

    def __str__(self):
        return self.search_query
    
    @classmethod
    def get_random_quiz_question(cls):
        return cls.objects.order_by('?').first()