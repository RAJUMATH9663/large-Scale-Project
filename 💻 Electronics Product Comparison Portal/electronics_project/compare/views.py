from django.shortcuts import render
from .models import Product

def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})


def compare_products(request):
    product1_id = request.GET.get('product1')
    product2_id = request.GET.get('product2')

    product1 = Product.objects.get(id=product1_id) if product1_id else None
    product2 = Product.objects.get(id=product2_id) if product2_id else None

    products = Product.objects.all()

    return render(request, 'compare.html', {
        'products': products,
        'product1': product1,
        'product2': product2
    })