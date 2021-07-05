from django.contrib import admin
from .models import Images, Sessions, Annotations, Notes


# Register your models here.
admin.site.register(Images)
admin.site.register(Sessions)
admin.site.register(Annotations)
admin.site.register(Notes)

