import json
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import calendar
from .models import Trainer

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return None

@csrf_exempt
def trainer_create(request):
    if request.method == 'POST':
        data = parse_json(request)
        if not data:
            return HttpResponseBadRequest('Ошибка парсинга JSON')
        if Trainer.objects.filter(tg_id = data.get('tg_id')).exists() & Trainer.objects.filter(email = data.get('email')).exists():
            return HttpResponseBadRequest('Пользователь с таким tg_id или email уже существует') 
        trainer = Trainer.objects.create(
            tg_id = data.get('tg_id'),
            fullname = data.get('fullname'),
            username = data.get('username'),
            email = data.get('email')
        )
        return JsonResponse({
            'tg_id': str(trainer.tg_id),
            'fullname': trainer.fullname,
            'username': trainer.username,
            'email': trainer.email,
        })
    return HttpResponseBadRequest('Только POST запрос')