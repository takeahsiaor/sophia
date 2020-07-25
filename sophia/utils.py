import requests
from django.conf import settings

def is_recaptcha_valid(post_data):
    """Validates recaptcha with google server
    :param post_data: The datastructure containing the g-recaptcha-response
        from the request POST
    :type post_data: dict
    """
    import ipdb; ipdb.set_trace()
    recaptcha_response = post_data.get('g-recaptcha-response')
    payload = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data=payload
        )
        result = response.json().get('success')
    except Exception:
        result = False

    return result
