from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json
from .models import Booking


SLOTS = list(range(10, 20))


def index(request):
    return render(request, 'index.html')


def home(request):
    return render(request, 'booking/home.html')


def bookings_json(request):
    date = request.GET.get('date')
    qs = Booking.objects.all()
    if date:
        qs = qs.filter(reservation_date=date)
    data = [
        {
            'id': b.id,
            'first_name': b.first_name,
            'reservation_date': b.reservation_date.isoformat(),
            'reservation_slot': b.reservation_slot,
        }
        for b in qs
    ]
    return JsonResponse(data, safe=False)


def available_slots_json(request):
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'slots': SLOTS, 'booked': []})
    booked = list(
        Booking.objects.filter(reservation_date=date)
        .values_list('reservation_slot', flat=True)
    )
    return JsonResponse({'slots': SLOTS, 'booked': booked})


@csrf_exempt
def create_booking(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        first_name = (data.get('first_name') or '').strip()
        date = (data.get('reservation_date') or '').strip()
        slot = data.get('reservation_slot')
    else:
        first_name = (request.POST.get('first_name') or '').strip()
        date = (request.POST.get('reservation_date') or '').strip()
        slot = request.POST.get('reservation_slot')
    if not (first_name and date and slot is not None and slot != ''):
        return JsonResponse({'detail': 'first_name, reservation_date and reservation_slot are required.'}, status=400)
    try:
        slot = int(slot)
        if slot not in SLOTS:
            return JsonResponse({'detail': 'Invalid slot.'}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({'detail': 'reservation_slot must be an integer.'}, status=400)
    try:
        from datetime import date as date_cls
        if isinstance(date, str):
            try:
                parsed_date = date_cls.fromisoformat(date)
            except ValueError:
                return JsonResponse({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        else:
            parsed_date = date
        booking = Booking.objects.create(
            first_name=first_name,
            reservation_date=parsed_date,
            reservation_slot=slot,
        )
    except IntegrityError:
        return JsonResponse(
            {'detail': f'Slot {slot} on {date} is already booked.'},
            status=409,
        )
    return JsonResponse(
        {
            'id': booking.id,
            'first_name': booking.first_name,
            'reservation_date': booking.reservation_date.isoformat(),
            'reservation_slot': booking.reservation_slot,
        },
        status=201,
    )
