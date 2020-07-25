import datetime

from django import forms
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from sophia.models import Student
from sophia.utils import is_recaptcha_valid


class ContactForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100,
                                required=True,
                                widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(label='Email', max_length=100,
                                  required=True,
                                  widget=forms.TextInput(attrs={'class':'form-control'}))
    subject = forms.CharField(label='Subject', max_length=100,
                                widget=forms.TextInput(attrs={'class':'form-control'}))
    message = forms.CharField(label='Message', required=True,
                                widget=forms.Textarea(attrs={'class':'form-control'}))
    copy_email = forms.BooleanField(label="Send a copy to my email address",
        widget=forms.CheckboxInput(attrs={'class':'form-control'}),
        required=False
    )
    def clean(self):
        cleaned_data = super(ContactForm, self).clean()
        # Validate recaptcha
        if not is_recaptcha_valid(self.data):
            raise forms.ValidationError(
                'Failed reCAPTCHA validation. Please try again!'
            )
        return cleaned_data


    def send_contact_email(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        subject = self.cleaned_data.get('subject', 'No Subject')

        message = self.cleaned_data['message']
        send_copy = self.cleaned_data['copy_email']
        subject_str = "Message submitted to Sophia Hsiao Studio: %s" % subject
        context = {'name':name, 'email': email,
                    'message':message}
        body = render_to_string('contact_email_template.html', context)

        if send_copy:
            copy_body = render_to_string('contact_email_copy.html', context)
            send_mail(subject_str, copy_body, settings.DEFAULT_FROM_EMAIL,
                     [email], fail_silently=False)

        send_mail(subject_str, body, settings.DEFAULT_FROM_EMAIL,
                 settings.EMAIL_RECIPIENTS, fail_silently=False)

class ScheduleLessonForm(forms.Form):
    start_string = forms.CharField(required=True, widget=forms.HiddenInput())
    end_string = forms.CharField(required=True, widget=forms.HiddenInput())
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(active=True, is_trial=False),
        required=True,
    )

class ScheduleTrialLessonForm(forms.Form):
    date = forms.CharField(required=True, widget=forms.HiddenInput())
    student_pk = forms.IntegerField(required=True, widget=forms.HiddenInput())
    # Didn't want to have to have these three but need it for js population
    # of description of selection in modal
    start_time = forms.CharField(required=True, widget=forms.HiddenInput())
    end_time = forms.CharField(required=True, widget=forms.HiddenInput())
    day = forms.CharField(required=True, widget=forms.HiddenInput())

    student_name = forms.CharField(
        label="Student's Name",
        max_length=100,
        required=True, 
        widget=forms.TextInput(
            attrs={'class':'form-control', 'placeholder':'First and Last Name'}
        )
    )
    email = forms.EmailField(label='Email', max_length=100,
        required=True, widget=forms.TextInput(
            attrs={'class':'form-control', 'placeholder': 'example@example.com'}
        )
    )
    phone = forms.CharField(label="Phone", required=True,
        widget=forms.TextInput(
            attrs={'class':'form-control', 'placeholder': 'XXX-XXX-XXXX'}
        )
    )
    age = forms.CharField(label="Student Age", required=True,)
    own_violin = forms.BooleanField(
        required=False,
        label="Check if you currently have a violin to use",
        widget=forms.CheckboxInput(attrs={}))
    comments = forms.CharField(
        label='Additional Info',
        required=False,
        widget=forms.Textarea(
            attrs={'class':'form-control',
            'placeholder': "Is there anything else you'd like us to know?"}
        )
    )

    def send_notification(self):
        student_name = self.cleaned_data['student_name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone']
        age = self.cleaned_data['age']
        own_violin = self.cleaned_data['own_violin']
        comments = self.cleaned_data.get('comments', '')
        student = self.cleaned_data['student']
        date = self.cleaned_data['date']
        day = student.get_day_display()

        subject_str = "Trial lesson scheduled for %s, %s" % (
            day, date.strftime('%B %d, %Y')
        )
        context = {'student_name':student_name, 'email':email, 'phone':phone,
                    'age':age, 'own_violin':own_violin, 'comments':comments,
                    'date':date, 'student':student, 'day': day}
        body = render_to_string(
            'schedule_lesson_notification_email.html', context)

        recipients = settings.EMAIL_RECIPIENTS

        send_mail(subject_str, body, settings.DEFAULT_FROM_EMAIL,
                 recipients, fail_silently=False)

    def clean_date(self):
        # convert string to date object
        date_str = self.data['date']
        date_time = datetime.datetime.strptime(date_str, '%B %d, %Y')
        date = date_time.date()
        return date


    def clean(self):
        cleaned_data = super(ScheduleTrialLessonForm, self).clean()
        # Validate recaptcha
        if not is_recaptcha_valid(self.data):
            raise forms.ValidationError(
                'Failed reCAPTCHA validation. Please try again!'
            )

        # Make sure that the date and timeslot are valid
        date = cleaned_data['date']
        student_pk = cleaned_data['student_pk']

        students = Student.objects.filter(
            pk=student_pk, is_trial=True, is_held=False
        )
        # student obj doesn't exist
        if not students:
            raise forms.ValidationError("Sorry! Someone else just snapped up"
                " that spot. Please pick a new one and try again")

        # ensure that the timeslot and date match up and weren't tampered with
        student = students[0]
        if not student.date_in_timeslot(date):
            raise forms.ValidationError("Sorry! Something went wrong. Please "
                "select a new time and try again")

        # Add the students object to the cleaned data
        cleaned_data['student'] = student

        return cleaned_data

