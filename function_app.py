"""Notification Azure Function"""

import azure.functions as func

from alma_item_checks_notification_service.blueprints.bp_notification import (
    bp as bp_notification,
)

app = func.FunctionApp()

app.register_blueprint(bp_notification)
