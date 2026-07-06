import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)
HCAPTCHA_VERIFY_URL = 'https://api.hcaptcha.com/siteverify'


def verify_captcha(token, remote_ip=None):
    if not settings.CAPTCHA_ENABLED:
        return True
    if not token:
        return False

    payload = {
        'secret': settings.CAPTCHA_SECRET_KEY,
        'response': token,
        'sitekey': settings.CAPTCHA_SITE_KEY,
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    request = Request(
        HCAPTCHA_VERIFY_URL,
        data=urlencode(payload).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode())
    except (URLError, TimeoutError, ValueError) as error:
        logger.warning('hCaptcha verification failed: %s', error)
        return False
    return result.get('success') is True
