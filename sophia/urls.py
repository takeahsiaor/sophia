import views
from ckeditor import urls as ckeditor_urls

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from rest_framework.routers import DefaultRouter

from .sitemap import StaticViewSitemap, BlogSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap
}

router = DefaultRouter()
router.register(r'scheduled_lessons', views.ScheduledLessonViewSet)

urlpatterns = [
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ckeditor/', include(ckeditor_urls)),
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^api/', include(router.urls)),
    url(r'^bio/$', views.BioView.as_view(), name='bio'),
    url(r'^policy/$', views.PolicyView.as_view(), name='policy'),
    url(r'^philosophy/$', views.PhilosophyView.as_view(), name='philosophy'),
    url(r'^testimonials/$', views.TestimonialView.as_view(), name='testimonials'),
    url(r'^contact/$', views.ContactView.as_view(), name='contact'),
    url(r'^schedule-trial-lesson/$', views.ScheduleTrialLessonView.as_view(),
        name='schedule_trial_lesson'),
    url(r'^scheduled-lessons/$',
        login_required(views.ScheduledLessonsView.as_view()),
        name='scheduled_lessons'
    ),
    url(r'^blog/$', views.BlogHome.as_view(), name='blog'),
    url(r'^blog/entry/(?P<post_id>\d+)/$', views.BlogEntry.as_view(), name='blog_entry'),
    url(r'^blog/tag/(?P<tag_id>\d+)/$', views.BlogByTag.as_view(), name='blog_by_tag'),
    url(r'^blog/search/$', views.BlogSearch.as_view(), name='search_blog'),
    url(r'^gallery/$', views.GalleryView.as_view(), name='gallery'),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT})
    ]