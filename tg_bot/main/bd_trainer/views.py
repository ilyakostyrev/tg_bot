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

@csrf_exempt
def trainer_update(request, tg_id):
    if request.method == 'PUT':
        data = parse_json(request)
        if not data:
            return HttpResponseBadRequest('Ошибка парсинга JSON')
        trainer = get_object_or_404(Trainer, tg_id=tg_id)
        trainer.fullname = data.get('fullname', trainer.fullname)
        trainer.username = data.get('username', trainer.username)
        trainer.email = data.get('email', trainer.email)
        trainer.save()
        return JsonResponse({
            'tg_id': str(trainer.tg_id),
            'fullname': trainer.fullname,
            'username': trainer.username,
            'email': trainer.email,
        })
    return HttpResponseBadRequest('Только PUT запрос')

@csrf_exempt
def trainer_delete(request, tg_id):
    if request.method == 'DELETE':
        trainer = get_object_or_404(Trainer, tg_id=tg_id)
        trainer.delete()
        return HttpResponse(status=204)
    return HttpResponseBadRequest('Только DELETE запрос')

@csrf_exempt
def trainer_detail(request, tg_id):
    trainer = get_object_or_404(Trainer, tg_id=tg_id)
    return JsonResponse({
        'tg_id': str(trainer.tg_id),
        'fullname': trainer.fullname,
        'username': trainer.username,
        'email': trainer.email,
    })  

@csrf_exempt
def trainer_list(request):
    trainers = Trainer.objects.all()
    trainers_data = []
    for trainer in trainers:
        trainers_data.append({
            'tg_id': str(trainer.tg_id),
            'fullname': trainer.fullname,
            'username': trainer.username,
            'email': trainer.email,
        })
    return JsonResponse(trainers_data, safe=False)

