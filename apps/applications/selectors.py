from django.db.models import Q


def filter_applications(queryset, filters):
    q = filters.get('q')
    if q:
        queryset = queryset.filter(
            Q(applicant_full_name__icontains=q) | Q(applicant_email__icontains=q)
        )
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])
    if filters.get('district'):
        queryset = queryset.filter(district=filters['district'])
    if filters.get('volunteer'):
        queryset = queryset.filter(assigned_volunteer=filters['volunteer'])
    if filters.get('date_from'):
        queryset = queryset.filter(created_at__date__gte=filters['date_from'])
    if filters.get('date_to'):
        queryset = queryset.filter(created_at__date__lte=filters['date_to'])
    return queryset

