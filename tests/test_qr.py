"""Unit and integration tests for QR code generation and public plant pages."""

from django.test import TestCase
from django.urls import reverse
from nursery.models import Nursery, NurseryZone, SeedlingBatch, SeedlingStatus
from nursery.services import generate_qr_code_image, generate_printable_label


class QRCodeModuleTestCase(TestCase):
    def setUp(self):
        self.nursery = Nursery.objects.create(name="Nursery Delta", code="NUR-D", location="Greenhouse 3")
        self.zone = NurseryZone.objects.create(nursery=self.nursery, name="Zone Alpha", code="ZA")
        self.batch = SeedlingBatch.objects.create(
            nursery=self.nursery,
            nursery_zone=self.zone,
            batch_code="BATCH-TEST-TOM-01",
            plant_name="Roma Tomato",
            variety="Roma VF",
            quantity=100,
            status=SeedlingStatus.GROWING
        )

    def test_qr_code_generation_service(self):
        url = f"http://testserver/plant/{self.batch.qr_token}/"
        qr_bytes = generate_qr_code_image(url)
        self.assertTrue(len(qr_bytes) > 0)
        self.assertTrue(qr_bytes.startswith(b'\x89PNG'))

    def test_printable_label_generation_service(self):
        label_bytes = generate_printable_label(self.batch, "http://testserver")
        self.assertTrue(len(label_bytes) > 0)
        self.assertTrue(label_bytes.startswith(b'\x89PNG'))

    def test_public_plant_detail_view_success(self):
        url = reverse('nursery:public-plant-detail', kwargs={'qr_token': self.batch.qr_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roma Tomato")
        self.assertContains(response, "Roma VF")
        self.assertContains(response, "Nursery Delta")
        self.assertContains(response, "BATCH-TEST-TOM-01")
        # Ensure administrative secrets are never exposed
        self.assertNotContains(response, "api_key")
        self.assertNotContains(response, "secret")

    def test_public_plant_detail_view_invalid_token(self):
        url = reverse('nursery:public-plant-detail', kwargs={'qr_token': 'invalid-token-12345'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_qr_image_view(self):
        url = reverse('nursery:plant-qr-image', kwargs={'qr_token': self.batch.qr_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_print_label_view(self):
        url = reverse('nursery:plant-print-label', kwargs={'qr_token': self.batch.qr_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))
