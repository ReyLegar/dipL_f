"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.views import admin_authorization_page, admin_home, create_user, user_info, credit_applications, CustomTokenObtainPairView, UserInfoView, CreateCreditApplicationView, active_credits, confirm_credit, CreditListView, CreditPaymentQRView, payment_page
from django.conf import settings
from django.conf.urls.static import static
from api.views import GeneratePDFView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/get_user/', UserInfoView.as_view(), name='user_info'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/admin_page/', admin_authorization_page, name="admin_page"),
    path('api/admin_home/', admin_home, name='admin_home'),
    path('api/create_user/', create_user, name='create_user'),
    path('api/user_info/<int:user_id>/', user_info, name='user_info'),
    path('api/credit_applications/', credit_applications, name='credit_applications'),
    path('api/credit_applications_create/', CreateCreditApplicationView.as_view(), name='credit_application_create'),
    path('api/active_credits/', active_credits, name='active_credits'),
    path('api/credit_applications/<int:credit_application_id>/', confirm_credit, name='confirm_credit_application'),
    path('api/credits/', CreditListView.as_view(), name='credits'),

    path('api/credit_payment_qr/', CreditPaymentQRView.as_view(), name='credit_payment_qr'),
    path('api/payment/<int:credit_id>/', payment_page, name='payment_page'),

    path('api/generate_pdf/', GeneratePDFView.as_view(), name='generate_pdf'),





]+ static(settings.DOCUMENT_URL, document_root=settings.DOCUMENT_ROOT)
