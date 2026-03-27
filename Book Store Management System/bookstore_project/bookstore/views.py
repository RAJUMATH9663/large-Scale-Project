from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Cart
from django.contrib.auth.decorators import login_required

def home(request):
    books = Book.objects.all()
    return render(request, 'home.html', {'books': books})


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        book=book
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.book.price * item.quantity for item in cart_items)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })