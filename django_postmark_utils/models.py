from django.db import models
from django.utils.translation import ugettext_lazy as _


class Message(models.Model):
    """
    Email message data.

    TODO: - make the following messages unavailable for resending:
            - already-been-resent messages, because new messages are created
              upon resending
    """

    DELIVERY_STATUS_OPTIONS = {
        'NOT_SENT'    : 0,
        'SENT'        : 1,
        'BOUNCED'     : 2,
        'DELIVERED'   : 3,
    }

    pickled_obj = models.BinaryField(
        _("Pickled object"),
        help_text=_("Pickled message object")
    )
    message_id = models.CharField(
        _("Message ID"),
        max_length=255,
        unique=True,
        help_text=_("The 'Message-ID' header field of the message")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("The 'Date' header field of the message")
    )
    subject = models.CharField(
        _("Subject"),
        max_length=255,
        blank=True,
        help_text=_("The 'Subject' header field of the message")
    )
    from_email = models.CharField(
        _("Sender email address"),
        max_length=255,
        blank=True,
        help_text=_("The 'From' header field of the message")
    )
    to_emails = models.TextField(
        _("Recipient email addresses"),
        blank=True,
        help_text=_("The 'To' field of the message, with email addresses "
                    "separated by commas")
    )
    cc_emails = models.TextField(
        _("Cc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Cc' field of the message, with email addresses "
                    "separated by commas")
    )
    bcc_emails = models.TextField(
        _("Bcc'd recipient email addresses"),
        blank=True,
        help_text=_("The 'Bcc' field of the message, with email addresses "
                    "separated by commas")
    )
    delivery_status = models.IntegerField(
        _("Delivery status"),
        help_text=_("The delivery status of the message"),
    )
    has_been_resent = models.BooleanField(
        _("Has been resent"),
        default=False,
        help_text=_("If the message has been resent, after an exception "
                    "prevented this from happening the first time round")
    )
    delivery_submission_date = models.DateTimeField(
        _("Delivery-submission date"),
        null=True,
        blank=True,
        help_text=_("When the message was submitted for delivery")
    )
    delivery_message_id = models.CharField(
        _("Delivery message ID"),
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("The 'Message-ID' header field of the message, as set by "
                    "Postmark")
    )
    delivery_error_code = models.IntegerField(
        _("Delivery error code"),
        null=True,
        blank=True,
        help_text=_("The delivery error code of the message, as specified here: "
                    "<https://postmarkapp.com/developer/api/overview#error-codes>"),
    )
    delivery_message = models.CharField(
        _("Delivery message"),
        max_length=255,
        blank=True,
        help_text=_("The response message from Postmark")
    )

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ['-date']

    def update_delivery_status(self):
        """
        Updates the message delivery status upon a bounce or delivery.

        TODO: - do email addresses appearing in multiple recepient fields (or
                even multiple times in the same field) get delivered to the
                addresses multiple times?
              - do bounce and delivery email addresses have names in them, if
                they were specified that way when sending, or do they get
                changed in any way from what was in the sending header?
        """

        delivery_status = self.delivery_status

        to_emails = [email.strip() for email in self.to_emails.split(',')]
        cc_emails = [email.strip() for email in self.cc_emails.split(',')]
        if (len(cc_emails) == 1) and (cc_emails[0] == ''):
            cc_emails = []
        bcc_emails = [email.strip() for email in self.bcc_emails.split(',')]
        if (len(bcc_emails) == 1) and (bcc_emails[0] == ''):
            bcc_emails = []
        # TODO: find out if Postmark delivers (and sends webhooks for) multiple
        #       messages to email addresses specified multiple times, and if
        #       not, use "set()" here
        recipients = to_emails + cc_emails + bcc_emails
        bounces = self.bounces.all()
        deliveries = self.deliveries.all()
        if bounces and not deliveries:
            delivery_status = Message.DELIVERY_STATUS_OPTIONS['BOUNCED']
        elif deliveries:
            if (len(deliveries) == len(recipients)):
                delivery_status = Message.DELIVERY_STATUS_OPTIONS['DELIVERED']
            else:
                # TODO: use single query instead of loop?
                for recipient in recipients:
                    # Assumes Postmark does not deliver (and send webhooks
                    # for) multiple messages to email addresses specified
                    # multiple times
                    recipient_bounces = bounces.filter(email=recipient)
                    recipient_deliveries = deliveries.filter(email=recipient)
                    if recipient_bounces and not recepient_deliveries:
                        delivery_status = Message.DELIVERY_STATUS_OPTIONS['BOUNCED']
                        break

        if delivery_status is not self.delivery_status:
            self.delivery_status = delivery_status
            self.save()


class Bounce(models.Model):
    """
    Email bounce data.

    TODO: - make the following bounces unavailable for resending:
            - already-been-resent bounces, because new messages are created
              upon resending
            - bounces with inactive email addresses
            - bounces whose messages were later delivered
    """

    raw_data = models.TextField(
        _("Raw data"),
        help_text=_("The raw bounce data, in JSON format")
    )
    message = models.ForeignKey(
        'Message',
        verbose_name=_("Message"),
        on_delete=models.CASCADE,
        related_name='bounces',
        help_text=_("The message the bounce is for")
    )
    bounce_id = models.BigIntegerField(
        _("Bounce ID"),
        unique=True,
        help_text=_("The ID of the bounce, as set by Postmark"),
    )
    email = models.TextField(
        _("Email address"),
        help_text=_("The email address the bounce is for")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("When the bounce happened")
    )
    type_code = models.IntegerField(
        _("Type code"),
        help_text=_("The type code of the bounce, as specified here: "
                    "<https://postmarkapp.com/developer/api/bounce-api#bounce-types>"),
    )
    is_inactive = models.BooleanField(
        _("Is inactive"),
        help_text=_("If the bounce caused the email address to be deactivated")
    )
    can_activate = models.BooleanField(
        _("Can activate"),
        help_text=_("If the email address can be activated again")
    )
    has_been_resent = models.BooleanField(
        _("Has been resent"),
        default=False,
        help_text=_("If the message has been resent, in response to the bounce")
    )
    has_been_delivered = models.BooleanField(
        _("Has been delivered"),
        default=False,
        help_text=_("If the message has been delivered, after the bounce "
                    "happened")
    )

    class Meta:
        verbose_name = _("bounce")
        verbose_name_plural = _("bounces")
        ordering = ['-date']


class Delivery(models.Model):
    """
    Email message delivery data.
    """

    raw_data = models.TextField(
        _("Raw data"),
        help_text=_("The raw delivery data, in JSON format")
    )
    message = models.ForeignKey(
        'Message',
        verbose_name=_("Message"),
        on_delete=models.CASCADE,
        related_name='deliveries',
        help_text=_("The message the delivery is for")
    )
    email = models.TextField(
        _("Email address"),
        help_text=_("The email address the delivery is to")
    )
    date = models.DateTimeField(
        _("Date"),
        help_text=_("When the delivery was made")
    )

    class Meta:
        verbose_name = _("delivery")
        verbose_name_plural = _("deliveries")
        unique_together = ('message', 'email')
        ordering = ['-date']

    def update_bounce_has_been_delivered(self):
        """
        Updates the flag indicating a bounce has been delivered, upon a
        delivery.

        TODO: - do email addresses appearing in multiple recepient fields (or
                even multiple times in the same field) get delivered to the
                addresses multiple times?
              - do bounce and delivery email addresses have names in them, if
                they were specified that way when sending, or do they get
                changed in any way from what was in the sending header?
        """

        # Assumes Postmark does not deliver (and send webhooks for) multiple
        # messages to email addresses specified multiple times
        self.message.bounces.filter(email=self.email).update(has_been_delivered=True)
