from itertools import product
from unicodedata import category

from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import serialize
from .models import Category, Product,Seller
from .serializers import CategorySerializer, ProductSerializer, CheckoutSerializer
from .models import Review
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import ReviewSerializer
from apps.profiles.models import OrderItem, ShippingAddress, Order
from apps.shop.serializers import OrderItemSerializer, ToggleCartItemSerializer,OrderSerializer
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

from apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE
from apps.shop.filters import ProductFilter
from ..common.paginations import CustomPagination
from ..common.permissions import IsOwner

# Create your views here.


tags=["Shop"]

class CategoriesView(APIView):

    serializer_class = CategorySerializer

    @extend_schema(
        summary="Categories Fetch",
        description="This endpoint returns all categories",
        tags=tags

    )
    def get(self,request,*args,**kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories,many=True)
        return Response(serializer.data,status=200)

    @extend_schema(
        summary="Categories",
        description="This endpoint creates categories",
        tags=tags
    )
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data,status=201)
        return Response(serializer.errors,status=401)



class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Category Products Fetch",
        description="""
            This endpoint returns all products in a particular category.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(data={"message": "Category does not exist!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

class ProductsView(APIView):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
            This endpoint returns all products.
        """,
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        filterset = ProductFilter(request.query_params,queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response(filterset.errors,status=400)

class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
            This endpoint returns all products in a particular seller.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(data={"message": "Seller does not exist!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True,)
        return Response(data=serializer.data, status=200)

class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Product Details Fetch",
        description="""
            This endpoint returns the details for a product via the slug.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)


class CartView(APIView):
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary="Cart Items Fetch",
        description="""
            This endpoint returns all items in a user cart.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user")
        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Toggle Item in cart",
        description="""
            This endpoint allows a user or guest to add/update/remove an item in cart.
            If quantity is 0, the item is removed from cart
        """,
        tags=tags,
        request=ToggleCartItemSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=data["slug"])
        if not product:
            return Response({"message": "No Product with that slug"}, status=404)
        orderitem, created = OrderItem.objects.update_or_create(
            user=user,
            order_id=None,
            product=product,
            defaults={"quantity": quantity},
        )
        resp_message_substring = "Updated In"
        status_code = 200
        if created:
            status_code = 201
            resp_message_substring = "Added To"
        if orderitem.quantity == 0:
            resp_message_substring = "Removed From"
            orderitem.delete()
            data = None
        if resp_message_substring != "Removed From":
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(data={"message": f"Item {resp_message_substring} Cart", "item": data}, status=status_code)


class  CheckoutView(APIView):
    serializer_class = CheckoutSerializer


    @extend_schema(
        summary="Checkout",
        description="""
               This endpoint allows a user to create an order through which payment can then be made through.
               """,
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self,request,*args,**kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user,order=None)
        if not orderitems.exists():
            return Response({"message":"No items in Cart"})

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_id = data.get("shipping_id")
        if shipping_id:
            shipping = ShippingAddress.objects.get_or_none(shipping_id=shipping_id)
            if not shipping:
                return Response({"message":"No shipping address"})


        fields_to_update = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        ]

        data ={}

        for field in fields_to_update:
            value = getattr(shipping,field)
            data[field] = value

        order=Order.objects.create(user=user,**data)
        orderitems.update(order=order)

        serializer = OrderSerializer(order)
        return Response({"message": "Checkout Successful", "item": serializer.data}, status=200)



class ReviewView(APIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsOwner]

    def get_object(self,request,*args,**kwargs):
        try:
            product = Product.objects.get_or_none(slug=kwargs["slug"])
            return product
        except product.DoesNotExist:
            return Response(data={"message":"Product does not exist!"})


    @extend_schema(
        summary="Get a review",
        description="This endpoint allows to get all reviews for this product",
        tags=tags,
    )

    def get(self,request,*args,**kwargs):
        product = self.get_object(request,*args,**kwargs)
        reviews = Review.objects.select_related("user","product","product__category").filter(product=product)
        if reviews.exists():
            serializer = self.serializer_class(reviews,many=True)
            return Response(data=serializer.data,status=200)
        return Response(data={"message":"No reviews for this product!"})



    @extend_schema(
        summary="Create a review",
        description="This endpoint allows to create a review to the product",
        tags=tags
    )
    def post(self,request,*args,**kwargs):
        user = request.user
        product = self.get_object(request, *args, **kwargs)
        review = Review.objects.get_or_none(product=product,user=user)
        if review:
            return Response(data={"message":"Only one review for the one product is allowed!"})
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            Review.objects.create(**serializer.validated_data,product=product,user=request.user)
            return Response(data=serializer.validated_data,status=201)
        return Response(data=serializer.errors)

    @extend_schema(
        summary="Update review",
        description="This endpoint allows to update a review, that has already been created",
        tags=tags
    )

    def put(self,request,*args,**kwargs):
        user = request.user
        product = self.get_object(request,*args,*kwargs)
        review = Review.objects.get_or_none(product=product,user=user)
        if not review:
            return Response(data={"message":"No such review"})
        serializer = self.serializer_class(review,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data,status=202)
        else:
            return Response(serializer.errors,status=404)

    @extend_schema(
        summary="Delete review",
        description="This endpoint allows to delete a review if you are creator or stuff member",
        tags=tags
    )

    def delete(self,request,*args,**kwargs):
        user = request.user
        product = self.get_object(request,*args,**kwargs)
        review = Review.objects.filter(product=product,user=user).first()
        if not review:
            return Response(data={"message":"No such review"})
        if review.user != user:
            return Response(data={"message":f"Access is denied! "},status=403)
        review.delete()
        return Response(status=204)







