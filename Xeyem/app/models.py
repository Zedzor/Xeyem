from operator import mod
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
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
    user_id             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name                = models.CharField(max_length=50, default="New Dashboard")
    default_dashboard   = models.BooleanField(default=False)
    balance             = models.BooleanField(default=True)
    balance_time        = models.BooleanField(default=True)
    fst_lst_transaction = models.BooleanField(default=True)
    transactions        = models.BooleanField(default=True)
    transactions_stats  = models.BooleanField(default=True)
    related_addresses   = models.BooleanField(default=True)
    illegal_activity    = models.BooleanField(default=True)
    web_appearances     = models.BooleanField(default=True)
    
    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_default_dashbord(sender, instance, created, **kwargs):
        if created:
            Dashboard.objects.create(user_id=instance, name="Default Dashboard", default_dashboard=True)
    
    def save(self, *args, **kwargs):
        if not self.default_dashboard:
            return super(Dashboard, self).save(*args, **kwargs)
        with transaction.atomic():
            Dashboard.objects.filter(
                default_dashboard=True).update(default_dashboard=False)
            return super(Dashboard, self).save(*args, **kwargs)
        
    def get_functionalities(self):
        return [key for key, value in self.__dict__.items() if value == True and key not in ['id', 'user_id', 'name', 'default_dashboard']]
    
class Search(models.Model):
    user_id         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet_address  = models.CharField(max_length=100)
    search_date     = models.DateTimeField(auto_now=True)
    notes           = models.TextField(max_length=500, null=True ,blank=True)
    
class Entity(models.Model):
    address = models.CharField(max_length=100, primary_key=True)
    address_name = models.CharField(max_length=100, null=False)
    address_tag = models.CharField(max_length=100, null=False)
    address_country = models.CharField(max_length=40, null=True)
