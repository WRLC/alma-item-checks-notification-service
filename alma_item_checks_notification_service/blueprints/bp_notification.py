"""Notification blueprint"""
import azure.functions as func

from alma_item_checks_notification_service.config import NOTIFICATION_QUEUE, STORAGE_CONNECTION_SETTING_NAME
from alma_item_checks_notification_service.database import SessionMaker
from alma_item_checks_notification_service.services.notification_service import NotificationService

bp = func.Blueprint()


@bp.function_name("send_notification")
@bp.queue_trigger(
    arg_name="notificationmsg",
    queue_name=NOTIFICATION_QUEUE,
    connection=STORAGE_CONNECTION_SETTING_NAME
)
def send_notification(notificationmsg: func.QueueMessage) -> None:
    """Notification function"""
    notification = NotificationService(notificationmsg)  # initialize notification service

    with SessionMaker() as session:
        notification.send_notification(session)  # send notification
