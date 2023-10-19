from django.core.mail import send_mail


def send_activation_code(email, code):
    send_mail(
        'Py29',
        f'Привет перейди по этой ссылке чтобы активировать аккаунт: '
        f'\n\n http://localhost:8000/api/account/activate/{code}',
        'sassassas107@gmail.com',
        [email]
    )


def send_new_password(user, new_password):
    send_mail(
        'Ваш пароль успешно сбросился',
        f'Это ваш код подверждение: {new_password}'
        f'Перейдите по этой сслыке что-бы создать новый пароль код поставьте вместо current_password '
        f'\n\n localhost:8000/api/account/change_password/',
        'sassassas107@gmail.com',
        [user.email],
        fail_silently=False,
    )

