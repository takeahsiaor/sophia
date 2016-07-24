from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from sophia.models import BlogPost

class BlogSitemap(Sitemap):

    def items(self):
        return BlogPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_on

    def location(self, obj):
        return reverse('blog_entry', kwargs={'post_id': obj.pk})

class StaticViewSitemap(Sitemap):

    def items(self):
        return [
            'home', 'bio', 'policy', 'philosophy', 'testimonials', 'contact',
            'schedule_trial_lesson', 'blog'
        ]

    def location(self, item):
        return reverse(item)