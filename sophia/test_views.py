import datetime
import json
from django.core.urlresolvers import reverse
from django.test import TestCase
from sophia.models import Student, ScheduledLesson

# Create your tests here.

class TestScheduledLessonsAPI(TestCase):
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
        self.start_date = datetime.date.today()
        self.end_date = self.start_date + datetime.timedelta(days=7)
        self.url = reverse('scheduled_lessons_api')

    def create_lesson(self):
        start = datetime.datetime(month=11, day=20, year=2016)
        end = start + datetime.timedelta(minutes=30)
        return ScheduledLesson.objects.create(
            date=start.date(),
            start_time=start.time(),
            end_time=end.time(),
            student=self.student,
        )

    def assert_no_lessons(self):
        response = self.client.get(
            self.url,
            {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            }
        )
        results = json.loads(response.content)
        self.assertEqual(results, [])

    def test_get(self):
        self.assert_no_lessons()
        # Create some scheduled lessons
        self.student.generate_lessons_for_month(
            self.start_date.month, self.start_date.year
        )
        response = self.client.get(
            self.url,
            {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            }
        )
        results = json.loads(response.content)
        self.assertEqual(len(results), 1)

    def test_create(self):
        self.assert_no_lessons()
        start = datetime.datetime.now()
        start = start.replace(microsecond=0)
        end = start + datetime.timedelta(minutes=30)

        response = self.client.post(
            self.url,
            {
                'start_string': start.isoformat(),
                'end_string': end.isoformat(),
                'student': self.student.pk,
                'action': 'create'
            }
        )
        lesson = ScheduledLesson.objects.first()
        self.assertEqual(lesson.date, start.date())
        self.assertEqual(lesson.start_time, start.time())
        self.assertEqual(lesson.end_time, end.time())
        self.assertEqual(self.student, lesson.student)
        self.assertFalse(lesson.is_trial)
        self.assertTrue(lesson.is_reschedule)
        self.assertFalse(lesson.completed_on)
        self.assertFalse(lesson.cancelled_on)
        self.assertFalse(lesson.rescheduled_on)
    
    def test_generate(self):
        '''
        Make sure that this generates the lessons for all months touched by
        the start date, end date, and every one in between.
        If start is 11/29 and end is 1/03, this should create lessons for 11, 12,
        and 1
        '''
        self.student2 = Student.objects.create(
            first_name='first2',
            last_name='last2',
            contact_email='first2@last.com',
            start_time=datetime.time(hour=9),
            end_time=datetime.time(hour=10),
            day='0',
            period=1,
            active=True,
            is_trial=False,
            is_held=False,
            rate=30
        )
        self.assert_no_lessons()
        start_date = datetime.date(month=11, day=29, year=2016)
        end_date = datetime.date(month=1, day=3, year=2017)
        response = self.client.post(
            self.url,
            {
                'start_string': start_date.isoformat(),
                'end_string': end_date.isoformat(),
                'action': 'generate'
            }
        )
        self.assertEqual(Student.objects.count(), 2)
        # 4 mondays in Nov, 4 mondays in Dec, 5 mondays in Jan = 13 weeks
        # X2 students should have 26 lessons
        self.assertEqual(ScheduledLesson.objects.count(), 26)

        # The first monday should be 11/7/2016
        date = datetime.date(month=11, day=7, year=2016)
        cutoff_date = datetime.date(month=2, day=1, year=2017)
        student_start_times = Student.objects.all().values_list('start_time', flat=True)
        student_end_times = Student.objects.all().values_list('end_time', flat=True)
        while date < cutoff_date:
            start_times = set(student_start_times)
            end_times = set(student_end_times)
            lessons = ScheduledLesson.objects.filter(date=date)
            for lesson in lessons:
                self.assertFalse(lesson.completed_on)
                self.assertFalse(lesson.cancelled_on)
                self.assertFalse(lesson.rescheduled_on)
                self.assertFalse(lesson.is_trial)
                self.assertFalse(lesson.is_reschedule)
                self.assertIn(lesson.start_time, start_times)
                self.assertIn(lesson.end_time, end_times)
                start_times.remove(lesson.start_time)
                end_times.remove(lesson.end_time)
            date = date + datetime.timedelta(days=7)

    def test_complete(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.completed_on)
        response = self.client.post(
            self.url,
            {
                'action': 'complete',
                'pk': lesson.pk
            }
        )
        lesson.refresh_from_db()
        self.assertTrue(lesson.completed_on)

    def test_cancel(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.cancelled_on)
        response = self.client.post(
            self.url,
            {
                'action': 'cancel',
                'pk': lesson.pk
            }
        )
        lesson.refresh_from_db()
        self.assertTrue(lesson.cancelled_on)

    def test_reschedule(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.rescheduled_on)
        response = self.client.post(
            self.url,
            {
                'action': 'reschedule',
                'pk': lesson.pk
            }
        )
        lesson.refresh_from_db()
        self.assertTrue(lesson.rescheduled_on)

    def test_update_times(self):
        lesson = self.create_lesson()
        date = lesson.date
        start_dt = datetime.datetime.combine(date, lesson.start_time)
        end_dt = datetime.datetime.combine(date, lesson.end_time)
        # Shift time ahead an hour and extend the lesson by 30 minutes
        new_start = start_dt + datetime.timedelta(hours=1)
        new_end = end_dt + datetime.timedelta(hours=1, minutes=30)

        response = self.client.post(
            self.url,
            {
                'action': 'reschedule',
                'pk': lesson.pk,
                'start_string': new_start.isoformat(),
                'end_string': new_end.isoformat()
            }
        )
        lesson.refresh_from_db()
        self.assertEqual(lesson.date, date)
        self.assertEqual(lesson.start_time, start_dt.time())
        self.assertEqual(lesson.end_time, end_dt.time())

    def test_delete(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.is_reschedule)
        response = self.client.post(
            self.url,
            {
                'action': 'delete',
                'pk': lesson.pk
            }
        )
        # Lesson didn't get deleted because it's not a reschedule one
        self.assertTrue(ScheduledLesson.objects.exists())

        # Now change the lesson to be a reschedule one and we should be able
        # to delete it
        lesson.is_reschedule = True
        lesson.save()
        self.assertFalse(lesson.rescheduled_on)
        response = self.client.post(
            self.url,
            {
                'action': 'delete',
                'pk': lesson.pk
            }
        )
        self.assertFalse(ScheduledLesson.objects.exists())