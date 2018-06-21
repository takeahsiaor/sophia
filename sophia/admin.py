from django.contrib import admin
from django import forms
from django.db import models
# Register your models here.
from sophia.models import (
    BlogPost,
    BlogTag,
    GalleryImage,
    GalleryImageTag,
    PageText,
    ScheduledLesson,
    Student,
    Testimonial,
)


class GalleryImageTagAdmin(admin.ModelAdmin):
    model = GalleryImageTag

    list_display = ('name',)


class GalleryImageAdmin(admin.ModelAdmin):
    model = GalleryImage

    list_display = ('title', 'caption', 'ordering', 'priority', 'image')
    ordering = ('ordering',)

class TestimonialAdmin(admin.ModelAdmin):
    model = Testimonial

    list_display = ('client_name', 'text', 'start_year', 'end_year', 'priority')


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_on', 'updated_on',)
    ordering = ('-updated_on', '-created_on')
    search_fields = ['title', 'content']
    filter_horizontal = ('tags', )


class ScheduledLessonAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'start_time', 'end_time',
        'student', 'is_trial', 'is_reschedule', 'completed_on',
        'cancelled_on', 'rescheduled_on'
    )
    ordering = ('-date',)


class StudentForm(forms.ModelForm):

    def clean_timeslot(self):
        # Don't allow two active students in one time slot
        timeslot_pks = self.data.get('timeslot')
        if timeslot_pks:
            timeslots = Timeslot.objects.filter(pk__in=timeslot_pks)
            for timeslot in timeslots:
                current_student = timeslot.get_active_student()
                if current_student and current_student != self.instance:
                    raise forms.ValidationError(
                        'There is already an active student in this timeslot'
                    )
        return timeslots

class StudentAdmin(admin.ModelAdmin):
    model = Student
    form = StudentForm
    list_display = (
        'first_name', 'last_name', 'rate', 'day',
        'start_time', 'end_time', 'active', 'is_trial', 'is_held')
    list_filter = (
        'is_trial', 'is_held', 'day'
        )

admin.site.register(GalleryImage, GalleryImageAdmin)
admin.site.register(GalleryImageTag, GalleryImageTagAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Testimonial, TestimonialAdmin)
admin.site.register(PageText)
admin.site.register(BlogTag)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(ScheduledLesson, ScheduledLessonAdmin)