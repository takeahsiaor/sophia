import datetime, calendar
import json

from collections import OrderedDict

from django.db import models
from django.db.models import Q
from django.db.models.fields.files import ImageFieldFile, ImageField

from ckeditor.fields import RichTextField


class SmartImageFieldFile(ImageFieldFile):
    """
    This is an image file that, in addition to all the nice
    things django adds, will expose a method to calculate
    whether the image is landscape or portrait
    """
    def _is_wide(self):
        self._require_file()
        aspect_ratio = float(self.width)/self.height
        # of should this be 5:3?
        # show as landscape if aspect ratio of 2:1 or greater
        if aspect_ratio >= 1.66:
            return True
        return False

    def _is_landscape(self):
        self._require_file()
        if self.width > self.height:
            return True
        return False

    is_wide = property(_is_wide)
    is_landscape = property(_is_landscape)


class SmartImageField(ImageField):
    """
    An extremely thin wrapping around ImageField simply adding
    a hook into determining if an image should be displayed
    in landscape or portrait
    """
    attr_class = SmartImageFieldFile


class GalleryImageTag(models.Model):
    name = models.CharField(max_length=40)

    def save(self):
        # force name to be title case
        self.name = self.name.title()
        super(GalleryImageTag, self).save()

    def __unicode__(self):
        return self.name


class GalleryImage(models.Model):
    image = SmartImageField(upload_to='./gallery_images/')
    title = models.CharField(max_length=255, blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    ordering = models.IntegerField(default=1)
    priority = models.BooleanField(
        default=False,
        help_text="Determines if this image should be displayed on home screen"
    )
    tags = models.ManyToManyField(GalleryImageTag)


class BlogTag(models.Model):
    name = models.CharField(max_length=40)

    def save(self):
        # force name to be title case
        self.name = self.name.title()
        super(BlogTag, self).save()

    def __unicode__(self):
        return self.name


class BlogPost(models.Model):
    main_image = SmartImageField(upload_to='./blog_main_images/',
                                    blank=True,
                                    null=True,
                                    help_text="For best results, the width of the image \
                                                should be larger than the height. Ideally \
                                                5:3 aspect ratio")
    title = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(BlogTag)
    content = RichTextField()

    def clean(self):
        self.content = self.content.replace('<p>&nbsp;</p>', '')
        super(BlogPost, self).clean()


class Testimonial(models.Model):
    client_name = models.CharField(max_length=255)
    start_year = models.CharField(max_length=4)
    end_year = models.CharField(blank=True, null=True, max_length=4)
    text = models.TextField()
    priority = models.BooleanField(
                        default=False,
                        help_text="Should this testimonial be prioritized \
                        to be displayed?")

    def __unicode__(self):
        return "%s testimonial" % self.client_name


class PageText(models.Model):
    """
    A Page text represents the text on a page. Each view will query for a
    PageText object and if one exists, then will display that.
    
    Must implement WYSIWYG editor for this
    """
    page_name = models.CharField(max_length=255)
    text = RichTextField()


class ScheduledLessonQuerySet(models.QuerySet):
    def filter_by_month(self, month_index, year):
        start_date = datetime.date(day=1, month=month_index, year=year)
        if month_index == 12:
            end_month = 1
            end_year = year + 1
        else:
            end_month = month_index + 1
            end_year = year
        end_date = datetime.date(day=1, month=end_month, year=end_year)
        return self.filter(date__gte=start_date).filter(date__lt=end_date)

    def group_by_date(self):
        lessons_dict = OrderedDict()
        dates = self.values_list('date', flat=True).order_by('date').distinct()
        for date in dates:
            lessons_dict[date] = []

        for lesson in self:
            lessons_dict[lesson.date].append(lesson)
        return lessons_dict


class ScheduledLessonManager(models.Manager):
    def get_queryset(self):
        return ScheduledLessonQuerySet(self.model, using=self._db)

    def filter_by_month(self, month_index, year):
        return self.get_queryset().filter_by_month(month_index, year)

class ScheduledLesson(models.Model):
    """
    Represents the actual weekly instance of a lesson.

    Unpersisted versions are presented to the user and only given a pk when
    a user schedules.

    Up to us then to make it available if a trial lesson isn't converted to a full
    time student
    """
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    student = models.ForeignKey('Student')
    is_trial = models.BooleanField(default=False)
    is_reschedule = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    cancelled_on = models.DateTimeField(blank=True, null=True)
    rescheduled_on = models.DateTimeField(blank=True, null=True)

    objects = ScheduledLessonManager()

    @property
    def is_completed(self):
        return bool(self.completed_on)

    @property
    def is_cancelled(self):
        return bool(self.cancelled_on)

    @property
    def is_rescheduled(self):
        return bool(self.rescheduled_on)

    @property
    def is_pending(self):
        return bool(
            not self.rescheduled_on and not self.cancelled_on and not self.completed_on
        )

    @property
    def color(self):
        color = '#539ce7'
        if self.is_completed:
            # green
            color = '#87b667'
        elif self.is_cancelled:
            # gray
            color = '#b0b0b0'
        elif self.is_rescheduled:
            # orange
            color = '#eea236'
        return color

    def get_start_time_string(self):
        dt = datetime.datetime.combine(self.date, self.start_time)
        return dt.isoformat() 

    def get_end_time_string(self):
        dt = datetime.datetime.combine(self.date, self.end_time)
        return dt.isoformat() 

    def __unicode__(self):
        return '%s, %s' % (self.date, self.student)


class Student(models.Model):
    # TODO: when updating a student's canonical time, make sure to delete
    # all future pending ScheduledLessons that are created
    DAYS_OF_WEEK = (
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    )

    first_name = models.CharField(max_length=47)
    last_name = models.CharField(max_length=47)
    contact_email = models.EmailField(max_length=75)

    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=9, choices=DAYS_OF_WEEK)

    period = models.IntegerField(default=1)  # how many weeks apart are lessons?
    active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)  # trial lesson yet to be scheduled
    is_held = models.BooleanField(default=False)  # trial lesson that's scheduled
    rate = models.DecimalField(decimal_places=2, max_digits=5)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def date_in_timeslot(self, date):
        # Checks that the date does in fact fit in the timeslot
        date = date.strftime('%B %d, %Y')
        dates = self.get_lesson_dates()
        return date in dates

    def get_lesson_dates(self, weeks=2, as_str=True):
        '''
        Used to get the lesson dates from day of week
        '''
        # Must give at least a day's notice
        now = datetime.date.today() + datetime.timedelta(days=1)
        found_first_date = False
        first_date = now
        # get the first date that matches the day of the week
        while not found_first_date:
            day_of_week_index = calendar.weekday(
                first_date.year, first_date.month, first_date.day)
            if str(day_of_week_index) == self.day:
                found_first_date = True
                break
            first_date = first_date + datetime.timedelta(days=1)

        dates = []
        for i in range(weeks):
            date = first_date + datetime.timedelta(days=7*i)
            if as_str:
                date = date.strftime('%B %d, %Y')
            dates.append(date)
        return dates

    def get_lesson_dates_in_month(self, month, year):
        '''
        Will be used to generate the scheduledlessons for a student
        Interval represents how many weeks between each lesson
        '''
        first_of_month = datetime.date(month=month, year=year, day=1)
        found_first_date = False
        first_date = first_of_month
        # get the first date that matches the day of the week
        while not found_first_date:
            day_of_week_index = calendar.weekday(
                first_date.year, first_date.month, first_date.day)
            if str(day_of_week_index) == self.day:
                found_first_date = True
                break
            first_date = first_date + datetime.timedelta(days=1)

        date = first_date
        dates_in_month = []
        while date.month == month:
            dates_in_month.append(date)
            # Bug here! if period is anything besides 1, this will give
            # bad results. Putting 2 will cause issues in months after
            # those with 5 weeks
            date = date + datetime.timedelta(days=7*self.period)
        return dates_in_month

    def generate_lessons_for_month(self, month_index, year):
        '''
        Generate the scheduled lessons based on the student's time slot
        for a given month in a year
        '''
        dates = self.get_lesson_dates_in_month(
            month=month_index,
            year=year
        )
        # Check that the month doens't already have scheduled lessons
        if self.scheduledlesson_set.filter(date__in=dates).exists():
            return
        for date in dates:
            ScheduledLesson.objects.create(
                date=date,
                start_time=self.start_time,
                end_time=self.end_time,
                student=self,
                is_trial=False,
            )
        return

    def get_billing_for_month(self, month_index, year):
        if month_index == 1:
            last_month = 12
            last_year = year - 1
        else:
            last_month = month_index - 1
            last_year = year
        last_month_cancels = ScheduledLesson.objects.filter_by_month(
            last_month, last_year
        ).filter(cancelled_on__isnull=False)
        current_lessons = ScheduledLesson.objects.filter_by_month(
            month_index, year
        )
        lessons_to_bill = current_lessons.count() - last_month_cancels.count()
        bill = lessons_to_bill * self.rate
        billing = {
            'cancelled_lessons': last_month_cancels,
            'scheduled_lessons': current_lessons,
            'bill': bill
        }
        return billing
        
    def __unicode__(self):
        return '%s (%s %s - %s)' % (
            self.full_name(), self.get_day_display()[:3],
            self.start_time.strftime('%I:%M%p'), self.end_time.strftime('%I:%M%p')
        )
