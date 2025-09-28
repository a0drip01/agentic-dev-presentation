from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Room, Consumer, ConsumerSubscription, ObserverSubscription
from core.notification_bus import NotificationBus

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with demo data for live presentation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing demo data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING('🧹 Cleaning existing demo data...'))
            Room.objects.filter(name__startswith='DEMO-').delete()
            Consumer.objects.filter(name__startswith='DEMO-').delete()
            ObserverSubscription.objects.filter(name__startswith='DEMO-').delete()
            User.objects.filter(username__startswith='demo_').delete()
            
        self.stdout.write(self.style.SUCCESS('🚀 Creating demo data for live presentation...'))
        
        # Create demo rooms
        rooms_data = [
            {'name': 'DEMO-ICU-1', 'timer_seconds': 300},  # 5 minutes
            {'name': 'DEMO-ICU-2', 'timer_seconds': 600},  # 10 minutes  
            {'name': 'DEMO-ER-1', 'timer_seconds': 180},   # 3 minutes
            {'name': 'DEMO-OR-1', 'timer_seconds': 900},   # 15 minutes
        ]
        
        rooms = []
        for room_data in rooms_data:
            room, created = Room.objects.get_or_create(
                name=room_data['name'],
                defaults={'timer_seconds': room_data['timer_seconds']}
            )
            rooms.append(room)
            status = 'created' if created else 'exists'
            self.stdout.write(f'  📍 Room {room.name} ({status})')

        # Create demo users
        users_data = [
            {'username': 'demo_doctor1', 'first_name': 'Dr. Sarah', 'last_name': 'Johnson', 'role': 'doctor'},
            {'username': 'demo_doctor2', 'first_name': 'Dr. Michael', 'last_name': 'Chen', 'role': 'doctor'},
            {'username': 'demo_nurse1', 'first_name': 'Nurse Emily', 'last_name': 'Rodriguez', 'role': 'nurse'},
            {'username': 'demo_nurse2', 'first_name': 'Nurse David', 'last_name': 'Thompson', 'role': 'nurse'},
            {'username': 'demo_patient1', 'first_name': 'John', 'last_name': 'Smith', 'role': 'patient'},
            {'username': 'demo_patient2', 'first_name': 'Maria', 'last_name': 'Garcia', 'role': 'patient'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'email': f"{user_data['username']}@hospital.demo"
                }
            )
            users.append(user)
            status = 'created' if created else 'exists'
            self.stdout.write(f'  👤 User {user.username} - {user.first_name} {user.last_name} ({status})')

        # Assign users to rooms
        assignments = [
            ('DEMO-ICU-1', ['demo_doctor1', 'demo_nurse1', 'demo_patient1']),
            ('DEMO-ICU-2', ['demo_doctor2', 'demo_nurse2', 'demo_patient2']),
            ('DEMO-ER-1', ['demo_doctor1', 'demo_nurse1']),
            ('DEMO-OR-1', ['demo_doctor2', 'demo_nurse2']),
        ]
        
        for room_name, user_names in assignments:
            room = Room.objects.get(name=room_name)
            for username in user_names:
                user = User.objects.get(username=username)
                user.assigned_room = room
                user.save()
            self.stdout.write(f'  🏥 Assigned users to {room_name}: {", ".join(user_names)}')

        # Create demo consumers (for polling API)
        consumers_data = [
            {
                'name': 'DEMO-iPhone-App-DrJohnson',
                'consumer_type': 'mobile',
                'metadata': {'device_id': 'iPhone_Demo_1', 'user': 'Dr. Sarah Johnson'},
                'subscriptions': [
                    {'tag_type': 'room', 'tag_value': 'DEMO-ICU-1'},
                    {'tag_type': 'provider', 'tag_value': 'demo_doctor1'},
                ]
            },
            {
                'name': 'DEMO-Android-App-DrChen',
                'consumer_type': 'mobile',
                'metadata': {'device_id': 'Android_Demo_1', 'user': 'Dr. Michael Chen'},
                'subscriptions': [
                    {'tag_type': 'room', 'tag_value': 'DEMO-ICU-2'},
                    {'tag_type': 'room', 'tag_value': 'DEMO-OR-1'},
                ]
            },
            {
                'name': 'DEMO-Monitoring-Script',
                'consumer_type': 'script',
                'metadata': {'purpose': 'System monitoring'},
                'subscriptions': [
                    {'tag_type': 'all', 'tag_value': 'all'},
                ]
            }
        ]
        
        for consumer_data in consumers_data:
            consumer, created = Consumer.objects.get_or_create(
                name=consumer_data['name'],
                defaults={
                    'consumer_type': consumer_data['consumer_type'],
                    'metadata': consumer_data['metadata']
                }
            )
            
            # Create subscriptions
            for sub_data in consumer_data['subscriptions']:
                sub, sub_created = ConsumerSubscription.objects.get_or_create(
                    consumer=consumer,
                    tag_type=sub_data['tag_type'],
                    tag_value=sub_data['tag_value']
                )
            
            status = 'created' if created else 'exists'
            self.stdout.write(f'  📱 Consumer {consumer.name} ({status}) with {len(consumer_data["subscriptions"])} subscriptions')

        # Create demo observers (for push notifications/webhooks)  
        observers_data = [
            {
                'name': 'DEMO-iPhone-Push-DrJohnson',
                'observer_type': 'mobile_app',
                'room': 'DEMO-ICU-1',
                'callback_url': 'https://httpbin.org/post',
                'metadata': {'device_token': 'demo_token_123', 'user': 'Dr. Sarah Johnson'}
            },
            {
                'name': 'DEMO-Slack-Integration',
                'observer_type': 'webhook',
                'room': 'DEMO-ER-1',
                'callback_url': 'https://hooks.slack.com/demo/webhook',
                'metadata': {'channel': '#emergency-alerts'}
            },
            {
                'name': 'DEMO-External-Monitor',
                'observer_type': 'external_service',
                'room': 'DEMO-OR-1',
                'callback_url': 'https://httpbin.org/post',
                'metadata': {'service': 'Hospital Monitoring System'}
            }
        ]
        
        for obs_data in observers_data:
            room = Room.objects.get(name=obs_data['room'])
            observer_config = {
                'name': obs_data['name'],
                'observer_type': obs_data['observer_type'],
                'callback_url': obs_data['callback_url'],
                'metadata': obs_data['metadata']
            }
            
            try:
                observer = NotificationBus.register_observer(room, observer_config)
                self.stdout.write(f'  🔔 Observer {observer.name} registered for {room.name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Failed to register observer {obs_data["name"]}: {e}'))

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n🎉 Demo data creation complete!'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'  📍 Rooms: {Room.objects.filter(name__startswith="DEMO-").count()}')
        self.stdout.write(f'  👤 Users: {User.objects.filter(username__startswith="demo_").count()}')
        self.stdout.write(f'  📱 Consumers: {Consumer.objects.filter(name__startswith="DEMO-").count()}')
        self.stdout.write(f'  🔔 Observers: {ObserverSubscription.objects.filter(name__startswith="DEMO-").count()}')
        
        # Print demo commands
        self.stdout.write(self.style.SUCCESS('\n🚀 Demo Commands:'))
        self.stdout.write('  # Start a timer on ICU-1 (5 min):')
        self.stdout.write('    python manage.py shell -c "from core.models import Room; Room.objects.get(name=\'DEMO-ICU-1\').start_timer(300)"')
        self.stdout.write('  # Manually trigger notification:')
        self.stdout.write('    python manage.py shell -c "from core.models import Room; Room.objects.get(name=\'DEMO-ICU-1\').notify_observers()"')
        self.stdout.write('  # Check observer status:')
        self.stdout.write('    python manage.py shell -c "from core.models import ObserverSubscription; [print(f\'{o.name}: {o.status} (failures: {o.failure_count})\') for o in ObserverSubscription.objects.filter(name__startswith=\'DEMO-\')]"')