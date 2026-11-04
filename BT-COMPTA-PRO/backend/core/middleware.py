"""En-têtes de sécurité HTTP ajoutés à toutes les réponses de l'API."""

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
PERMISSIONS_POLICY = 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()'


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        if request.path.startswith('/api/'):
            # Les réponses JSON ne doivent jamais être interprétées comme une page ni mises en cache partagé.
            response.setdefault('Content-Security-Policy', API_CSP)
            response.setdefault('Cache-Control', 'no-store')
            response.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        return response
