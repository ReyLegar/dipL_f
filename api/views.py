import base64
import datetime
from io import BytesIO
import uuid
import qrcode
import os
import requests

from rest_framework import status
from .forms import CreditConfirmationForm
from api.models import CustomUser, CreditApplication, Credit
from api.serializers import CustomTokenObtainPairSerializer, CreditApplicationSerializer

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def admin_authorization_page(request):
    if request.method == 'POST':
        phone_number = request.POST['phone_number']
        password = request.POST['password']
        personal_code = request.POST['personal_code']
        try:
            admin_user = CustomUser.objects.get(phone_number=phone_number)
            if admin_user.password == password and admin_user.personal_code == personal_code:
                request.session['admin_user_id'] = admin_user.id
                request.session['admin_user_name'] = admin_user.first_name + ' ' + admin_user.last_name
                return redirect('admin_home')
            else:
                error_message = 'Неверный номер телефона, пароль или персональный код'
                return render(request, 'admin_authorization.html', {'error_message': error_message})
        except CustomUser.DoesNotExist:
            error_message = 'Неверный номер телефона, пароль или персональный код'
        return render(request, 'admin_authorization.html', {'error_message': error_message})

    return render(request, 'admin_authorization.html')


def admin_home(request):
    if 'admin_user_id' not in request.session:
        error_message = 'Вы не авторизованы'
        return render(request, 'admin_authorization.html', {'error_message': error_message})

    admin_user = CustomUser.objects.get(id=request.session['admin_user_id'])
    admin_user_name = admin_user.first_name + ' ' + admin_user.last_name
    users = CustomUser.objects.all()
    return render(request, 'admin_home.html', {'admin_user_name': admin_user_name, 'users': users})


def create_user(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic')
        balance = request.POST.get('balance')
        document_image = request.FILES.get('document_image')
        password = request.POST.get('password')
        
        username = str(uuid.uuid4())
        
        user = CustomUser.objects.create(
            username=username,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            balance=balance,
            document_image=document_image,
            password=password,
        )
        
        return render(request, 'admin_home.html')
    else:
        return render(request, 'create_user.html')
    

def user_info(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'user_info.html', {'user': user})


def credit_applications(request):
    credit_applications = CreditApplication.objects.all()
    return render(request, 'credit_applications.html', {'credit_applications': credit_applications})


class CustomTokenObtainPairView(APIView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    

class UserInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        data = {
            'phone_number': user.phone_number,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic': user.patronymic,
            'balance': user.balance,
            'document_image': user.document_image.url if user.document_image else None,
        }
        return Response(data)
    

class CreateCreditApplicationView(APIView):
    def post(self, request):
        serializer = CreditApplicationSerializer(data=request.data)
        if serializer.is_valid():
            credit_application = serializer.save(user=request.user)
            return Response({'id': credit_application.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def active_credits(request):
    active_credits = Credit.objects.all().order_by('payment_dates')
    return render(request, 'active_credits.html', {'active_credits': active_credits})


def confirm_credit(request, credit_application_id):
    # Получаем заявку на кредит по переданному id
    try:
        credit_application = CreditApplication.objects.get(id=credit_application_id)
    except CreditApplication.DoesNotExist:
        return HttpResponseBadRequest('Неправильный id заявки на кредит')

    # Проверяем, что заявка еще не подтверждена или отклонена
    if credit_application.status != CreditApplication.PENDING:
        return HttpResponseBadRequest('Заявка на кредит уже подтверждена или отклонена')

    # Если метод запроса POST, обрабатываем форму подтверждения
    if request.method == 'POST':
        form = CreditConfirmationForm(request.POST, request.FILES)
        if form.is_valid():

            # Получаем данные из формы
            payment_period = form.cleaned_data['term']
            interest_rate = form.cleaned_data['interest_rate']

            payment_document = form.cleaned_data['document']

            # Рассчитываем платежи
            payment_dates = calculate_payment_dates(payment_period, interest_rate, credit_application.amount)

            # Создаем новый кредит и сохраняем его в базе данных
            payment_dates_str = ','.join([f"{payment['date']} ({payment['amount']})" for payment in payment_dates])
            
            new_credit = Credit.objects.create(
                user=credit_application.user,
                amount=credit_application.amount,
                payment_dates=payment_dates_str,
                image=payment_document
            )

            # Меняем статус заявки на кредит на "Одобрена"
            credit_application.status = CreditApplication.APPROVED
            credit_application.save()

            return HttpResponseRedirect(reverse('credit_applications'))

    # Если метод GET, просто отображаем форму
    else:
        form = CreditConfirmationForm()

    context = {
        'form': form,
        'credit_application': credit_application
    }
    return render(request, 'confirm_credit_application.html', context)


def calculate_payment_dates(payment_period, interest_rate, amount):
    monthly_interest_rate = interest_rate / 12

    num_payments = payment_period

    monthly_payment = amount * monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** (-num_payments))

    payment_dates = []
    date = datetime.date.today() + datetime.timedelta(days=30)
    for i in range(num_payments):
        payment_dates.append({
            'date': date.strftime('%d.%m.%Y'),
            'amount': monthly_payment
        })
        date += datetime.timedelta(days=30)

    return payment_dates


class CreditListView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        credits = Credit.objects.filter(user=user)
        active_credits = []
        for credit in credits:
            payment_dates = credit.payment_dates.split(',')
            last_payment_date = datetime.datetime.strptime(payment_dates[-1], '%d.%m.%Y').date()
            active_credits.append({
                'id': credit.id,
                'amount': credit.amount,
                'payment_dates': payment_dates,
                'image_url': request.build_absolute_uri(credit.image.url),
            })
        return Response(active_credits)


class CreditPaymentQRView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def generate_qr_code(self, payment_url):
        # Генерация QR-кода на основе URL оплаты
        qr_code = qrcode.make(payment_url)

        # Преобразование QR-кода в изображение в формате PNG и его кодирование в base64
        buffered = BytesIO()
        qr_code.save(buffered, format='PNG')
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return qr_code_base64

    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            # Получение ID кредита из параметров запроса
            credit_id = request.data.get('credit_id')

            try:
                # Логика для получения информации о кредите по его ID
                credit = Credit.objects.get(id=credit_id)

                # Логика для формирования URL оплаты
                payment_url = f"https://localhost/api/payment/{credit_id}"

                # Генерация QR-кода
                qr_code_base64 = self.generate_qr_code(payment_url)

                # Контекст для передачи данных в шаблон
                context = {
                    'amount': 100,  # Пример суммы оплаты
                    'details': f'Payment for Credit #{credit_id}',  # Пример описания платежа
                    'qr_code_base64': qr_code_base64,  # QR-код в формате base64
                }

                return Response(context, status=status.HTTP_200_OK)

            except Credit.DoesNotExist:
                return Response({'error': 'Invalid credit ID'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        

def payment_page(request, credit_id):
    # Получение информации о кредите по его ID
    credit = get_object_or_404(Credit, id=credit_id)

    if request.method == 'POST':
        # Обработка отправленной формы
        payment_amount = int(request.POST.get('payment_amount', 0))

        if payment_amount > 0 and payment_amount <= credit.amount:
            # Выполнение платежа
            credit.amount -= payment_amount
            credit.save()
            credit = Credit.objects.get(id=credit_id)
            user_id = credit.user_id

            # Обновление баланса пользователя, если пользователь существует
            try:
                user = CustomUser.objects.get(id=user_id)
                user.balance -= payment_amount
                user.save()
            except CustomUser.DoesNotExist:
                return render(request, 'payment_error.html')

            return render(request, 'payment_success.html')
        else:
            return render(request, 'payment_error.html')

    # Контекст для передачи данных в шаблон
    context = {
        'credit_id': credit_id,
        'amount': credit.amount,
        'details': f'Payment for Credit #{credit_id}',
    }

    return render(request, 'credit_payment.html', context)


import os
import requests
from io import BytesIO
from PIL import Image
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class GeneratePDFView(APIView):

    def post(self, request):
        # Получение данных из запроса
        credit_data = request.data
        # Создание объекта BytesIO для сохранения PDF
        buffer = BytesIO()
        credit_id = credit_data['id']
        u_c = get_object_or_404(Credit, id=credit_id)
        font_path = os.path.join(os.path.dirname(__file__), "Roboto-Black.ttf")
        font_name = "YourFontName"
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        # Создание документа PDF с использованием reportlab
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        custom_style = styles['Normal']
        custom_style.fontName = 'YourFontName'
        custom_style.fontSize = 14
        custom_style.bold = False  # Установка значения False для атрибута bold


        # Создание стиля для абзаца и таблицы
        styles = getSampleStyleSheet()
        style_title = styles['Normal']
        style_normal = styles['Normal']
        # style_table = TableStyle([
        #     ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        #     ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        #     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        #     ('FONTNAME', (0, 0), (-1, 0), font_name),  # Используется шрифт Helvetica
        #     ('FONTSIZE', (0, 0), (-1, 0), 12),
        #     ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        #     ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        #     ('GRID', (0, 0), (-1, -1), 1, colors.black)
        # ])

        # Формирование информации о общей сумме
        total_amount = credit_data['amount']
        amount = 1000
        total_amount_text = f"Сумма долга: {amount}"
        user_credit_name = f"Плательщик: {u_c.user.last_name} {u_c.user.first_name} {u_c.user.patronymic}"
        bank = "Наименование организации: SBERBANK"


        poluchatel = "SBER"
        number_scheta = "00000000000000000000"
        name_bank_poluchatel = "SBER"
        BIK = "044525974"
        kor_schet = "30111810400100000023"
        nazn = "Оплата"

        sum = 1000
        # Формирование данных таблицы
        data = [['Номер даты', 'Дата']]
        payment_dates = credit_data['payment_dates']  # Прямой порядок элементов
        for i, date in enumerate(payment_dates):
            data.append([f'Date {i + 1}', date])

        # Создание таблицы
        # table = Table(data)
        # table.setStyle(style_table)

        url_qr = f"https://createqr.ru/api/v1/qr-pay?Name={poluchatel}&PersonalAcc={number_scheta}&BankName={name_bank_poluchatel}&BIC={BIK}&CorrespAcc={kor_schet}&SumRub={sum}&Purpose={nazn}"

        response = requests.get(url_qr)

        image_bytes = response.content
        image = Image.open(BytesIO(image_bytes))

        buffer2 = BytesIO()
        image.save(buffer2, format='PNG')
        buffer2.seek(0)


        rl_image = RLImage(buffer2, width=100, height=100)
        custom_style.leftIndent = 1.5 * inch  # Задайте нужный отступ в дюймах
        
        elements = [
            Image(rl_image, width=100, height=100, hAlign="LEFT"),

            Paragraph("Организация получатель платежа: SBERBANK", custom_style),
            Spacer(1, 12),  
            Paragraph("ИНН: 7840473679", custom_style),
            Spacer(1, 12),  
            Paragraph("КПП: 770201001", custom_style),
            Spacer(1, 12),  
            Paragraph("Р/С: 40701810610310004455", custom_style),
            Spacer(1, 12),  
            Paragraph("БИК: 044525411", custom_style),
            Spacer(1, 12),  
            Paragraph("К/С: 30101810145250000411", custom_style),
            Spacer(1, 12),  
            Paragraph("Адрес плательщика: ул.Московская д.1", custom_style),
            Spacer(1, 12),  
            Paragraph(user_credit_name, custom_style),
            Spacer(1, 12),  
            Paragraph(bank, custom_style),
            Spacer(1, 12), 
            Paragraph("Сумма платежа: 1000 руб 00 коп" ,custom_style),
            Spacer(1, 12), 
            Spacer(1, 12),  
            Paragraph("Подпись:___________ Дата: \"___\" ___________ 20__г." ,custom_style),

        ]

        doc.build(elements)

        # Получение содержимого PDF из буфера
        buffer.seek(0)
        pdf = buffer.getvalue()
        buffer.close()

        # Отправка PDF как ответа от API
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="credit_document.pdf"'
        response.content = pdf

        return response
