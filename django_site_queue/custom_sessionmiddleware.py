from django.conf import settings

class DisableSessionMiddleware:
    def __init__(self, get_response):
        print ("DISABLED")
        print (get_response)
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if the current path matches the one you want to be "session-less"
        # Example: disable sessions for the /api/status/ path
        remove_cookies_urls = ['/site-queue/max-threshold/parkstayv2/','/site-queue/service-restricted/','/site-queue/view/','/site-queue/waiting-room/parkstayv2/']

        if request.path in remove_cookies_urls:
            # response.delete_cookie sets the cookie's expiry to the past
            response.delete_cookie(
                settings.SESSION_COOKIE_NAME, 
                domain=settings.SESSION_COOKIE_DOMAIN,
                path=settings.SESSION_COOKIE_PATH
            )
            if 'sessionid' in response.cookies:
                del response.cookies['sessionid']
       
            response.cookies['Vary'] = "Origin"

        return response
   