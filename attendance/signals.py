from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Attendance, Penalty


@receiver(post_save, sender=Attendance)
def create_penalty(sender, instance, created, **kwargs):
    """
    Automatically create a penalty when an Attendance is created.
    Handles Absent and Late statuses.
    """
    if not created:
        return

    penalty_amount = Decimal("0.00")

    if instance.status == "Absent":
        penalty_amount = instance.session.event.penalty_amount or Decimal("0.00")

    # elif instance.status == "Late":
    #     penalty_amount = instance.session.event.late_penalty_amount or Decimal("0.00")

    # Only create penalty if there's an amount
    if penalty_amount > 0:
        Penalty.objects.get_or_create(
            attendance=instance,
            defaults={"amount": penalty_amount}
        )
