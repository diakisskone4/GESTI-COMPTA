from rest_framework.exceptions import ValidationError


def int_param(request, name):
    """Lit un identifiant numérique dans l'URL ; renvoie None s'il est absent, une erreur 400 s'il est invalide."""
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    if not str(value).isdigit() or len(str(value)) > 18:
        raise ValidationError({name: 'Identifiant invalide.'})
    return int(value)
