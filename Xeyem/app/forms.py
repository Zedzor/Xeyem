from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth import get_user_model
from django.forms import CharField, Form

User = get_user_model()
class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields =['email','password1','password2']

class ExecuteSearchForm(Form):
    address = CharField(label='Address', max_length=100)