
window.addEventListener('load', function() {
	var messages = {
		subscribe: 'Hälytä raideista',
		unsubscribe: 'Älä hälytä raideista',
		successfullySubscribed: 'Nyt raideista tulee huomautus',
		successfullyUnsubscribed: 'Nyt raideista ei tule enää huomautusta',
		serviceWorkerNotSupported: 'Selaimesi ei tue huomautuksia (Service Worker)',
		showingNotificationNotSupported: 'Selaimesi ei tue huomautuksia (notification)',
		notificationDenied: 'Olet estänyt huomautukset raidikalusta',
		pushNotAvailable: 'Selaimesi ei tue huomautuksia (Push Manager)',
		fetchNotAvailable: 'Selaimesi ei tue huomautuksia (fetch)',
		subscriptionUnavailable: 'Huomautusta ei ole rekisteröity',
		failedToUnsubscribe: 'Virhe peruutettaessa huomautuksia',
		error: 'Virhe',
	};

	var toggle = document.getElementById('notifications-toggle');
	var toggleLabel = document.getElementById('notifications-toggle-label');
	var messageBox = document.getElementById('notifications-message');
	toggle.disabled = true;

	/* import */
	var selectedPokemon = window.selectedPokemon,
	    selectedGyms = window.selectedGyms,
	    selectedTiers = window.selectedTiers,
	    applicationServerKey = window.applicationServerKey,
	    serviceWorkerUrl = window.serviceWorkerUrl,
	    CSRFTOKEN = window.CSRFTOKEN;

	if ('serviceWorker' in navigator) {
		navigator.serviceWorker.register(serviceWorkerUrl)
			.then(function(reg) {
				if (checkPushSupport(reg)) {
					toggle.addEventListener('change', function() {
						toggle.disabled = true;
						if (!toggle.checked) {
							unsubscribe(reg);
						} else {
							subscribe(reg);
						}
					});
					reg.pushManager.getSubscription().then(function(subscription) {
						if (subscription) {
							updateMessage(false, true, '');
						} else {
							updateMessage(false, false, '');
						}
					});
				}
			});
	} else {
		updateMessage(true, false, messages.serviceWorkerNotSupported);
	}

	function updateMessage(toggleDisabled, pushEnabled, messageText) {
		toggle.disabled = toggleDisabled;
		toggle.checked = pushEnabled;
		messageBox.textContent = messageText;
		messageBox.style.display = messageText ? '' : 'hidden';
	}
	function checkPushSupport(reg) {
		if (!reg.showNotification) {
			updateMessage(true, false, messages.showingNotificationsNotSupported);
			return;
		}

		if (Notification.permission === 'denied') {
			updateMessage(false, false, messages.notificationDenied);
			return;
		}

		if (!('PushManager' in window)) {
			updateMessage(true, false, messages.pushNotAvailable);
			return;
		}
		if (!('fetch' in window)) {
			updateMessage(true, false, messages.fetchNotAvailable);
		}

		return true;
	}

	function subscribe(reg) {
		getOrCreateSubscription(reg).then(function(subscription) {
			request('/notifications/subscribe', reg, subscription, function(response) {
				if (response.status === 201) {
					updateMessage(false, true, messages.successfullySubscribed);
				} else {
					throw new Error(response.status);
 				}
			});
		}).catch(function(error) {
			updateMessage(true, false, messages.error);
			console.error('Subscription error:', error)
		});
	}

	function urlB64ToUint8Array(base64String) {
		const padding = '='.repeat((4 - base64String.length % 4) % 4);
		const base64 = (base64String + padding)
			.replace(/\-/g, '+')
			.replace(/_/g, '/');

		const rawData = window.atob(base64);
		const outputArray = new Uint8Array(rawData.length);

		for (var i = 0; i < rawData.length; ++i) {
			outputArray[i] = rawData.charCodeAt(i);
		}
		return outputArray;
	}

	function getOrCreateSubscription(reg) {
		return reg.pushManager.getSubscription().then(function(subscription) {
			// Check if Subscription is available
			if (subscription) {
				return subscription;
			}
			
			if (!applicationServerKey) {
				throw new Error('Failed to register subscription as vapid key is not defined in settings');
			}
			var options = {
				userVisibleOnly: true,
				applicationServerKey: urlB64ToUint8Array(applicationServerKey),
			};
			return reg.pushManager.subscribe(options)
		});
	}

	function unsubscribe(reg) {
		reg.pushManager.getSubscription()
			.then(function(subscription) {
				if (!subscription) {
					updateMessage(false, false, messages.subscriptionUnavailable);
					return;
				}
				request('/notifications/unsubscribe', reg, subscription, function(response) {
					if (response.status === 202) {
						subscription.unsubscribe()
							.then(function(successful) {
								if (!successful) {
									throw new Error('Failed to unsubscribe()');
								}
								updateMessage(false, false, messages.successfullyUnsubscribed);
							});
					} else {
						throw new Error(response.status);
					}
				});
			}).catch(function(error) {
				updateMessage(false, true, messages.failedToUnsubscribe);
				console.error('Error: ' + error);
			});
	}

	function request(url, reg, subscription, callback) {
		var data = {
			subscription: subscription.toJSON(),
			pokemon: selectedPokemon, 
			gyms: selectedGyms,
			tiers: selectedTiers,
		};

		fetch(url, {
			method: 'post',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': CSRFTOKEN,
			},
			body: JSON.stringify(data),
			credentials: 'include'
		}).then(callback);
	}
});
