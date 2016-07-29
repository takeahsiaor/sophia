import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.views.generic import TemplateView, FormView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from sophia.forms import ContactForm, ScheduleTrialLessonForm
from sophia.models import (
    ScheduledLesson,
    Testimonial,
    Timeslot,
    BlogPost,
    BlogTag,
)

def paginate(request, queryset, num_per_page):
    paginator = Paginator(queryset, num_per_page)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    return queryset


# Create your views here.
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # do some smarter filtering here later
        testimonials = Testimonial.objects.all()
        context['testimonials'] = testimonials
        return context


class BioView(TemplateView):
    template_name = 'bio.html'


class PolicyView(TemplateView):
    template_name = 'policy.html'


class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        form.send_contact_email()
        success_message = "Thanks for submitting your message!"
        messages.success(self.request, success_message)
        return super(ContactView, self).form_valid(form)


class ScheduleTrialLessonView(FormView):
    template_name = 'schedule_trial_lesson.html'
    form_class = ScheduleTrialLessonForm
    success_url = reverse_lazy('schedule_trial_lesson')

    COLOR_CLASSES = {
        'Monday': 'u',
        'Tuesday': 'sea',
        'Wednesday': 'blue',
        'Thursday': 'orange',
        'Friday': 'purple',
        'Saturday': 'dark-blue',
        'Sunday': 'dark'
    }

    def form_valid(self, form):
        success_message = """Thank you for scheduling your free lesson! We will
            be in touch with you shortly!"""
        timeslot = form.cleaned_data['timeslot']
        ScheduledLesson.objects.create(
            date=form.cleaned_data['date'],
            timeslot=timeslot
        )
        timeslot.available = False
        timeslot.save()
        form.send_notification()
        messages.success(self.request, success_message)

        return super(ScheduleTrialLessonView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ScheduleTrialLessonView, self).get_context_data(**kwargs)
        timeslots = Timeslot.objects.filter(available=True).order_by('start_time')
        trial_lessons = []
        for timeslot in timeslots:
            lesson_dates = timeslot.get_lesson_dates()
            trial_lessons.append(
                {
                    'timeslot':timeslot, 
                    'lesson_dates': lesson_dates,
                    'color_class': self.COLOR_CLASSES[timeslot.day]
                }
            )
        context['trial_lessons'] = trial_lessons

        return context


class PhilosophyView(TemplateView):
    template_name = 'philosophy.html'
    # include video?


# class FAQView(TemplateView):
#     template_name = 'faq.html'


class TestimonialView(TemplateView):
    template_name = 'testimonials.html'

    def get_context_data(self, **kwargs):
        context = super(TestimonialView, self).get_context_data(**kwargs)
        context['testimonials'] = Testimonial.objects.all()
        return context
        

class GalleryView(TemplateView):
    template_name = 'gallery.html'


def get_archive_post_list():
    all_posts = BlogPost.objects.all().order_by('-created_on')
    #need list to preserve order for template generation
    #archive will be of the form [[year,month,num_posts], ....]
    #want dictionary to do quick lookup if year-month combination exists
    #archive_contents of the form {(year,month):index_in_archive...}
    #over_two_years_ago of the form [[year, num_posts]] to limit
    #listing in archive posts sidebar
    archive_contents = {}
    archive = []
    current_year = datetime.datetime.now().year
    first_day_last_year = datetime.date(current_year-1, 1, 1)
    posts_over_two_years = all_posts.filter(
                                created_on__lt=first_day_last_year).values_list(
                                    'created_on', flat=True)
    #for posts over two years ago, only break down by year
    over_two_years_ago = []
    year_contents ={}
    for post_date in posts_over_two_years:
        year = post_date.year
        if year in year_contents:
            index = year_contents.get(year)
            over_two_years_ago[index][1] +=1
        else:
            over_two_years_ago.append([year, 1])
            index = len(over_two_years_ago) -1
            year_contents[year] = index

    #for posts in hte last two years, break it down by months
    posts_last_two_years = all_posts.filter(
                                created_on__gte=first_day_last_year).values_list(
                                    'created_on', flat=True)
    # archived_post_dates = all_posts.values_list('created_on', flat=True)

    for post_date in posts_last_two_years:
        year = post_date.year
        month = post_date.strftime("%B") #format month as name instead of int
        month_ordinal = post_date.month
        #if the year-month combo is already in the list
        #increment num_posts
        if (year, month) in archive_contents:
            index = archive_contents.get((year,month))
            archive[index][3] += 1
        else:
            #otherwise initialize in list and add year-month combo
            #to dictionary with value as index in archive list
            archive.append([year, month, month_ordinal, 1])
            index = len(archive) - 1
            archive_contents[(year,month)] = index
    return archive, over_two_years_ago


class Blog(TemplateView):
    #all blog pages subclass from this
    #supplement get_context_data making sure to call super()
    # override template_name
    def paginate_blog(self, posts_queryset, num_per_page=5):
        """
        Pass in the queryset of posts you want
        Returns pagination
        Pass in num_per_page to defined how many posts per page
        """
        posts = paginate(self.request, posts_queryset, num_per_page)
        return posts

    def get_context_data(self):
        most_recent_posts = BlogPost.objects.all().order_by('-created_on')[:5]
        tags = BlogTag.objects.all().order_by('name') 

        monthly_archive, yearly_archive = get_archive_post_list()

        context = {'monthly_archive': monthly_archive,
                   'yearly_archive': yearly_archive,
                   'most_recent_posts': most_recent_posts,
                   'tags':tags
                   }
        return context


class BlogHome(Blog):
    template_name = 'blog.html'

    def get_context_data(self):
        context = super(BlogHome, self).get_context_data()
        all_posts = BlogPost.objects.all().order_by('-created_on')
        posts = self.paginate_blog(all_posts)
        context.update({'posts':posts, 
                        'page_title':'From the desk of Living Hope'})
        return context


class BlogByTag(Blog):
    template_name = 'blog.html'

    def get_context_data(self, **kwargs):
        context = super(BlogByTag, self).get_context_data()
        tag_id = kwargs.get('tag_id')
        tag = get_object_or_404(BlogTag, id=tag_id)
        posts = BlogPost.objects.filter(tags=tag).order_by('-created_on')
        posts = self.paginate_blog(posts)
        page_title = 'Posts tagged with %s' % tag
        unique_context = {'page_title':page_title,
                          'posts':posts,
                          'tag': tag}
        context.update(unique_context)
        return context  


class BlogSearch(Blog):
    template_name = 'blog.html'

    def get_context_data(self):
        context = super(BlogSearch, self).get_context_data()
        #when given as a url param, in request
        #when parsed from the url itself, then in kwargs
        query = self.request.GET.get('query')
        by_content = Q(content__icontains=query)
        by_title = Q(title__icontains=query)
        #ordering??
        posts = BlogPost.objects.filter(by_content|by_title)
        posts = self.paginate_blog(posts)
        page_title = 'Resulting Posts for "%s"' % query
        unique_context = {'page_title':page_title,
                          'posts':posts}
        context.update(unique_context)
        return context


class BlogEntry(Blog):
    # this is the only one that can have a unique template
    template_name = 'blog_post.html'

    def get_context_data(self, **kwargs):
        context = super(BlogEntry, self).get_context_data()
        post_id = kwargs.get('post_id')
        post = get_object_or_404(BlogPost,id=post_id)
        #consider putting these also as methods
        try:
            previous_post_id = post.get_previous_by_created_on().id
        except:
            previous_post_id = None
        try:
            next_post_id = post.get_next_by_created_on().id
        except:
            next_post_id = None        

        unique_context = {'next_post_id':next_post_id,
                          'post':post,
                          'previous_post_id':previous_post_id}
        context.update(unique_context)
        return context