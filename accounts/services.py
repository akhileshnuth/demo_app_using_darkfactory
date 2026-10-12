"""Atomic, dependency-free two-factor account operations."""

import base64
import hashlib
import hmac
import secrets
import struct
import time

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .models import ActivityLog, BackupCode, TwoFactorAuth, TwoFactorEnrollment


def _secret():
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_code(secret, timestamp=None):
    timestamp = int(time.time() if timestamp is None else timestamp)
    counter = timestamp // 30
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7fffffff) % 1000000
    return f"{number:06d}"


def verify_totp(secret, code, timestamp=None):
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return False
    now = int(time.time() if timestamp is None else timestamp)
    return any(hmac.compare_digest(totp_code(secret, now + drift), code) for drift in (-30, 0, 30))


def provisioning_uri(user, secret):
    return f"otpauth://totp/Vault:{user.email}?secret={secret}&issuer=Vault"


@transaction.atomic
def start_enrollment(user):
    TwoFactorEnrollment.objects.filter(user=user, completed_at__isnull=True).delete()
    enrollment = TwoFactorEnrollment.objects.create(
        user=user, secret=_secret(), expires_at=timezone.now() + timezone.timedelta(minutes=10)
    )
    return enrollment, provisioning_uri(user, enrollment.secret)


@transaction.atomic
def complete_enrollment(user, enrollment, code):
    if enrollment.user_id != user.id or enrollment.completed_at or enrollment.expires_at <= timezone.now():
        return False
    if not verify_totp(enrollment.secret, code):
        ActivityLog.objects.create(user=user, event_type=ActivityLog.EventType.TWO_FACTOR_FAILED, description="Two-factor enrollment failed.")
        return False
    TwoFactorAuth.objects.update_or_create(user=user, defaults={"secret": enrollment.secret, "enabled": True})
    enrollment.completed_at = timezone.now()
    enrollment.save(update_fields=["completed_at"])
    BackupCode.objects.filter(user=user).delete()
    codes = [secrets.token_hex(5) for _ in range(10)]
    BackupCode.objects.bulk_create([BackupCode(user=user, code_hash=make_password(code)) for code in codes])
    ActivityLog.objects.create(user=user, event_type=ActivityLog.EventType.TWO_FACTOR_ENABLED, description="Two-factor login enabled.")
    return codes


@transaction.atomic
def verify_login_factor(user, code):
    factor = TwoFactorAuth.objects.filter(user=user, enabled=True).first()
    if not factor:
        return True
    if factor.locked_until and factor.locked_until > timezone.now():
        return False
    valid = verify_totp(factor.secret, code)
    if not valid:
        backup = next((item for item in BackupCode.objects.select_for_update().filter(user=user, used_at__isnull=True) if check_password(code or "", item.code_hash)), None)
        if backup:
            backup.used_at = timezone.now()
            backup.save(update_fields=["used_at"])
            valid = True
    ActivityLog.objects.create(
        user=user,
        event_type=ActivityLog.EventType.TWO_FACTOR_VERIFIED if valid else ActivityLog.EventType.TWO_FACTOR_FAILED,
        description="Two-factor login verified." if valid else "Two-factor login failed.",
    )
    if valid:
        if factor.failed_attempts or factor.locked_until:
            factor.failed_attempts = 0
            factor.locked_until = None
            factor.save(update_fields=["failed_attempts", "locked_until"])
    else:
        factor.failed_attempts += 1
        if factor.failed_attempts >= 5:
            factor.locked_until = timezone.now() + timezone.timedelta(minutes=5)
        factor.save(update_fields=["failed_attempts", "locked_until"])
    return valid


@transaction.atomic
def disable_two_factor(user):
    factor = TwoFactorAuth.objects.filter(user=user).first()
    if not factor:
        return False
    factor.enabled = False
    factor.save(update_fields=["enabled", "updated_at"])
    BackupCode.objects.filter(user=user).delete()
    ActivityLog.objects.create(user=user, event_type=ActivityLog.EventType.TWO_FACTOR_DISABLED, description="Two-factor login disabled.")
    return True
