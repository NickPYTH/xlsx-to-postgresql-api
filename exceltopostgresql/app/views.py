from rest_framework.decorators import api_view
from django.http import JsonResponse

@api_view(['POST'])
def convert(request):
    body = request.data['body']
    return JsonResponse({'status': 'success'})
