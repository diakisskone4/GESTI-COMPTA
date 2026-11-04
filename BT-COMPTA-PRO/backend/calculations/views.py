from django.http import Http404, HttpResponse
from django.utils.text import slugify
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from reports.exports import build_pdf, build_xlsx, calculation_document

from .engines import REGISTRY, CalculationError
from .models import CalculationRecord


def get_calculator(slug):
    calc = REGISTRY.get(slug)
    if calc is None:
        raise Http404('Calculatrice introuvable.')
    return calc


def _inputs_display(calc, data):
    """Liste (libellé, valeur) des saisies simples pour les exports."""
    rows = []
    for f in calc.fields:
        if f.get('type') == 'table':
            continue
        value = data.get(f['name'], f.get('default', ''))
        if f.get('type') == 'select':
            value = next((o['label'] for o in f.get('options', []) if o['value'] == value), value)
        rows.append((f['label'], '' if value is None else str(value)))
    return rows


def _run(calc, data):
    try:
        return calc.run(data), None
    except CalculationError as exc:
        return None, Response({'detail': str(exc), 'field': exc.field_name}, status=status.HTTP_400_BAD_REQUEST)


class CalculatorListView(APIView):
    def get(self, request):
        level = request.query_params.get('level')
        items = [c.meta() for c in REGISTRY.values() if not level or c.level == level]
        return Response(items)


class CalculatorDetailView(APIView):
    def get(self, request, slug):
        return Response(get_calculator(slug).meta())


class CalculatorRunView(APIView):
    throttle_classes = [UserRateThrottle, ScopedRateThrottle]
    throttle_scope = 'calculations'

    def post(self, request, slug):
        calc = get_calculator(slug)
        data = request.data.get('inputs', request.data) if isinstance(request.data, dict) else {}
        output, error = _run(calc, data)
        if error:
            return error
        if request.data.get('save') is True:
            CalculationRecord.objects.create(
                user=request.user, slug=slug, title=calc.title, inputs=data,
                summary=[{'label': r['label'], 'value': r['value']} for r in output['results'][:4]])
        return Response({'calculator': calc.meta(), 'output': output})


class CalculatorExportView(APIView):
    throttle_classes = [UserRateThrottle, ScopedRateThrottle]
    throttle_scope = 'exports'

    def post(self, request, slug, fmt):
        calc = get_calculator(slug)
        data = request.data.get('inputs', request.data) if isinstance(request.data, dict) else {}
        output, error = _run(calc, data)
        if error:
            return error
        doc = calculation_document(calc.meta(), _inputs_display(calc, data), output)
        name = slugify(calc.title)[:60] or slug
        if fmt == 'pdf':
            response = HttpResponse(build_pdf(doc), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{name}.pdf"'
        elif fmt == 'xlsx':
            response = HttpResponse(build_xlsx(doc), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{name}.xlsx"'
        else:
            raise Http404('Format inconnu.')
        return response


class CalculationHistoryView(APIView):
    def get(self, request):
        records = CalculationRecord.objects.filter(user=request.user)[:50]
        return Response([{'id': r.id, 'slug': r.slug, 'title': r.title, 'inputs': r.inputs, 'summary': r.summary,
                          'created_at': r.created_at} for r in records])


class CalculationHistoryDeleteView(APIView):
    def delete(self, request, pk):
        deleted, _ = CalculationRecord.objects.filter(user=request.user, pk=pk).delete()
        if not deleted:
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)
