from rest_framework import serializers


class ProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=25)
    last_name = serializers.CharField(max_length=25)
    email = serializers.EmailField()
    avatar = serializers.ImageField(read_only=True)
    account_type = serializers.CharField(read_only=True)



