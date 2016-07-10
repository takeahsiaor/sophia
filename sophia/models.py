import datetime, calendar
from django.db import models
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
    #this is where to put my method to calculate aspect ratio


class SmartImageField(ImageField):
    """
    An extremely thin wrapping around ImageField simply adding
    a hook into determining if an image should be displayed
    in landscape or portrait
    """
    attr_class = SmartImageFieldFile


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
    tags = models.ManyToManyField(BlogTag, blank=True, null=True)
    content = RichTextField()

    def clean(self):
        #remove <p>&nbsp;</p> from manuscripts
        self.content = self.content.replace('<p>&nbsp;</p>', '')
        super(BlogPost, self).clean()


class Testimonial(models.Model):
    client_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
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

class Timeslot(models.Model):
    """
    Represents a weekly available timeslot open to a new student
    Kept general to day of week and time but not date

    Need to distinguish between different "taken" slots.
    A slot can be taken by a free one time lesson. Scheduled lessons therefore
    should not be displayed to potential students

    Also can be taken by a weekly lesson. Scheduled lessons should not be
    shown to potential students but they should be shown to admin for current
    full time students

    This is facilitated by checking the scheduledlesson_set for the is_trial 
    flag on future ScheduledLesson objects
    """
    DAYS_OF_WEEK = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=9, choices=DAYS_OF_WEEK)
    available = models.BooleanField(default=True)

    def get_lesson_dates(self, weeks=2):
        # Must give at least a day's notice
        now = datetime.date.today() + datetime.timedelta(days=1)
        found_first_date = False
        first_date = now
        # get the first date that matches the day of the week
        while not found_first_date:
            day_of_week_index = calendar.weekday(
                first_date.year, first_date.month, first_date.day)
            day_abbrev = self.DAYS_OF_WEEK[day_of_week_index][0]
            if day_abbrev == self.day:
                found_first_date = True
                break
            first_date = first_date + datetime.timedelta(days=1)

        dates = []
        for i in range(1, weeks+1):
            date = first_date + datetime.timedelta(days=7*i)
            dates.append(date)
        return dates

    def date_in_timeslot(self, date):
        # Checks that the date does in fact fit in the timeslot
        dates = self.get_lesson_dates()
        return date in dates

    def __unicode__(self):
        return '%s from %s to %s' % (self.day, self.start_time, self.end_time)

class ScheduledLesson(models.Model):
    """
    Represents the actual weekly instance of a lesson.
    Should be created programmatically via timeslot for each given week

    Unpersisted versions are presented to the user and only given a pk when
    a user schedules.

    If is_trial, Timeslot availability should be changed to False.

    Alternative is to always maintain timeslot available flag manually. Up
    to us then to make it available if a trial lesson isn't converted to a full
    time student
    """
    date = models.DateField()
    timeslot = models.ForeignKey('Timeslot')
    is_trial = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s, %s' % (self.date, self.timeslot)