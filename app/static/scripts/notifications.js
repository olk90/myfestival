$(function () {
    var timer = null;
    var xhr = null;
    $('.user_popup').hover(
        function(event) {
            // mouse in event handler
            var elem = $(event.currentTarget);
            timer = setTimeout(function() {
                timer = null;
                xhr = $.ajax(
                    '/user/' + elem.first().text().trim() + '/popup').done(
                        function(data) {
                            xhr = null;
                            elem.popover({
                                trigger: 'manual',
                                html: true,
                                animation: false,
                                container: elem,
                                content: data
                            }).popover('show');
                            flask_moment_render_all();
                        }
                    );
            }, 250);
        },
        function(event) {
            // mouse out event handler
            var elem = $(event.currentTarget);
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            else if (xhr) {
                xhr.abort();
                xhr = null;
            }
            else {
                elem.popover('destroy');
            }
        }
    );
});

function setNotificationUpdate(n, spanId) {
    $('#'.concat(spanId)).text(n);
    $('#'.concat(spanId)).css('visibility', n ? 'visible' : 'hidden');
}

function updateNotifications(since) {
    $.ajax('/notifications?since=' + since).done(
        function(notifications) {
            for (var i = 0; i < notifications.length; i++) {
                if (notifications[i].name == 'festival_updated')
                    setNotificationUpdate(notifications[i].data, 'festival_count');
                if (notifications[i].name == 'no_registration_codes')
                    setNotificationUpdate(notifications[i].data, 'available_codes');
                if (notifications[i].name == 'admin')
                    setNotificationUpdate(notifications[i].data, 'admin_changed');
                since = notifications[i].timestamp;
            }
        }
    );
    setTimeout(updateNotifications, 10000)
}

$(function() {
    var since = 0;
    updateNotifications(since);
});