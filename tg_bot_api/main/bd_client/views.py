import json
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import calendar
from .models import Client, Trainer , ProgressRecord

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return None

@csrf_exempt
def client_update_profile(request):
    if request.method != 'PUT':
        return HttpResponseBadRequest('Только PUT запрос')
    
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest('Ошибка парсинга JSON')

    tg_id = data.get('tg_id')
    if not tg_id:
        return HttpResponseBadRequest("Отсутствует обязательное поле 'tg_id'.")

    client = get_object_or_404(Client, tg_id=tg_id)

    fullname = data.get('fullname')
    email = data.get('email')

    # Обновляем поля, только если они были предоставлены и не были пропущены
    if fullname is not None and fullname != 'Пропустить':
        client.fullname = fullname
        
    if email is not None and email != 'Пропустить':
        client.email = email
    
    client.save()

    # Возвращаем обновленные данные
    return JsonResponse({
        'status': 'success',
        'message': 'Профиль клиента обновлен.',
        'data': {
            'tg_id': str(client.tg_id),
            'fullname': client.fullname or None,
            'username': client.username,
            'email': client.email or None,
        }
    }, status=200)

    
@csrf_exempt
def client_link_trainer(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST запрос')
    
    data = parse_json(request)
    client_tg_id = data.get('client_tg_id')
    link_code = data.get('code')

    if not client_tg_id or not link_code:
        return HttpResponseBadRequest("Missing client_tg_id or code.")

    # 1. Находим тренера по введенному коду
    try:
        trainer = Trainer.objects.get(link_code=link_code)
    except Trainer.DoesNotExist:
        return HttpResponseBadRequest("Invalid link code.")

    # 2. Находим клиента
    client = get_object_or_404(Client, tg_id=client_tg_id)

    # 3. Привязываем клиента к тренеру и сохраняем
    client.trainer = trainer
    client.save()

    return JsonResponse({'status': 'success', 'message': f'Linked to trainer {trainer.username}'})


@csrf_exempt
def client_progress_report(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")

    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest("Invalid JSON data.")

    tg_id = data.get('tg_id')
    weight = data.get('weight')
    calories = data.get('calories')

    if not tg_id:
        return HttpResponseBadRequest("Missing 'tg_id' in request data.")

    client = get_object_or_404(Client, tg_id=tg_id)

    today = timezone.now().date()
    progress_record, created = ProgressRecord.objects.get_or_create(
        client=client,
        date=today,
        defaults={'weight': weight, 'calories_consumed': calories}
    )

    if not created:
        if weight is not None:
            progress_record.weight = weight
        if calories is not None:
            progress_record.calories_consumed = calories
        progress_record.save()

    response_data = {
        "status": "success",
        "message": "Progress record created." if created else "Progress record updated.",
        "data": {
            "client_tg_id": client.tg_id,
            "date": progress_record.date.strftime('%Y-%m-%d'),
            "weight": str(progress_record.weight) if progress_record.weight is not None else None,
            "calories_consumed": progress_record.calories_consumed
        }
    }

    return JsonResponse(response_data)
# Напиши какие данные должны быть в входном json для этого метода
# {
#     "tg_id": "string",
#     "weight": "float",
#     "calories": "int"
# }
@csrf_exempt
def get_client_progress(request, tg_id):
    if request.method != 'GET':
        return HttpResponseBadRequest("Invalid request method.")

    client = get_object_or_404(Client, tg_id=tg_id)
    progress_records = ProgressRecord.objects.filter(client=client).order_by('-date')

    records_list = []
    for record in progress_records:
        records_list.append({
            "date": record.date.strftime('%Y-%m-%d'),
            "weight": str(record.weight) if record.weight is not None else None,
            "calories_consumed": record.calories_consumed
        })

    response_data = {
        "status": "success",
        "client_tg_id": client.tg_id,
        "progress_records": records_list
    }

    return JsonResponse(response_data)
@csrf_exempt
def get_monthly_progress_summary(request, tg_id, year, month):
    if request.method != 'GET':
        return HttpResponseBadRequest("Invalid request method.")

    client = get_object_or_404(Client, tg_id=tg_id)

    try:
        year = int(year)
        month = int(month)
        _, num_days = calendar.monthrange(year, month)
    except ValueError:
        return HttpResponseBadRequest("Invalid year or month.")

    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, num_days).date()

    progress_records = ProgressRecord.objects.filter(
        client=client,
        date__range=(start_date, end_date)
    ).order_by('date')

    records_list = []
    for record in progress_records:
        records_list.append({
            "date": record.date.strftime('%Y-%m-%d'),
            "weight": str(record.weight) if record.weight is not None else None,
            "calories_consumed": record.calories_consumed
        })

    response_data = {
        "status": "success",
        "client_tg_id": client.tg_id,
        "month": month,
        "year": year,
        "progress_records": records_list
    }

    return JsonResponse(response_data)
@csrf_exempt
def delete_progress_record(request, tg_id, date_str):
    if request.method != 'DELETE':
        return HttpResponseBadRequest("Invalid request method.")

    client = get_object_or_404(Client, tg_id=tg_id)

    try:
        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")

    progress_record = ProgressRecord.objects.filter(client=client, date=record_date).first()
    if not progress_record:
        return HttpResponseBadRequest("Progress record not found for the given date.")

    progress_record.delete()

    response_data = {
        "status": "success",
        "message": f"Progress record for {date_str} deleted."
    }

    return JsonResponse(response_data)
@csrf_exempt
def list_clients(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Invalid request method.")

    clients = Client.objects.all()
    clients_list = []
    for client in clients:
        clients_list.append({
            "tg_id": client.tg_id,
            "fullname": client.fullname,
            "username": client.username,
            "email": client.email
        })

    response_data = {
        "status": "success",
        "clients": clients_list
    }

    return JsonResponse(response_data)
@csrf_exempt
def register_client(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method.")
    
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest("Invalid JSON data.")

    # Получаем данные. Необязательные поля могут быть None.
    tg_id = data.get('tg_id')
    username = data.get('username')
    fullname = data.get('fullname') # Это поле теперь необязательное
    email = data.get('email')     # Это поле теперь необязательное
    

    # !!! Проверка ТОЛЬКО обязательных полей: tg_id и username
    if not tg_id or not username:
        # Убеждаемся, что tg_id - это число, если нужно (Django Model CharField/IntegerField handles this)
        return HttpResponseBadRequest("Missing required fields 'tg_id' or 'username'.")

    # Используем get_or_create только с обязательными полями (tg_id)
    # Остальные поля передаем как defaults для случая создания объекта
    client, created = Client.objects.get_or_create(
        tg_id=tg_id,
        defaults={
            'username': username,
            'fullname': fullname or '', # Устанавливаем пустую строку, если None (если модель не допускает NULL)
            'email': email or ''        # Устанавливаем пустую строку, если None
        }
    )

    # Если объект существовал, мы хотим обновить его необязательные поля, 
    # если они были предоставлены в текущем запросе
    if not created:
        # Обновляем обязательное поле username (на случай, если пользователь сменил его в ТГ)
        client.username = username 
        
        # Обновляем необязательные поля, только если они пришли в запросе
        # (или если вы хотите обновить их на None, если они пришли пустыми)
        client.fullname = fullname or client.fullname or ''
        client.email = email or client.email or ''
        
        client.save()

    response_data = {
        "status": "success",
        "message": "Client registered." if created else "Client updated.",
        "data": {
            "tg_id": client.tg_id,
            "fullname": client.fullname or None, # Возвращаем как None в JSON, если пусто
            "username": client.username,
            "email": client.email or None       # Возвращаем как None в JSON, если пусто
        }
    }

    # Убедитесь, что вы импортировали JsonResponse
    from django.http import JsonResponse
    return JsonResponse(response_data, status=201 if created else 200)

