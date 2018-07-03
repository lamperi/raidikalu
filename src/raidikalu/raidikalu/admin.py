from django.contrib import admin
from raidikalu.models import EditableSettings, Gym, GymNickname, Raid, DataSource, RaidVote, Attendance
from raidikalu.models import PushSubscription, SubscriptionPokemon, SubscriptionGym, SubscriptionTier


class GymAdmin(admin.ModelAdmin):
  list_display = ('name', 'is_park', 'is_active')
  list_filter = ('is_park', 'is_active')
  search_fields = ('name',)


admin.site.register(EditableSettings)
admin.site.register(Gym, GymAdmin)
admin.site.register(GymNickname)
admin.site.register(Raid)
admin.site.register(DataSource)
admin.site.register(RaidVote)
admin.site.register(Attendance)
admin.site.register(PushSubscription)
admin.site.register(SubscriptionPokemon)
admin.site.register(SubscriptionGym)
admin.site.register(SubscriptionTier)
