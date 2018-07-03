
from django.conf.urls import url, include
from raidikalu.views import RaidListView, RaidSnippetView, RaidCreateView, RaidReceiverView, GymReceiverView, RaidJsonExportView, NotificationSubView, NotificationUnsubView


urlpatterns = [
  url('^$', RaidListView.as_view(), name='raidikalu.raid_list'),
  url('^ilmoita-raidi/$', RaidCreateView.as_view(), name='raidikalu.raid_create'),
  url('^api/1/raid-receiver/(?P<api_key>[^/]+)/$', RaidReceiverView.as_view(), name='raidikalu.raid_receiver'),
  url('^api/1/gym-receiver/(?P<api_key>[^/]+)/$', GymReceiverView.as_view(), name='raidikalu.gym_receiver'),
  url('^api/1/raid-export/(?P<api_key>[^/]+)/$', RaidJsonExportView.as_view(), name='raidikalu.raid_export'),
  url('^api/1/raid-snippet/(?P<pk>[^/]+)/$', RaidSnippetView.as_view(), name='raidikalu.raid_snippet'),
  url('^notifications/subscribe$', NotificationSubView.as_view(), name='raidikalu.notifications.subscribe'),
  url('^notifications/unsubscribe$', NotificationUnsubView.as_view(), name='raidikalu.notifications.unsubscribe'),
]
