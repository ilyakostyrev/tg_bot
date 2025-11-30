import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import calendar
from .models import Trainer, AvailableSlot
import random
import string
from django.utils.timezone import make_aware 
from bd_client.models import Client, ProgressRecord
import logging
from django.db import transaction
logger = logging.getLogger(__name__)

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return None

# views.py
import logging
import random
import string
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Trainer, AvailableSlot
from bd_client.models import Client

logger = logging.getLogger(__name__)

# -------------------------------
# Утилита: генерация кода
# -------------------------------
def generate_link_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# -------------------------------
# 1. Регистрация
# -------------------------------
@csrf_exempt
def register_trainer(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    username = data.get('username', f"user_{tg_id}")
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    trainer, created = Trainer.objects.get_or_create(
        tg_id=tg_id,
        defaults={'username': username}
    )
    status = 201 if created else 409
    return JsonResponse({'status': 'created' if created else 'exists'}, status=status)

@csrf_exempt
def register_client(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    username = data.get('username', f"user_{tg_id}")
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    client, created = Client.objects.get_or_create(
        tg_id=tg_id,
        defaults={'username': username}
    )
    status = 201 if created else 409
    return JsonResponse({'status': 'created' if created else 'exists'}, status=status)

# -------------------------------
# 2. Генерация кода
# -------------------------------
@csrf_exempt
def generate_link_code_view(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    trainer = get_object_or_404(Trainer, tg_id=tg_id)
    code = generate_link_code()
    trainer.link_code = code
    trainer.save()
    return JsonResponse({'code': code})

# -------------------------------
# 3. Обновление профиля
# -------------------------------
@csrf_exempt
def update_profile_trainer(request):
    if request.method != 'PUT':
        return HttpResponseBadRequest('Только PUT')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    fullname = data.get('fullname')
    email = data.get('email')
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    trainer = get_object_or_404(Trainer, tg_id=tg_id)
    if fullname: trainer.fullname = fullname
    if email: trainer.email = email
    trainer.save()
    return JsonResponse({'status': 'updated'})

@csrf_exempt
def update_profile_client(request):
    if request.method != 'PUT':
        return HttpResponseBadRequest('Только PUT')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    fullname = data.get('fullname')
    email = data.get('email')
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    client = get_object_or_404(Client, tg_id=tg_id)
    if fullname: client.fullname = fullname
    if email: client.email = email
    client.save()
    return JsonResponse({'status': 'updated'})

# -------------------------------
# 4. Привязка клиента
# -------------------------------
@csrf_exempt
def link_client_to_trainer(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    client_tg_id = data.get('client_tg_id')
    code = data.get('code')
    if not client_tg_id or not code:
        return HttpResponseBadRequest("Missing client_tg_id or code")
    trainer = get_object_or_404(Trainer, link_code=code.upper())
    client = get_object_or_404(Client, tg_id=client_tg_id)
    client.trainer = trainer
    client.save()
    return JsonResponse({'status': 'linked'})

# -------------------------------
# 5. Добавление слота
# -------------------------------
@csrf_exempt
def add_free_time(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    start_time = data.get('start_time')
    duration = data.get('duration_minutes')
    if not all([tg_id, start_time, duration]):
        return HttpResponseBadRequest("Missing fields")
    trainer = get_object_or_404(Trainer, tg_id=tg_id)
    try:
        duration = int(duration)
    except:
        return HttpResponseBadRequest("Invalid duration")
    slot = AvailableSlot.objects.create(
        trainer=trainer,
        start_time=start_time,
        duration_minutes=duration
    )
    return JsonResponse({'id': slot.id}, status=201)

# -------------------------------
# 6. Список клиентов тренера
# -------------------------------
@csrf_exempt
def get_trainer_clients(request, trainer_tg_id):
    if request.method != 'GET':
        return HttpResponseBadRequest('Только GET')
    trainer = get_object_or_404(Trainer, tg_id=trainer_tg_id)
    
    clients = Client.objects.filter(trainer=trainer).prefetch_related('progress_records')
    
    clients_list = []
    for client in clients:
        last_record = client.progress_records.first()  # ordering=['-date'] → последняя
        clients_list.append({
            'tg_id': client.tg_id,
            'fullname': client.fullname or 'Не указано',
            'username': client.username,
            'email': client.email or 'Не указан',
            'last_weight': str(last_record.weight) if last_record and last_record.weight else None,
            'last_calories': last_record.calories_consumed if last_record and last_record.calories_consumed else None,
            'last_date': last_record.date.isoformat() if last_record else None,
        })

    return JsonResponse({
        'status': 'success',
        'clients': clients_list,
        'total': len(clients_list)
    })

# -------------------------------
# 7. Слоты тренера
# -------------------------------
@csrf_exempt
def view_trainer_slots(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('Только GET')
    tg_id = request.GET.get('tg_id')
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    trainer = get_object_or_404(Trainer, tg_id=tg_id)
    slots = AvailableSlot.objects.filter(trainer=trainer).values(
        'id', 'start_time', 'duration_minutes', 'is_booked'
    )
    return JsonResponse(list(slots), safe=False)

# -------------------------------
# 8. Удаление слота
# -------------------------------
@csrf_exempt
def delete_slot(request, slot_id):
    if request.method != 'DELETE':
        return HttpResponseBadRequest('Только DELETE')
    slot = get_object_or_404(AvailableSlot, id=slot_id)
    slot.delete()
    return JsonResponse({}, status=204)

# -------------------------------
# 9. Лог веса
# -------------------------------
@csrf_exempt
def log_weight(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    weight = data.get('weight')
    if not tg_id or not weight:
        return HttpResponseBadRequest("Missing fields")
    
    client = get_object_or_404(Client, tg_id=tg_id)
    today = timezone.now().date()

    record, created = ProgressRecord.objects.update_or_create(
        client=client,
        date=today,
        defaults={'weight': weight}
    )
    return JsonResponse({'status': 'logged', 'created': created})

# -------------------------------
# 10. Лог калорий
# -------------------------------

@csrf_exempt
def log_calories(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    tg_id = data.get('tg_id')
    calories = data.get('calories')
    if not tg_id or not calories:
        return HttpResponseBadRequest("Missing fields")
    
    client = get_object_or_404(Client, tg_id=tg_id)
    today = timezone.now().date()

    record, created = ProgressRecord.objects.update_or_create(
        client=client,
        date=today,
        defaults={'calories_consumed': calories}
    )
    return JsonResponse({'status': 'logged', 'created': created})

# -------------------------------
# 11. Доступные слоты (для клиента)
# -------------------------------
@csrf_exempt
def get_available_slots(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('Только GET')
    tg_id = request.GET.get('tg_id')
    if not tg_id:
        return HttpResponseBadRequest("Missing tg_id")
    client = get_object_or_404(Client, tg_id=tg_id)
    if not client.trainer:
        return JsonResponse([], safe=False)
    slots = AvailableSlot.objects.filter(
        trainer=client.trainer,
        is_booked=False
    ).values('id', 'start_time', 'duration_minutes')
    return JsonResponse(list(slots), safe=False)

# -------------------------------
# 12. Бронирование слота
# -------------------------------
@csrf_exempt
def book_slot(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Только POST')
    data = parse_json(request)
    client_tg_id = data.get('client_tg_id')
    slot_id = data.get('slot_id')
    if not client_tg_id or not slot_id:
        return HttpResponseBadRequest("Missing fields")
    client = get_object_or_404(Client, tg_id=client_tg_id)
    with transaction.atomic():
        slot = AvailableSlot.objects.select_for_update().get(id=slot_id)
        if slot.is_booked:
            return HttpResponseBadRequest("Слот уже забронирован.")
        slot.is_booked = True
        slot.save()
    return JsonResponse({'status': 'booked'}, status=201)