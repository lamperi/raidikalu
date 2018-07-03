
import json
import requests
from pywebpush import webpush, WebPushException
from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import date as date_filter
from raidikalu.models import EditableSettings, RaidVote, PushSubscription

def notify_raid(instance, created, **kwargs):
  raid = instance
  if not raid.pokemon_name and not raid.tier:
    return
  notify_raid_push_notification(raid)
  already_notified_raid_ids = cache.get('already_notified_raid_ids') or []
  if raid.pk in already_notified_raid_ids:
    return
  should_notify = bool(raid.pokemon_name and RaidVote.get_confidence(raid, RaidVote.FIELD_POKEMON) >= 1)
  should_notify |= bool(raid.tier and RaidVote.get_confidence(raid, RaidVote.FIELD_TIER) >= 1)
  if should_notify:
    check_raid_notifications(raid)
    already_notified_raid_ids.append(raid.pk)
    already_notified_raid_ids = already_notified_raid_ids[-100:]
    cache.set('already_notified_raid_ids', already_notified_raid_ids, 300 * 24 * 60 * 60)


def check_raid_notifications(raid):
  editable_settings = EditableSettings.get_current_settings()
  already_notified_channels = []
  for notification in editable_settings.notifications:
    if 'pokemon' in notification and notification['pokemon'] != raid.pokemon_name:
      continue
    if 'tier' in notification and notification['tier'] != raid.tier:
      continue
    webhook_url = notification['webhook']
    channel = notification.get('channel', None)
    channel_key = '%s|%s' % (channel or '', webhook_url)
    if channel_key in already_notified_channels:
      continue
    already_notified_channels.append(channel_key)
    if notification['service'] == 'slack':
      notify_raid_slack(raid, webhook_url, channel)
    elif notification['service'] == 'discord':
      notify_raid_discord(raid, webhook_url, channel)


def notify_raid_slack(raid, webhook_url, channel=None):
  payload = {
    'username': 'Raidikalu',
    'icon_emoji': ':large_blue_circle:',
    'text': '%s - %s jäljellä - %s' % (raid.pokemon_name or raid.get_tier_display(), raid.get_time_left_until_end_display(), raid.gym.name),
    'unfurl_media': False,
    'attachments': [
      {
        'fallback': '',
        'thumb_url': raid.gym.image_url,
        'fields': [
          {'title': 'Sali', 'value': raid.gym.name},
          {'title': 'Pokémon', 'value': raid.pokemon_name, 'short': True},
          {'title': 'Taso', 'value': raid.get_tier_display(), 'short': True},
          {'title': 'Sijainti', 'value': '<https://gymhuntr.com/#%s,%s|Salin sijainti>' % (raid.gym.latitude, raid.gym.longitude), 'short': True},
          {'title': 'Ajo-ohjeet', 'value': '<https://www.google.com/maps/?daddr=%s,%s|Ajo-ohjeet salille>' % (raid.gym.latitude, raid.gym.longitude), 'short': True},
          {'title': 'Alkaa', 'value': date_filter(raid.start_at, 'H:i') if raid.start_at else '\u2013', 'short': True},
          {'title': 'Päättyy', 'value': date_filter(raid.end_at, 'H:i') if raid.end_at else '\u2013', 'short': True},
        ],
      }
    ]
  }
  if channel:
    payload['channel'] = channel
  requests.post(webhook_url, json=payload)


def notify_raid_discord(raid, webhook_url, channel=None):
  payload = {
    'username': 'Raidikalu',
    'icon_emoji': ':large_blue_circle:',
    'text': '%s - %s jäljellä - %s' % (raid.pokemon_name or raid.get_tier_display(), raid.get_time_left_until_end_display(), raid.gym.name),
    'unfurl_media': False,
    'attachments': [
      {
        'fallback': '',
        'thumb_url': raid.gym.image_url,
        'fields': [
          {'title': 'Sali', 'value': raid.gym.name},
          {'title': 'Pokémon', 'value': raid.pokemon_name, 'short': True},
          {'title': 'Taso', 'value': raid.get_tier_display(), 'short': True},
          {'title': 'Sijainti', 'value': '<https://gymhuntr.com/#%s,%s|Salin sijainti>' % (raid.gym.latitude, raid.gym.longitude), 'short': True},
          {'title': 'Ajo-ohjeet', 'value': '<https://www.google.com/maps/?daddr=%s,%s|Ajo-ohjeet salille>' % (raid.gym.latitude, raid.gym.longitude), 'short': True},
          {'title': 'Alkaa', 'value': date_filter(raid.start_at, 'H:i') if raid.start_at else '\u2013', 'short': True},
          {'title': 'Päättyy', 'value': date_filter(raid.end_at, 'H:i') if raid.end_at else '\u2013', 'short': True},
        ],
      }
    ]
  }
  if channel:
    payload['channel'] = channel
  requests.post(webhook_url, json=payload)

def notify_raid_push_notification(raid):
  raid_time_left = raid.get_time_left_until_end()
  ttl = int(raid_time_left.total_seconds()) if raid_time_left is not None else 1800
  message = '%s - %s jäljellä - %s' % (raid.pokemon_name or raid.get_tier_display(), raid.get_time_left_until_end_display(), raid.gym.name)
  pokemon_image = raid.get_pokemon_image_url()
  payload = {
    'raid_id': raid.pk,
    'message': message,
    'pokemon': raid.pokemon_name,
    'tier': raid.get_tier_display(),
    'pokemon_image': pokemon_image,
    'gym_image': raid.gym.image_url,
    'gmaps': '/#redirect/https://www.google.com/maps/?daddr={},{}'.format(raid.gym.latitude, raid.gym.longitude),
  }
  
  users_to_notify = PushSubscription.find_by_raid(raid)
  for push_subscription in users_to_notify:
    subscription_info = {
      'endpoint': push_subscription.endpoint,
      'keys': {
        'auth': push_subscription.auth,
        'p256dh': push_subscription.p256dh
      }
    }
    try:
       webpush(
        subscription_info,
        json.dumps(payload),
        ttl=ttl,
        vapid_private_key=settings.NOTIFICATION_SETTINGS.get('VAPID_PRIVATE_KEY', ''),
        vapid_claims={"sub": "mailto:{}".format(settings.NOTIFICATION_SETTINGS.get('VAPID_ADMIN_EMAIL', ''))}
      )
    except WebPushException as e:
      if not hasattr(e, 'response'):
        push_subscription.delete()
      elif e.response and e.response.status_code == 400:
        # remove invalid subscription, 400 == do not repeat this request
        push_subscription.delete()

