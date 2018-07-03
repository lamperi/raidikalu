self.addEventListener('push', function(event) {
    if (!event.data) {
        return;
    }

    var payload = event.data.json();
    var title = 'Raidi kalussa!'
    var options = {
        icon: payload.pokemon_image || payload.gym_image,
        body: payload.message,
        actions: [
            {action: 'navigate', title: 'Ajo-ohjeet'},
            {action: 'view', title: 'Mukaan'},
        ],
        tag: 'raid-' + payload.raid_id,
        data: payload,
    };

    event.waitUntil(
      self.registration.showNotification(title, options)
    );
});


self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    var url;
    if (event.action === 'navigate') {
        url = '/#redirect/' + event.notification.data.gmaps;
    } else if (event.action === 'view') {
        url = '/#raid-' + event.notification.data.raid_id;
    }
    event.waitUntil(
      clients.matchAll().then(function(clientList) {
        var client = clientList.find(function(c) {
          c.visibilityState === 'visible';
        });
        if (client !== undefined) {
          client.navigate(url);
          client.focus();
        } else {
          clients.openWindow(url);
        }
      })
    );
});
