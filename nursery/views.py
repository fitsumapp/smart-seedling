"""Public views for QR code scanning, plant care, and printable label generation."""

from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Avg

from nursery.models import SeedlingBatch
from nursery.services import generate_qr_code_image, generate_printable_label
from monitoring.models import SensorReading


class SeedlingPublicDetailView(DetailView):
    """
    Public, mobile-first customer page displayed when a customer scans a plant pot QR code.
    Shows plant origin, care instructions, germination age, and nursery climate summary.
    Excludes all sensitive internal IDs, API keys, and administrative configurations.
    """
    model = SeedlingBatch
    slug_field = 'qr_token'
    slug_url_kwarg = 'qr_token'
    template_name = 'nursery/plant_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object

        # Calculate growth progress (e.g. 0% seeded to 100% ready)
        status_progress_map = {
            'SEEDED': 15,
            'GERMINATING': 35,
            'GROWING': 70,
            'READY': 100,
            'TRANSPLANTED': 100,
            'ARCHIVED': 100
        }
        context['progress_pct'] = status_progress_map.get(batch.status, 60)

        # Retrieve average growing conditions from sensors in the assigned nursery zone
        readings = SensorReading.objects.none()
        if batch.nursery_zone:
            readings = SensorReading.objects.filter(device__nursery_zone=batch.nursery_zone)
        elif batch.nursery:
            readings = SensorReading.objects.filter(device__nursery_zone__nursery=batch.nursery)

        if readings.exists():
            avg_stats = readings.aggregate(
                avg_temp=Avg('soil_temperature'),
                avg_moist=Avg('soil_moisture')
            )
            context['avg_temp'] = round(avg_stats['avg_temp'], 1) if avg_stats['avg_temp'] else 23.5
            context['avg_moist'] = round(avg_stats['avg_moist'], 1) if avg_stats['avg_moist'] else 46.0
        else:
            context['avg_temp'] = 24.0
            context['avg_moist'] = 45.0

        # Absolute QR code image URL for downloading/sharing
        full_url = self.request.build_absolute_uri(
            reverse('nursery:public-plant-detail', kwargs={'qr_token': batch.qr_token})
        )
        context['full_qr_url'] = full_url
        context['qr_image_url'] = reverse('nursery:plant-qr-image', kwargs={'qr_token': batch.qr_token})
        context['print_label_url'] = reverse('nursery:plant-print-label', kwargs={'qr_token': batch.qr_token})

        return context


class SeedlingQRCodeImageView(View):
    """Returns raw PNG image of the plant's QR code."""

    def get(self, request, qr_token, *args, **kwargs):
        batch = get_object_or_404(SeedlingBatch, qr_token=qr_token)
        target_url = request.build_absolute_uri(
            reverse('nursery:public-plant-detail', kwargs={'qr_token': batch.qr_token})
        )
        qr_bytes = generate_qr_code_image(target_url, box_size=10, border=2)
        response = HttpResponse(qr_bytes, content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="qr_{batch.batch_code}.png"'
        return response


class SeedlingPrintLabelView(View):
    """Generates and downloads a high-resolution printable plant pot label."""

    def get(self, request, qr_token, *args, **kwargs):
        batch = get_object_or_404(SeedlingBatch.objects.select_related('nursery', 'nursery_zone'), qr_token=qr_token)
        base_url = f"{request.scheme}://{request.get_host()}"
        label_bytes = generate_printable_label(batch, base_url)
        response = HttpResponse(label_bytes, content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="label_{batch.batch_code}.png"'
        return response
