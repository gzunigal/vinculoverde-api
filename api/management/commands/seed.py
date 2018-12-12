# <project>/<app>/management/commands/seed.py
from django.core.management.base import BaseCommand
import random
from api.models import Organization, User
# python manage.py seed --mode=refresh


class Command(BaseCommand):
  help = "seed database for testing and development."

  def add_arguments(self, parser):
    parser.add_argument('--mode', type=str, help="Mode")

  def handle(self, *args, **options):
    self.stdout.write('seeding data...')
    run_seed(self, options['mode'])
    self.stdout.write('done.')


def create_admin():
  """Creates an admin for vinculo verde"""
  vinculo_verde = Organization(
    name='Vinculo Verde',
    short_name='VinculoVerde',
    address = '...',
    phone = '000',
    email = 'contacto@vinculoverde.cl'
  )
  vinculo_verde.save()

  User(
    username = 'admin',
    password = 'pbkdf2_sha256$120000$kCpz6TantlwZ$oD2K3WnyNeUJhWDv9lQSSERWQ8sd25QI3IJL0VBKVV4=',
    email = 'admin@vinculoverde.cl',
    national_id = '0-9',
    organization = vinculo_verde,
    is_staff = True,
    is_superuser = True,
  ).save()
  return


def run_seed(self, mode):
  """ Seed database based on mode"""

  # Creating admin
  create_admin()
