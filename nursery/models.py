"""Nursery, NurseryZone, and SeedlingBatch models."""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Nursery(models.Model):
    """Represents a physical greenhouse/nursery installation."""
    name = models.CharField(max_length=100, help_text=_('Display name of the nursery.'))
    code = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text=_('Unique uppercase code e.g. NURSERY-NORTH-01')
    )
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True, help_text=_('Physical address or GPS coordinates.'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Nursery')
        verbose_name_plural = _('Nurseries')

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)


class NurseryZone(models.Model):
    """Subdivision within a nursery (e.g. Zone A, Propagation Bench 1)."""
    nursery = models.ForeignKey(
        Nursery,
        on_delete=models.CASCADE,
        related_name='zones'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nursery', 'name']
        verbose_name = _('Nursery Zone')
        verbose_name_plural = _('Nursery Zones')
        constraints = [
            models.UniqueConstraint(
                fields=['nursery', 'code'],
                name='unique_nursery_zone_code'
            )
        ]

    def __str__(self):
        return f"{self.nursery.code} - {self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)


class SeedlingStatus(models.TextChoices):
    SEEDED = 'SEEDED', _('Seeded')
    GERMINATING = 'GERMINATING', _('Germinating')
    GROWING = 'GROWING', _('Growing')
    READY = 'READY', _('Ready for Transplant')
    TRANSPLANTED = 'TRANSPLANTED', _('Transplanted')
    ARCHIVED = 'ARCHIVED', _('Archived')


class SeedlingBatch(models.Model):
    """Represents a specific batch of seedlings managed within a nursery zone."""
    nursery = models.ForeignKey(
        Nursery,
        on_delete=models.CASCADE,
        related_name='seedling_batches'
    )
    nursery_zone = models.ForeignKey(
        NurseryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seedling_batches'
    )
    batch_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique batch identification code, e.g. BATCH-2026-TOM-001')
    )
    plant_name = models.CharField(max_length=100, help_text=_('Common name e.g. Tomato'))
    species = models.CharField(max_length=100, blank=True, help_text=_('Scientific name e.g. Solanum lycopersicum'))
    variety = models.CharField(max_length=100, blank=True, help_text=_('Cultivar / Variety e.g. San Marzano'))
    planting_date = models.DateField(default=timezone.now)
    expected_transplant_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=SeedlingStatus.choices,
        default=SeedlingStatus.GROWING
    )
    description = models.TextField(blank=True)
    care_instructions = models.TextField(
        blank=True,
        help_text=_('Customer care instructions rendered on public QR page.')
    )
    photo = models.ImageField(upload_to='seedlings/photos/', null=True, blank=True)
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
        help_text=_('Secret UUID token for public QR code customer access.')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Seedling Batch')
        verbose_name_plural = _('Seedling Batches')

    def __str__(self):
        return f"{self.batch_code} - {self.plant_name} ({self.quantity} plants)"

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex
        self.batch_code = self.batch_code.upper().strip()
        super().save(*args, **kwargs)

    @property
    def age_days(self) -> int:
        """Returns the age of the seedling batch in days."""
        p_date = self.planting_date.date() if hasattr(self.planting_date, 'date') else self.planting_date
        return max(0, (timezone.now().date() - p_date).days)

