import datetime
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from sophia.models import Student, ScheduledLesson
from rest_framework.test import APIClient

# Create your tests here.
class TestScheduleTrialLessonView(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name='Empty',
            last_name='Slot',
            contact_email='trial_slot@test.com',
            start_time=datetime.time(hour=10),
            end_time=datetime.time(hour=11),
            day='0',
            period=1,
            active=True,
            is_trial=True,
            is_held=False,
            rate=30
        )

        self.valid_date = self.student.get_lesson_dates(as_str=False)[0]

        self.valid_data = {
            'date': self.valid_date.strftime('%B %d, %Y'),
            'student_pk': self.student.pk,
            'start_time': self.student.start_time,
            'end_time': self.student.end_time,
            'day': self.student.day,
            'student_name': 'Trial Student',
            'email': 'trial_student@excited.com',
            'phone': '234-234-2345',
            'age': '10',
            'own_violin': False,
            'captcha_0': 'passed',
            'captcha_1': 'passed'
        }

        self.url = reverse('schedule_trial_lesson')
        ScheduledLesson.objects.all().delete()

    def test_get(self):
        '''
        Ensure that only slots that are open are shown
        '''
        response = self.client.get(self.url)
        context = response.context_data
        self.assertEqual(len(context['trial_lessons']), 1)

        # Set the student slot to be a full time student (not trial)
        self.student.is_trial = False
        self.student.save()
        response = self.client.get(self.url)
        context = response.context_data
        self.assertEqual(len(context['trial_lessons']), 0)

        # The student is now a trial student but the slot's already taken
        self.student.is_trial = True
        self.student.is_held = True
        self.student.save()
        response = self.client.get(self.url)
        context = response.context_data
        self.assertEqual(len(context['trial_lessons']), 0)


    def test_successful_post(self):
        self.assertFalse(ScheduledLesson.objects.exists())
        self.assertFalse(self.student.is_held)
        response = self.client.post(
            self.url,
            self.valid_data
        )
        self.assertEqual(response.status_code, 302)

        self.student.refresh_from_db()
        self.assertTrue(self.student.is_held)
        self.assertEqual(ScheduledLesson.objects.count(), 1)
        lesson = ScheduledLesson.objects.get()
        self.assertEqual(lesson.date, self.valid_date)
        self.assertEqual(lesson.student, self.student)
        self.assertEqual(lesson.start_time, self.student.start_time)
        self.assertEqual(lesson.end_time, self.student.end_time)
        self.assertTrue(lesson.is_trial)
        self.assertFalse(lesson.is_reschedule)

    def test_post_past_date(self):
        '''
        Past dates, even if they match the day should not be allowed
        '''
        self.assertFalse(ScheduledLesson.objects.exists())
        self.assertFalse(self.student.is_held)
        invalid_data = self.valid_data
        bad_date = self.valid_date - datetime.timedelta(days=7)
        invalid_data.update({
            'date': bad_date.strftime('%B %d, %Y')
        })
        response = self.client.post(
            self.url,
            invalid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data['form'].errors)

        self.student.refresh_from_db()
        self.assertFalse(ScheduledLesson.objects.exists())
        self.assertFalse(self.student.is_held)

    def test_post_incorrect_day(self):
        '''
        Future dates that do not match the slot day should not be allowed
        '''
        self.assertFalse(ScheduledLesson.objects.exists())
        self.assertFalse(self.student.is_held)
        invalid_data = self.valid_data
        # bad_date is the following tuesday and the slot is on monday
        bad_date = self.valid_date + datetime.timedelta(days=8)
        invalid_data.update({
            'date': bad_date.strftime('%B %d, %Y')
        })
        response = self.client.post(
            self.url,
            invalid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data['form'].errors)

        self.student.refresh_from_db()
        self.assertFalse(ScheduledLesson.objects.exists())
        self.assertFalse(self.student.is_held)

    def test_post_race_condition(self):
        '''
        Test that if two people are trying to schedule the same slot at
        nearly the same time, that one of them gets an error
        '''
        self.assertFalse(ScheduledLesson.objects.exists())

        # Someone snatches up the spot
        self.student.is_held = True
        self.student.save()

        response = self.client.post(
            self.url,
            self.valid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data['form'].errors)
        # No new lesson is created
        self.assertFalse(ScheduledLesson.objects.exists())


class TestScheduledLessonsAPI(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'pass')
        self.client = APIClient()
        self.client.login(username='admin', password='pass')
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
        self.start_date = datetime.date(month=11, day=1, year=2016)
        self.end_date = self.start_date + datetime.timedelta(days=7)
        self.list_url = reverse('scheduledlesson-list')
        self.generate_lessons_url = reverse('scheduledlesson-bulk-generate')

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
            self.list_url,
            {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            }
        )
        results = json.loads(response.content)
        self.assertEqual(results, [])

    def test_get(self):
        # self.assert_no_lessons()
        # Create some scheduled lessons
        self.student.generate_lessons_for_month(
            self.start_date.month, self.start_date.year
        )
        response = self.client.get(
            self.list_url,
            {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            }
        )
        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)
        self.assertEqual(len(results), 1)

    def test_create(self):
        self.assert_no_lessons()
        start = datetime.datetime.now()
        start = start.replace(microsecond=0)
        end = start + datetime.timedelta(minutes=30)

        response = self.client.post(
            self.list_url,
            {
                'start_string': start.isoformat(),
                'end_string': end.isoformat(),
                'student': self.student.pk,
            }
        )
        self.assertEqual(response.status_code, 201)

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
            self.generate_lessons_url,
            {
                'start_string': start_date.isoformat(),
                'end_string': end_date.isoformat(),
            }
        )
        self.assertEqual(response.status_code, 201)
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
        response = self.client.patch(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
            {
                'completed_on': '2016-12-25',
                'rescheduled_on': '',
                'cancelled_on': ''
            }
        )
        self.assertEqual(response.status_code, 202)
        lesson.refresh_from_db()
        self.assertTrue(lesson.completed_on)
        self.assertFalse(lesson.rescheduled_on)
        self.assertFalse(lesson.cancelled_on)

    def test_cancel(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.cancelled_on)
        response = self.client.patch(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
            {
                'completed_on': '',
                'rescheduled_on': '',
                'cancelled_on': '2016-12-25'
            }
        )
        self.assertEqual(response.status_code, 202)
        lesson.refresh_from_db()
        self.assertTrue(lesson.cancelled_on)

    def test_reschedule(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.rescheduled_on)
        response = self.client.patch(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
            {
                'completed_on': '',
                'rescheduled_on': '2016-12-25',
                'cancelled_on': ''
            }
        )
        self.assertEqual(response.status_code, 202)
        lesson.refresh_from_db()
        self.assertTrue(lesson.rescheduled_on)

    def test_clear(self):
        lesson = self.create_lesson()
        now = datetime.datetime.now()
        lesson.rescheduled_on = now
        lesson.cancelled_on = now
        lesson.completed_on = now
        lesson.save()
        response = self.client.patch(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
            {
                'completed_on': '',
                'rescheduled_on': '',
                'cancelled_on': ''
            }
        )
        self.assertEqual(response.status_code, 202)
        lesson.refresh_from_db()
        self.assertFalse(lesson.rescheduled_on)
        self.assertFalse(lesson.cancelled_on)
        self.assertFalse(lesson.completed_on)

    def test_update_times(self):
        lesson = self.create_lesson()
        date = lesson.date
        start_dt = datetime.datetime.combine(date, lesson.start_time)
        end_dt = datetime.datetime.combine(date, lesson.end_time)
        # Shift time ahead an hour and extend the lesson by 30 minutes
        new_start = start_dt + datetime.timedelta(hours=1)
        new_end = end_dt + datetime.timedelta(hours=1, minutes=30)

        response = self.client.patch(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
            {
                'start_string': new_start.isoformat(),
                'end_string': new_end.isoformat()
            }
        )
        self.assertEqual(response.status_code, 202)
        lesson.refresh_from_db()
        self.assertEqual(lesson.date, date)
        self.assertEqual(lesson.start_time, new_start.time())
        self.assertEqual(lesson.end_time, new_end.time())

    def test_delete(self):
        lesson = self.create_lesson()
        self.assertFalse(lesson.is_reschedule)
        response = self.client.delete(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            'Deleting non-reschedule lessons is not allowed'
        )
        # Lesson didn't get deleted because it's not a reschedule one
        self.assertTrue(ScheduledLesson.objects.exists())

        # Now change the lesson to be a reschedule one and we should be able
        # to delete it
        lesson.is_reschedule = True
        lesson.save()
        self.assertFalse(lesson.rescheduled_on)
        response = self.client.delete(
            reverse('scheduledlesson-detail', kwargs={'pk': lesson.pk}),
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ScheduledLesson.objects.exists())