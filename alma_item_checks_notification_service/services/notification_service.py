"""Service class for notifications"""
import io
import json
import logging
import pathlib
from typing import Any

from acs_email_sender_message_model import EmailMessage  # type: ignore
import azure.functions as func
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template, TemplateNotFound
import pandas as pd
from sqlalchemy.orm import Session
from wrlc_azure_storage_service import StorageService  # type: ignore

from alma_item_checks_notification_service.config import (
    ACS_STORAGE_CONNECTION_STRING,
    ACS_SENDER_CONTAINER_NAME,
    ACS_SENDER_QUEUE_NAME
)
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.services.process_service import ProcessService
from alma_item_checks_notification_service.services.user_process_service import UserProcessService


# noinspection PyMethodMayBeStatic
class NotificationService:
    """Service class for notifications"""
    def __init__(self, msg: func.QueueMessage):
        self.msg = msg
        self.storage_service = StorageService()
        self.jinja_env: Environment | None = None

        # Initialize the Jinja2 environment once in the constructor for efficiency
        try:
            template_dir = pathlib.Path(__file__).parent.parent / "templates"
            if not template_dir.is_dir():
                logging.error(f"Jinja template directory not found at: {template_dir}")
                raise FileNotFoundError(
                    f"Jinja template directory not found: {template_dir}"
                )

            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(["html", "xml"]),
            )
            logging.info(f"Jinja2 environment loaded successfully from: {template_dir}")
        except Exception as e:
            logging.exception(f"Failed to initialize Jinja2 environment: {e}")
            # The service can continue, but render_email_body will fail gracefully.

    def send_notification(self, session: Session) -> None:
        """Send an email notification"""
        message_data: dict[str, Any] = json.loads(self.msg.get_body().decode())

        report_id: str | None = message_data["report_id"]
        institution_id: int | None = message_data["institution_id"]
        process_type: str | None = message_data["process_type"]

        if not process_type or not institution_id or not report_id:
            logging.error("NotificationService.send_notification: message body missing required fields")
            return

        process_service: ProcessService = ProcessService(session)
        process: Process | None = process_service.get_process_by_name(process_type)

        if not process:
            logging.error(f"NotificationService.send_notification: process type {process_type} not found")
            return

        report: dict[str, Any] | list | None = self.storage_service.download_blob_as_json(
            container_name=process.container,
            blob_name=report_id + ".json",
        )

        user_process_service: UserProcessService = UserProcessService(session)
        user_emails: list[str] = user_process_service.get_user_emails_for_process(int(process.id), institution_id)

        storage_service: StorageService = StorageService(ACS_STORAGE_CONNECTION_STRING)

        html_table: str | None = self.create_html_table(report=report, process=process)

        html_content_body: str | None = self.render_email_body(
            template_name="email_template.html.j2",
            process=process,
            html_table=html_table,
        )

        email_to_send: EmailMessage = EmailMessage(
            to=user_emails,
            subject=str(process.email_subject),
            html=html_content_body,
        )

        email_json_content = email_to_send.model_dump_json()

        storage_service.upload_blob_data(
            container_name=ACS_SENDER_CONTAINER_NAME,
            blob_name=report_id + ".json",
            data=email_json_content
        )

        message_content: dict[str, str] = {
            "blob_name": report_id + ".json",
        }

        storage_service.send_queue_message(
            queue_name=ACS_SENDER_QUEUE_NAME,
            message_content=message_content
        )

    def render_email_body(
        self,
        template_name: str,
        process: Process,
        html_table: str | None = None,
    ) -> str | None:
        """
        Render the email body using the provided template and context.

        Args:
            template_name (str): The name of the email template file.
            process (Process): The process object containing email subject and body.
            html_table (str): The HTML table to include in the email body.

        Returns:
             The rendered email body as a string, or None on failure.
        """
        if not self.jinja_env:
            logging.error(
                "NotificationService.render_email_body: Cannot render email, Jinja2 environment not available."
            )
            return None
        try:
            template: Template = self.jinja_env.get_template(template_name)
            template_context = {
                "email_caption": process.email_subject,
                "email_body": process.email_body,
                "body_addendum": process.email_addendum,
                "data_table_html": html_table,
            }
            html_content_body: str = template.render(template_context)
            logging.debug("NotificationService.render_email_body: Email template rendered successfully.")
            return html_content_body
        except TemplateNotFound as template_err:
            logging.error(
                f"NotificationService.render_email_body: Template not found: {template_err}", exc_info=True
            )
            return None
        except Exception as render_err:
            logging.error(
                f"NotificationService.render_email_body: Error rendering template: {render_err}", exc_info=True
            )
            return None

    def create_html_table(self, report: dict[str, Any] | list | None, process: Process) -> str | None:
        """
        Create an HTML table from JSON data stored in Azure Blob Storage.

        Args:
            report (dict[str, Any] | list | None): The JSON report data from Azure storage service.
            process (Process): The check object containing email subject and body.

        Returns:
            str | None: The HTML table as a string, or None if an error occurs.

        """
        html_table: str = "Error generating table from data."
        # noinspection PyUnusedLocal
        record_count = 0

        json_report = json.dumps(report)
        try:
            if report:
                json_io = io.StringIO(json_report)
                df = pd.read_json(json_io, orient='records')  # Adjust 'orient' if needed
                df.style.set_caption(str(process.email_subject))

                # Check if column '0' exists and all its values are '0' (as string or int)
                if '0' in df.columns and df['0'].astype(str).eq('0').all():
                    logging.debug(
                        "NotificationService.create_html_table: Column '0' contains only '0' values. Dropping column."
                    )
                    df.drop('0', axis=1, inplace=True)

                record_count = len(df)
                logging.debug(f"NotificationService.create_html_table: Read {record_count} rows into DataFrame.")
                if not df.empty:
                    html_table = df.to_html(index=False, border=1, na_rep='').replace(
                        'border="1"',
                        'border="1" style="border-collapse: collapse; border: 1px solid black;"'
                    )
                    logging.debug("NotificationService.create_html_table: Converted DataFrame to HTML string.")
                else:
                    html_table = (
                        "<i>Report generated, but contained no displayable data.</i><br>"
                    )
            else:
                logging.warning("NotificationService.create_html_table: No JSON data string available for conversion.")
                return None
        except Exception as convert_err:
            logging.error(
                f"NotificationService.create_html_table: Failed JSON->HTML conversion: {convert_err}",
                exc_info=True
            )

        return html_table
