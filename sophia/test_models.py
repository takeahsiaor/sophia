import datetime

from django.test import TestCase
from sophia.models import Student, ScheduledLesson

# Create your tests here.
class TestStudent(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name='first',
            last_name='last',
            contact_email='first@last.com',
            start_time=datetime.time(hour=10),
            end_time=datetime.time(hour=11),
            day='0',
            period=1,
            active=True,
            is_trial=False,
            is_held=False,
            rate=30
		)

        # Lesson dates start from 24 hours from now
        day = datetime.date.today() + datetime.timedelta(days=1)
        self.day_1 = day + datetime.timedelta(
            (int(self.student.day) - day.weekday()) % 7
        )
        self.day_2 = self.day_1 + datetime.timedelta(days=7)
        self.day_3 = self.day_2 + datetime.timedelta(days=7)

    def test_get_lesson_dates(self):
        # By default, method gets the next two dates
        self.assertTrue(
            self.day_1 in self.student.get_lesson_dates(as_str=False)
        )
        self.assertTrue(
            self.day_2 in self.student.get_lesson_dates(as_str=False)
        )
        self.assertFalse(
            self.day_3 in self.student.get_lesson_dates(as_str=False)
        )

        # Change to get 3 weeks of dates
        self.assertTrue(
            self.day_3 in self.student.get_lesson_dates(weeks=3, as_str=False)
        )

        # Make sure we can get the date as str (default)
        self.assertEqual(
            self.day_1.strftime('%B %d, %Y'),
            self.student.get_lesson_dates()[0]
        )

    def test_date_in_timeslot(self):
        # Wrong day
        wrong_day = self.day_1 + datetime.timedelta(days=1)
        self.assertFalse(self.student.date_in_timeslot(wrong_day))

        # Correct day but in the past
        past_day = self.day_1 - datetime.timedelta(days=7)
        self.assertFalse(self.student.date_in_timeslot(past_day))

        # Correct everything
        self.assertTrue(self.student.date_in_timeslot(self.day_1))

    def test_get_lesson_dates_in_month(self):
        '''
        Ensures that the method returns all the correct days of the month
        For instance, if the student is scheduled on mondays, this should
        return all the mondays of a given month
        '''
        mondays = [
            datetime.date(month=1, day=2, year=2017),
            datetime.date(month=1, day=9, year=2017),
            datetime.date(month=1, day=16, year=2017),
            datetime.date(month=1, day=23, year=2017),
            datetime.date(month=1, day=30, year=2017),
        ]
        self.assertEqual(
            self.student.get_lesson_dates_in_month(month=1, year=2017),
            mondays
        )

    def test_generate_lessons_for_month(self):
        mondays = [
            datetime.date(month=1, day=2, year=2017),
            datetime.date(month=1, day=9, year=2017),
            datetime.date(month=1, day=16, year=2017),
            datetime.date(month=1, day=23, year=2017),
            datetime.date(month=1, day=30, year=2017),
        ]
        ScheduledLesson.objects.all().delete()
        self.student.generate_lessons_for_month(1, 2017)

        self.assertEqual(ScheduledLesson.objects.count(), 5)
        for date in mondays:
            lesson = ScheduledLesson.objects.get(date=date)
            self.assertEqual(lesson.start_time, self.student.start_time)
            self.assertEqual(lesson.end_time, self.student.end_time)
            self.assertEqual(lesson.student, self.student)
            self.assertFalse(lesson.is_trial)

