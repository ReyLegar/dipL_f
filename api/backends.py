from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class PhoneNumberBackend(BaseBackend):
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            if phone_number:
                user = UserModel.objects.get(phone_number=phone_number)
            elif password:
                user = UserModel.objects.get(password=password)
            else:
                return None
        except UserModel.DoesNotExist:
            return None

        if user.password == password:
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
