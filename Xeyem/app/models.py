from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    
class Dashboard(models.Model):
    user_id             = models.ForeignKey(User, on_delete=models.CASCADE)
    name                = models.CharField(max_length=50)
    default_dashboard   = models.BooleanField(default=False)
    balance             = models.BooleanField(default=True)
    balance_time        = models.BooleanField(default=True)
    fst_lst_transaction = models.BooleanField(default=True)
    transactions        = models.BooleanField(default=True)
    transactions_stats  = models.BooleanField(default=True)
    related_addresses   = models.BooleanField(default=True)
    illegal_activity    = models.BooleanField(default=True)
    web_appereances     = models.BooleanField(default=True)
    
    
class Search(models.Model):
    user_id         = models.ForeignKey(User, on_delete=models.CASCADE)
    wallet_address  = models.CharField(max_length=100)
    search_date     = models.DateTimeField(auto_now=True)
    notes           = models.CharField(max_length=500, null=True ,blank=True)
    
