from rest_framework import serializers
from sophia.models import ScheduledLesson

class ScheduledLessonSerializer(serializers.ModelSerializer):
    start = serializers.TimeField(source='get_start_time_string')
    end = serializers.TimeField(source='get_end_time_string')
    day = serializers.CharField(source='student.get_day_display')
    title = serializers.CharField(source='student.full_name')    

    class Meta:
        model = ScheduledLesson
        fields = (
            'pk', 'date', 'start', 'end', 'day', 'title', 'color',
            'is_pending', 'is_reschedule',
            'start_time', 'end_time', 'completed_on', 'cancelled_on',
            'rescheduled_on'
        )
