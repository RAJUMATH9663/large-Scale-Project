from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
import re, random, logging

from .models import *
from .forms import *

logger = logging.getLogger(__name__)


def get_razorpay_client():
    import razorpay
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def send_otp_email(email, otp, subject=None, body=None):
    try:
        logger.info(f"Attempting to send OTP to {email}")
        send_mail(
            subject=subject or 'Your HomeServices OTP',
            message=body or f'Your OTP is: {otp}\n\nValid for 10 minutes.\n\n- HomeServices',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"✓ OTP sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"✗ Email error for {email}: {str(e)}", exc_info=True)
        print(f"✗ Email error: {e}")
        return False

def is_admin(user):
    return user.is_staff or user.is_superuser

def is_employee(user):
    return hasattr(user, 'employee')


# ════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════
def home(request):
    services   = Service.objects.filter(is_active=True)[:8]
    categories = ServiceCategory.objects.all()
    return render(request, 'home.html', {'services': services, 'categories': categories})


# ════════════════════════════════════════════════════════
#  REGISTER
# ════════════════════════════════════════════════════════
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    errors = {}

    if request.method == 'POST':
        first_name   = request.POST.get('first_name',   '').strip()
        last_name    = request.POST.get('last_name',    '').strip()
        email        = request.POST.get('email',        '').strip()
        phone        = request.POST.get('phone',        '').strip()
        password     = request.POST.get('password',     '')
        confirm_pass = request.POST.get('confirm_pass', '')

        if not first_name:
            errors['first_name'] = 'First name is required.'
        elif not re.match(r'^[a-zA-Z]+$', first_name):
            errors['first_name'] = 'First name must contain letters only. No numbers or symbols.'

        if not last_name:
            errors['last_name'] = 'Last name is required.'
        elif not re.match(r'^[a-zA-Z]+$', last_name):
            errors['last_name'] = 'Last name must contain letters only. No numbers or symbols.'

        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors['email'] = 'Enter a valid email address.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'This email is already registered. Please login.'

        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif not phone.isdigit():
            errors['phone'] = 'Phone number must contain digits only.'
        elif len(phone) != 10:
            errors['phone'] = f'Phone must be exactly 10 digits. You entered {len(phone)} digits.'
        elif phone[0] not in ('6', '7', '8', '9'):
            errors['phone'] = f'Invalid Indian number. Must start with 6, 7, 8, or 9.'

        if not password:
            errors['password'] = 'Password is required.'
        else:
            pwd_errors = []
            if len(password) < 8:
                pwd_errors.append('minimum 8 characters')
            if not re.search(r'[A-Z]', password):
                pwd_errors.append('1 uppercase letter (A-Z)')
            if not re.search(r'[a-z]', password):
                pwd_errors.append('1 lowercase letter (a-z)')
            if not re.search(r'[0-9]', password):
                pwd_errors.append('1 number (0-9)')
            if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
                pwd_errors.append('1 special character like !@#$%')
            if pwd_errors:
                errors['password'] = 'Password needs: ' + ' | '.join(pwd_errors)

        if not confirm_pass:
            errors['confirm_pass'] = 'Please confirm your password.'
        elif password and not errors.get('password') and password != confirm_pass:
            errors['confirm_pass'] = 'Passwords do not match.'

        if not errors:
            request.session['reg_data'] = {
                'first_name': first_name,
                'last_name':  last_name,
                'email':      email,
                'phone':      phone,
                'password':   password,
            }
            otp_obj = OTPVerification.generate_otp(email)
            sent    = send_otp_email(email, otp_obj.otp)
            if sent:
                messages.success(request, f'OTP sent to {email}')
            else:
                messages.info(request, f'[TEST MODE] OTP: {otp_obj.otp}')
            return redirect('verify_otp')

        return render(request, 'register.html', {
            'errors': errors,
            'post':   request.POST,
        })

    return render(request, 'register.html', {'errors': {}, 'post': {}})


def verify_otp(request):
    reg_data = request.session.get('reg_data')
    if not reg_data:
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        email       = reg_data['email']
        try:
            otp_obj = OTPVerification.objects.filter(
                email=email, otp=entered_otp, is_used=False
            ).latest('created_at')
            if otp_obj.is_valid():
                otp_obj.is_used = True
                otp_obj.save()
                username = email.split('@')[0]
                base = username; i = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base}{i}"; i += 1
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=reg_data['password'],
                    first_name=reg_data['first_name'],
                    last_name=reg_data['last_name'],
                )
                UserProfile.objects.create(
                    user=user, phone=reg_data['phone'], is_verified=True
                )
                del request.session['reg_data']
                login(request, user)
                messages.success(request, f"Welcome {user.first_name}! Account created.")
                return redirect('dashboard')
            else:
                messages.error(request, 'OTP expired. Please register again.')
        except OTPVerification.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html', {'email': reg_data.get('email', '')})


def resend_otp(request):
    reg_data = request.session.get('reg_data')
    if reg_data:
        otp_obj = OTPVerification.generate_otp(reg_data['email'])
        sent    = send_otp_email(reg_data['email'], otp_obj.otp)
        if sent:
            messages.success(request, 'New OTP sent.')
        else:
            messages.info(request, f'[TEST MODE] New OTP: {otp_obj.otp}')
    return redirect('verify_otp')


# ════════════════════════════════════════════════════════
#  LOGIN / LOGOUT
# ════════════════════════════════════════════════════════
def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username'].strip()
            pwd   = form.cleaned_data['password']
            if '@' in uname:
                try:
                    uname = User.objects.get(email=uname).username
                except User.DoesNotExist:
                    pass
            user = authenticate(request, username=uname, password=pwd)
            if user:
                login(request, user)
                if is_admin(user):    return redirect('admin_dashboard')
                if is_employee(user): return redirect('employee_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


# ════════════════════════════════════════════════════════
#  FORGOT PASSWORD
# ════════════════════════════════════════════════════════
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'forgot_password.html')
        if not User.objects.filter(email=email).exists():
            messages.error(request, 'No account found with this email.')
            return render(request, 'forgot_password.html')
        otp = str(random.randint(100000, 999999))
        request.session['reset_email']    = email
        request.session['reset_otp']      = otp
        request.session['reset_verified'] = False
        sent = send_otp_email(
            email, otp,
            subject='HomeServices — Password Reset OTP',
            body=f'Your password reset OTP is: {otp}\n\nValid for 10 minutes.\n\n- HomeServices'
        )
        if sent:
            messages.success(request, f'OTP sent to {email}')
        else:
            messages.info(request, f'[TEST MODE] Reset OTP: {otp}')
        return redirect('forgot_password_otp')
    return render(request, 'forgot_password.html')


def forgot_password_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        saved   = request.session.get('reset_otp', '')
        if entered == saved:
            request.session['reset_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'forgot_password_otp.html', {'email': email})


def reset_password(request):
    email    = request.session.get('reset_email')
    verified = request.session.get('reset_verified', False)
    if not email or not verified:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_pass', '')
        pwd_errors = []
        if len(password) < 8:
            pwd_errors.append('minimum 8 characters')
        if not re.search(r'[A-Z]', password):
            pwd_errors.append('1 uppercase (A-Z)')
        if not re.search(r'[a-z]', password):
            pwd_errors.append('1 lowercase (a-z)')
        if not re.search(r'[0-9]', password):
            pwd_errors.append('1 number (0-9)')
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
            pwd_errors.append('1 special character')
        if pwd_errors:
            messages.error(request, 'Password needs: ' + ' | '.join(pwd_errors))
            return render(request, 'reset_password.html')
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html')
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        for k in ('reset_email', 'reset_otp', 'reset_verified'):
            request.session.pop(k, None)
        messages.success(request, 'Password reset successful! Login with your new password.')
        return redirect('login')
    return render(request, 'reset_password.html')


def resend_reset_otp(request):
    email = request.session.get('reset_email')
    if email:
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        sent = send_otp_email(
            email, otp,
            subject='HomeServices — New Reset OTP',
            body=f'Your new OTP is: {otp}\n\nValid for 10 minutes.'
        )
        if sent:
            messages.success(request, 'New OTP sent.')
        else:
            messages.info(request, f'[TEST MODE] New OTP: {otp}')
    return redirect('forgot_password_otp')


# ════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════
@login_required
def dashboard(request):
    if is_admin(request.user):    return redirect('admin_dashboard')
    if is_employee(request.user): return redirect('employee_dashboard')
    bookings      = Booking.objects.filter(user=request.user).order_by('-created_at')[:5]
    complaints    = CivicComplaint.objects.filter(user=request.user).order_by('-created_at')[:3]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    services      = Service.objects.filter(is_active=True)[:6]
    return render(request, 'dashboard.html', {
        'bookings':           bookings,
        'complaints':         complaints,
        'notifications':      notifications,
        'services':           services,
        'total_bookings':     Booking.objects.filter(user=request.user).count(),
        'completed_bookings': Booking.objects.filter(user=request.user, status='completed').count(),
    })


def service_list(request):
    categories = ServiceCategory.objects.prefetch_related('services').all()
    return render(request, 'service_list.html', {'categories': categories})


# ════════════════════════════════════════════════════════
#  BOOK SERVICE
#  NO auto-assign — Admin assigns manually
# ════════════════════════════════════════════════════════
ALL_SLOTS = [
    ('10:00-11:00', '10:00 AM - 11:00 AM', 10),
    ('11:00-12:00', '11:00 AM - 12:00 PM', 11),
    ('12:00-13:00', '12:00 PM - 1:00 PM',  12),
    ('13:00-14:00', '1:00 PM  - 2:00 PM',  13),
    ('14:00-15:00', '2:00 PM  - 3:00 PM',  14),
    ('15:00-16:00', '3:00 PM  - 4:00 PM',  15),
    ('16:00-17:00', '4:00 PM  - 5:00 PM',  16),
]

@login_required
def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)

    now          = timezone.localtime(timezone.now())
    today_str    = now.strftime('%Y-%m-%d')
    current_hour = now.hour

    def build_slots(selected_date_str):
        is_today = (selected_date_str == today_str)
        result = []
        for value, label, start_hour in ALL_SLOTS:
            disabled = is_today and start_hour <= current_hour
            result.append({'value': value, 'label': label, 'disabled': disabled})
        return result

    if request.method == 'POST':
        chosen_date = request.POST.get('booking_date', today_str)
        chosen_slot = request.POST.get('time_slot', '')
        slots       = build_slots(chosen_date)

        # Block past slots server-side
        if chosen_date == today_str:
            slot_hour = next(
                (h for v, l, h in ALL_SLOTS if v == chosen_slot), None
            )
            if slot_hour is not None and slot_hour <= current_hour:
                messages.error(request,
                    f'The {chosen_slot} slot has already passed. Please choose a later slot.')
                return render(request, 'book_service.html', {
                    'service': service, 'form': BookingForm(request.POST, request.FILES),
                    'slots': slots, 'today': today_str, 'current_hour': current_hour,
                })

        form = BookingForm(request.POST, request.FILES)
        if form.is_valid():
            booking              = form.save(commit=False)
            booking.user         = request.user
            booking.service      = service
            booking.total_amount = service.price
            # ── NO auto-assign: booking waits for admin ──
            booking.status       = 'pending'
            booking.employee     = None
            booking.save()

            # ── Notify USER: booking received ────────────────────────────────
            Notification.objects.create(
                user=request.user,
                title="Booking Received",
                message=(
                    f"Your booking for {service.name} on "
                    f"{booking.booking_date} at {booking.time_slot} is received. "
                    f"Admin will assign an expert employee shortly."
                )
            )

            # ── Notify ALL ADMINS: new booking needs employee ─────────────────
            admins = User.objects.filter(is_staff=True)
            for admin_user in admins:
                Notification.objects.create(
                    user=admin_user,
                    title=f"New Booking — {service.name}",
                    message=(
                        f"New booking from {request.user.get_full_name() or request.user.username}. "
                        f"Service: {service.name} | Date: {booking.booking_date} | "
                        f"Slot: {booking.time_slot} | Address: {booking.address}. "
                        f"Please assign an employee."
                    )
                )

            messages.success(request,
                "Booking received! Please complete the payment.")
            return redirect('payment', booking_id=booking.id)

    else:
        form  = BookingForm()
        slots = build_slots(today_str)

    return render(request, 'book_service.html', {
        'service':      service,
        'form':         form,
        'slots':        slots,
        'today':        today_str,
        'current_hour': current_hour,
    })


@login_required
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if hasattr(booking, 'payment') and booking.payment.status == 'paid':
        return redirect('invoice', booking_id=booking.id)
    client       = get_razorpay_client()
    amount_paise = int(booking.total_amount * 100)
    order = client.order.create({
        'amount': amount_paise, 'currency': 'INR',
        'payment_capture': 1, 'notes': {'booking_id': str(booking.id)}
    })
    Payment.objects.update_or_create(
        booking=booking,
        defaults={'razorpay_order_id': order['id'], 'amount': booking.total_amount,
                  'status': 'created', 'is_test_mode': True}
    )
    return render(request, 'payment.html', {
        'booking': booking, 'razorpay_order_id': order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount_paise, 'amount_display': booking.total_amount,
        'is_test_mode': settings.RAZORPAY_TEST_MODE,
    })


@csrf_exempt
@login_required
def payment_success(request):
    import razorpay
    if request.method == 'POST':
        data   = request.POST
        client = get_razorpay_client()
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id':   data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature':  data.get('razorpay_signature'),
            })
            booking = get_object_or_404(Booking, id=data.get('booking_id'), user=request.user)
            pay = booking.payment
            pay.razorpay_payment_id = data.get('razorpay_payment_id')
            pay.razorpay_signature  = data.get('razorpay_signature')
            pay.status  = 'paid'
            pay.paid_at = timezone.now()
            pay.save()
            # Status stays pending — admin will assign employee after payment
            booking.status = 'pending'
            booking.save()
            total = booking.total_amount
            gst   = round(float(total) * 18 / 118, 2)
            base  = round(float(total) - gst, 2)
            Invoice.objects.get_or_create(
                booking=booking,
                defaults={'total_amount': base, 'gst_amount': gst, 'final_amount': total}
            )
            Notification.objects.create(
                user=request.user, title="Payment Successful",
                message=f"Payment of Rs.{total} received. Admin will assign your employee soon."
            )
            # Notify admins payment is done
            admins = User.objects.filter(is_staff=True)
            for admin_user in admins:
                Notification.objects.create(
                    user=admin_user,
                    title=f"Payment Done — Assign Employee",
                    message=(
                        f"{request.user.get_full_name() or request.user.username} "
                        f"paid Rs.{total} for {booking.service.name} on {booking.booking_date}. "
                        f"Please assign an employee now."
                    )
                )
            messages.success(request, "Payment successful! Admin will assign your employee shortly.")
            return redirect('my_bookings')
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return redirect('dashboard')
    return redirect('dashboard')


@login_required
def invoice(request, booking_id):
    booking     = get_object_or_404(Booking, id=booking_id, user=request.user)
    invoice_obj = get_object_or_404(Invoice, booking=booking)
    return render(request, 'invoice.html', {'booking': booking, 'invoice': invoice_obj})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})


@login_required
def rate_employee(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status='completed')
    if hasattr(booking, 'review'):
        messages.info(request, "Already reviewed.")
        return redirect('my_bookings')
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review          = form.save(commit=False)
            review.booking  = booking
            review.user     = request.user
            review.employee = booking.employee
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('my_bookings')
    else:
        form = ReviewForm()
    return render(request, 'rate_employee.html', {'booking': booking, 'form': form})


@login_required
def civic_complaint(request):
    if request.method == 'POST':
        form = CivicComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            c.save()
            messages.success(request, "Complaint submitted!")
            return redirect('my_complaints')
    else:
        form = CivicComplaintForm()
    return render(request, 'civic_complaint.html', {'form': form})


@login_required
def my_complaints(request):
    complaints = CivicComplaint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_complaints.html', {'complaints': complaints})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile_obj, initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
        })
    return render(request, 'profile.html', {'form': form, 'profile': profile_obj})


@login_required
def employee_dashboard(request):
    if not is_employee(request.user):
        return redirect('dashboard')
    emp            = request.user.employee
    all_assigned   = Booking.objects.filter(employee=emp).order_by('-created_at')
    pending_jobs   = all_assigned.filter(status__in=['confirmed', 'in_progress'])
    completed_jobs = all_assigned.filter(status='completed')
    return render(request, 'employee_dashboard.html', {
        'employee':       emp,
        'pending_jobs':   pending_jobs,
        'completed_jobs': completed_jobs,
        'total_jobs':     all_assigned.count(),
        'pending_count':  pending_jobs.count(),
        'done_count':     completed_jobs.count(),
    })


@login_required
def update_job_status(request, booking_id):
    if not is_employee(request.user):
        return redirect('dashboard')
    booking = get_object_or_404(Booking, id=booking_id, employee=request.user.employee)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        photo      = request.FILES.get('completion_photo')
        if new_status == 'in_progress' and booking.status == 'confirmed':
            booking.status = 'in_progress'
            booking.save()
            Notification.objects.create(
                user=booking.user, title="Service Started",
                message=f"Your {booking.service.name} service has started."
            )
            messages.success(request, "Job marked as In Progress.")
        elif new_status == 'completed' and booking.status == 'in_progress':
            if not photo:
                messages.error(request, "Please upload a completion photo.")
                return redirect('employee_dashboard')
            booking.status           = 'completed'
            booking.completion_photo = photo
            booking.save()
            emp = request.user.employee
            emp.total_jobs += 1
            emp.save()
            Notification.objects.create(
                user=booking.user, title="Service Completed",
                message=f"Your {booking.service.name} is done. Please rate your experience!"
            )
            messages.success(request, "Job completed!")
    return redirect('employee_dashboard')


# ════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ════════════════════════════════════════════════════════
@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:10]
    return render(request, 'admin_dashboard.html', {
        'total_users':         User.objects.filter(is_staff=False).count(),
        'total_bookings':      Booking.objects.count(),
        'total_revenue':       Payment.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,
        'pending':             Booking.objects.filter(status='pending').count(),
        # All unassigned bookings shown prominently
        'unassigned_bookings': Booking.objects.filter(
            employee__isnull=True
        ).exclude(status='cancelled').order_by('-created_at'),
        'recent_bookings':     Booking.objects.order_by('-created_at')[:20],
        'complaints':          CivicComplaint.objects.filter(status='submitted').order_by('-created_at')[:5],
        'employees':           Employee.objects.all(),
        'admin_notifications': notifications,
        'unassigned_count':    Booking.objects.filter(
            employee__isnull=True
        ).exclude(status='cancelled').count(),
    })


# ════════════════════════════════════════════════════════
#  ADMIN ASSIGN EMPLOYEE
#  Shows employees who are expert in that service
# ════════════════════════════════════════════════════════
@login_required
def admin_assign_employee(request, booking_id):
    if not is_admin(request.user):
        return redirect('dashboard')

    booking = get_object_or_404(Booking, id=booking_id)

    # ── Employees who have this service skill (experts) ──────────────────────
    expert_employees = Employee.objects.filter(
        is_available=True,
        services=booking.service
    ).order_by('user__first_name')

    # ── Other available employees (not specialists but still available) ───────
    other_employees = Employee.objects.filter(
        is_available=True
    ).exclude(
        services=booking.service
    ).order_by('user__first_name')

    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        
        # ── Validate employee_id is provided ──────────────────────────────────
        if not emp_id:
            messages.error(request, 'Please select an employee.')
            return redirect('admin_assign_employee', booking_id=booking.id)
        
        # ── Validate employee exists ──────────────────────────────────────────
        try:
            emp = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            messages.error(request, f'Employee not found. Please select a valid employee.')
            logger.warning(f"Admin tried to assign non-existent employee {emp_id} to booking {booking.id}")
            return redirect('admin_assign_employee', booking_id=booking.id)

        booking.employee = emp
        booking.status   = 'confirmed'
        booking.save()
        logger.info(f"Employee {emp.user.username} assigned to booking {booking.id}")

        # ── Notify USER: employee assigned ───────────────────────────────────
        Notification.objects.create(
            user=booking.user,
            title="Employee Assigned — Booking Confirmed!",
            message=(
                f"Great news! {emp.user.get_full_name() or emp.user.username} "
                f"has been assigned for your {booking.service.name} service. "
                f"Date: {booking.booking_date} | Slot: {booking.time_slot}. "
                f"Your booking is now confirmed."
            )
        )

        # ── Notify EMPLOYEE: new job ──────────────────────────────────────────
        Notification.objects.create(
            user=emp.user,
            title=f"New Job Assigned — {booking.service.name}",
            message=(
                f"You have been assigned a new job by admin. "
                f"Service: {booking.service.name} | "
                f"Customer: {booking.user.get_full_name() or booking.user.username} | "
                f"Date: {booking.booking_date} | Slot: {booking.time_slot} | "
                f"Address: {booking.address}"
            )
        )

        messages.success(
            request,
            f"{emp.user.get_full_name() or emp.user.username} assigned to this booking. "
            f"Employee has been notified."
        )
        return redirect('admin_dashboard')

    return render(request, 'assign_employee.html', {
        'booking':           booking,
        'expert_employees':  expert_employees,
        'other_employees':   other_employees,
    })


@login_required
def admin_resolve_complaint(request, complaint_id):
    if not is_admin(request.user):
        return redirect('dashboard')
    complaint = get_object_or_404(CivicComplaint, id=complaint_id)
    if request.method == 'POST':
        complaint.status     = request.POST.get('status', 'resolved')
        complaint.admin_note = request.POST.get('note', '')
        if complaint.status == 'resolved':
            complaint.resolved_at = timezone.now()
        complaint.save()
        messages.success(request, "Complaint updated.")
    return redirect('admin_dashboard')


@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})