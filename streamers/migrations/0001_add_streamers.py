# Generated by Django 3.2.4 on 2021-06-11 18:27

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Streamer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Le nom d'affichage du/de la streamer⋅euse", max_length=128, verbose_name='Nom du streamer')),
                ('twitch_login', models.CharField(help_text='Utilisé pour récupérer les informations automatiquement', max_length=64, verbose_name="Le nom d'utilisateur Twitch exact")),
                ('description', models.CharField(help_text="Une courte description affichée par exemple sur la page d'accueil", max_length=512, verbose_name='Courte description')),
                ('long_description', models.TextField(help_text='Description potentiellement très longue affichée sur la page du streamer ou de la streameuse', verbose_name='Longue description')),
                ('live', models.BooleanField(help_text='Est-iel en live actuellement ? Mis à jour automatiquement', verbose_name='Est en live actuellement')),
                ('live_title', models.CharField(blank=True, default=None, help_text='Le titre du live en cours, récupéré automatiquement depuis Twitch', max_length=140, null=True, verbose_name='Titre du live')),
                ('live_game_name', models.CharField(blank=True, default=None, help_text='La catégorie du live en cours, récupéré automatiquement depuis Twitch', max_length=140, null=True, verbose_name='Catégorie du stream')),
                ('user', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Compte interne du streamer')),
            ],
        ),
    ]
