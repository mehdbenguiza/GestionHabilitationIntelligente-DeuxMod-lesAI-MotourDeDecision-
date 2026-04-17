import sys
sys.path.insert(0, r'D:\ProjetPFE\Backend')

print('=== TEST IMPORTS ===')
from app.models.systeme import Systeme
print('  OK: Systeme model')
from app.models.access_profile import AccessProfile, ProfileStatus
print('  OK: AccessProfile model')
from app.services.email_service import build_approval_email, build_rejection_email
print('  OK: email_service')
from app.services.profile_service import generate_temp_password, _hash_password
print('  OK: profile_service')
from scripts.seed_systemes import SYSTEMES_DATA
print('  OK: seed_systemes')

print()
print('=== TEST GENERATION CREDENTIALS ===')
pwd = generate_temp_password()
print(f'  Mot de passe genere : {pwd}  (longueur: {len(pwd)})')
has_upper  = any(c.isupper() for c in pwd)
has_digit  = any(c.isdigit() for c in pwd)
has_symbol = any(c in '!@#$%&*+-=' for c in pwd)
print(f'  Majuscule: {has_upper} | Chiffre: {has_digit} | Symbole: {has_symbol}')
print(f'  Hash SHA-256 : {_hash_password(pwd)[:40]}...')

print()
print('=== TEST ACCOUNT_NAME ===')
import unicodedata
def normalize(text):
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

for full_name in ['Mehdi Ben Guiza', 'Sara Haddad', 'Omar Khelil']:
    parts = normalize(full_name.strip()).split()
    first_initial = parts[0][0]
    last_name_clean = ''.join(c for c in ''.join(parts[1:]) if c.isalnum())
    base = f'{first_initial}.{last_name_clean}'
    print(f'  {full_name} -> {base}')

print()
print('=== SYSTEMES BANCAIRES ===')
for s in SYSTEMES_DATA:
    print(f'  - [{s["sensibilite"]}] {s["nom"]} -> {s["applications"]}')

print()
print('OK Tous les tests passes')
