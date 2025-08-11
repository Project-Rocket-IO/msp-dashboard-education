from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate_queryset(queryset, page_number, per_page=10):
    paginator = Paginator(queryset, per_page)
    
    try:
        paginated_items = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = paginator.page(paginator.num_pages)
    
    return paginated_items, paginator