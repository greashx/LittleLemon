from django.db import models


class Booking(models.Model):
    first_name = models.CharField(max_length=255)
    reservation_date = models.DateField()
    reservation_slot = models.SmallIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reservation_date', 'reservation_slot')
        ordering = ['reservation_date', 'reservation_slot']

    def __str__(self) -> str:
        return f"{self.first_name} - {self.reservation_date} @ slot {self.reservation_slot}"
