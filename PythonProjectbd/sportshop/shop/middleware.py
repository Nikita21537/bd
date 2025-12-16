class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Код, выполняемый перед view

        response = self.get_response(request)

        # Код, выполняемый после view
        return response