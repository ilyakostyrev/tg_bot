import json
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import calendar
from .models import Client, ProgressRecord

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return None

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

    tg_id = data.get('tg_id')
    fullname = data.get('fullname')
    username = data.get('username')
    email = data.get('email')

    if not tg_id or not fullname:
        return HttpResponseBadRequest("Missing required fields 'tg_id' or 'fullname'.")

    client, created = Client.objects.get_or_create(
        tg_id=tg_id,
        defaults={
            'fullname': fullname,
            'username': username,
            'email': email
        }
    )

    if not created:
        client.fullname = fullname
        client.username = username
        client.email = email
        client.save()

    response_data = {
        "status": "success",
        "message": "Client registered." if created else "Client updated.",
        "data": {
            "tg_id": client.tg_id,
            "fullname": client.fullname,
            "username": client.username,
            "email": client.email
        }
    }

    return JsonResponse(response_data)


