from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    assigned_room = models.ForeignKey('Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')

class Room(models.Model):
    name = models.CharField(max_length=50)
    timer_seconds = models.PositiveIntegerField(default=0)
    timer_started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def start_timer(self, seconds):
        self.timer_seconds = seconds
        self.timer_started_at = timezone.now()
        self.save()

    def stop_timer(self):
        self.timer_seconds = 0
        self.timer_started_at = None
        self.save()

    def timer_expired(self):
        if self.timer_started_at and self.timer_seconds > 0:
            elapsed = (timezone.now() - self.timer_started_at).total_seconds()
            return elapsed >= self.timer_seconds
        return False

    def notify_observers(self, event_type='expired'):
        doctors = self.users.filter(role='doctor')
        nurses = self.users.filter(role='nurse')
        doctor_names = ', '.join([d.username for d in doctors]) or 'none'
        nurse_names = ', '.join([n.username for n in nurses]) or 'none'
        if event_type == 'expired':
            print(f"[NOTIFY] {timezone.now()} - room {self.name} timer EXPIRED, notify doctor(s) {doctor_names} and nurse(s) {nurse_names}")
        else:
            print(f"[NOTIFY] {timezone.now()} - room {self.name} timer expired, notify doctor(s) {doctor_names} and nurse(s) {nurse_names}")
