from django.contrib import admin
from django.db import models
# Register your models here.
from sophia.models import Testimonial, PageText, Timeslot, BlogPost, BlogTag

class TestimonialAdmin(admin.ModelAdmin):
    model = Testimonial

    list_display = ('client_name', 'text', 'start_year', 'end_year', 'priority')

class TimeslotAdmin(admin.ModelAdmin):
    model = Timeslot
    list_display = ('start_time', 'end_time', 'day', 'available')
    ordering = ('day', 'start_time')

class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_on', 'updated_on',)
    ordering = ('-updated_on', '-created_on')
    search_fields = ['title', 'content']
    filter_horizontal = ('tags', )

admin.site.register(Testimonial, TestimonialAdmin)
admin.site.register(Timeslot, TimeslotAdmin)
admin.site.register(PageText)
admin.site.register(BlogTag)
admin.site.register(BlogPost, BlogPostAdmin)