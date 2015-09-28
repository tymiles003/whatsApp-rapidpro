from datetime import datetime
from celery.utils.log import get_task_logger
from djcelery_transactions import task
from django_redis import get_redis_connection
import time
from whatapp.app.models import Message
from whatapp.app.send_stack import YowsupSendStack

__author__ = 'kenneth'

logger = get_task_logger(__name__)


@task
def push_out(limit=30):
    """
    Get all messages in Queue
    """
    r = get_redis_connection()
    key = 'pcmmessage_in_queue'
    if not r.get(key):
        with r.lock(key, timeout=60*20):
            messages = Message.objects.filter(direction=Message.OUTGOING, status=Message.QUEUED).order_by('created_on')

            # somebody already handled these messages, move on
            if not messages:
                return
            for message in messages:
                print "[%s] Processing message %s" % (str(datetime.now()), message.text)
                msg = [message.urn, message.text]
                y = YowsupSendStack(msg)
                y.start()
                message.status = Message.SENT
                message.save()



@task
def push_to_rapidpro(messages=None):
    if not messages:
        messages = Message.objects.filter(direction=Message.INCOMING, status=Message.QUEUED).order_by('created_on')
    for message in messages:
        message.notify_rapidpro_received()
