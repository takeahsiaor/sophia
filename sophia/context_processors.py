from sophia.models import BlogPost

def recent_posts(request):
    recent_posts = BlogPost.objects.all().order_by('-created_on')[:3]
    return {'recent_posts': recent_posts}