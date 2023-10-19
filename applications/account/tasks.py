from config.celery import app
from .utils import send_activation_code

"""
    Создания таска для того что бы благодаря celery отпавлять на email
"""

@app.task
def celery_send_activation_code(email, code):
    send_activation_code(email, code)
