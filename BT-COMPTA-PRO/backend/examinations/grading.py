"""Correction automatique des tentatives."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .models import Question

ZERO = Decimal('0')


def _dec(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value).replace(' ', '').replace(' ', '').replace(',', '.'))
    except InvalidOperation:
        return None


def _normalize_entry(lines):
    """Agrège les lignes par (compte, sens) pour une comparaison indépendante de l'ordre."""
    totals = {}
    for line in lines or []:
        account = str(line.get('account', '')).strip()
        if not account:
            continue
        debit = _dec(line.get('debit')) or ZERO
        credit = _dec(line.get('credit')) or ZERO
        if debit:
            totals[(account, 'D')] = totals.get((account, 'D'), ZERO) + debit
        if credit:
            totals[(account, 'C')] = totals.get((account, 'C'), ZERO) + credit
    return {k: v.quantize(Decimal('0.01')) for k, v in totals.items()}


def grade_question(question: Question, answer):
    """Retourne (points obtenus, correct: bool, réponse attendue lisible)."""
    points = question.points
    if question.kind == Question.Kind.MCQ:
        correct_ids = {c.id for c in question.choices.all() if c.is_correct}
        given = answer if isinstance(answer, list) else [answer]
        given_ids = set()
        for g in given:
            try:
                given_ids.add(int(g))
            except (TypeError, ValueError):
                pass
        ok = given_ids == correct_ids
        expected = ' ; '.join(c.text for c in question.choices.all() if c.is_correct)
        return (points if ok else ZERO), ok, expected
    if question.kind == Question.Kind.NUMERIC:
        value = _dec(answer)
        expected = question.answer_numeric
        ok = value is not None and expected is not None and abs(value - expected) <= question.tolerance
        return (points if ok else ZERO), ok, f'{expected.normalize():f}' if expected is not None else ''
    # Saisie d'écriture : points proportionnels aux lignes justes, pénalité si lignes en trop.
    expected = _normalize_entry(question.expected_entry)
    given = _normalize_entry(answer if isinstance(answer, list) else [])
    if not expected:
        return ZERO, False, ''
    good = sum(1 for k, v in expected.items() if given.get(k) == v)
    extra = sum(1 for k in given if k not in expected)
    ratio = max(ZERO, Decimal(good - extra) / Decimal(len(expected)))
    earned = (points * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    readable = ' ; '.join(f'{acc} {"débit" if side == "D" else "crédit"} {amount:f}' for (acc, side), amount in expected.items())
    return earned, earned == points, readable


def grade_attempt(attempt, answers: dict):
    questions = attempt.quiz.questions.prefetch_related('choices')
    total = earned = ZERO
    details = []
    for q in questions:
        answer = answers.get(str(q.id))
        pts, ok, expected = grade_question(q, answer)
        total += q.points
        earned += pts
        details.append({'question': q.id, 'text': q.text, 'kind': q.kind, 'answer': answer, 'correct': ok,
                        'points': str(pts), 'max_points': str(q.points), 'expected': expected, 'explanation': q.explanation})
    grade = (earned / total * 20).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total else ZERO
    return earned, total, grade, details
