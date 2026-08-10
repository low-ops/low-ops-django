from django.db.models import Max, Q
from django.utils import timezone

from users.auth_core import is_admin_role
from users.models import Account, Session, User


def avatar_url(user_id, image):
    if not image:
        return ''
    if image.startswith('http://') or image.startswith('https://'):
        return image
    return f'/api/user/avatar/{user_id}/'


def get_users(*, limit=10, offset=0, sort_by=None, sort_direction=None,
              role=None, status=None, email=None, name=None):
    qs = User.objects.all()

    if role and role != 'all':
        qs = qs.filter(role=role)

    if status == 'banned':
        qs = qs.filter(banned=True)
    elif status == 'active':
        qs = qs.filter(Q(banned=False) | Q(banned__isnull=True))

    if email:
        qs = qs.filter(email__icontains=email)

    if name:
        qs = qs.filter(name__icontains=name)

    sort_map = {
        'name': 'name',
        'email': 'email',
        'role': 'role',
        'createdAt': 'created_at',
    }
    order_field = sort_map.get(sort_by or '', 'created_at')
    prefix = '-' if sort_direction == 'desc' else ''
    qs = qs.order_by(f'{prefix}{order_field}')

    total = qs.count()
    users = list(qs[offset:offset + limit])
    user_ids = [user.id for user in users]

    accounts = Account.objects.filter(user_id__in=user_ids).values('user_id', 'provider_id')
    accounts_by_user = {}
    for row in accounts:
        accounts_by_user.setdefault(row['user_id'], []).append(row['provider_id'])

    last_sign_in = (
        Session.objects.filter(user_id__in=user_ids)
        .values('user_id')
        .annotate(last_sign_in=Max('created_at'))
    )
    last_sign_in_by_user = {row['user_id']: row['last_sign_in'] for row in last_sign_in}

    payload = []
    for user in users:
        payload.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'verified': user.email_verified,
            'role': user.role or 'user',
            'banned': bool(user.banned),
            'banReason': user.ban_reason or '',
            'banExpires': user.ban_expires,
            'accounts': accounts_by_user.get(user.id, []),
            'lastSignIn': last_sign_in_by_user.get(user.id),
            'createdAt': user.created_at,
            'avatarUrl': avatar_url(user.id, user.image),
        })

    return {'users': payload, 'total': total}


def ban_user(user_id, ban_reason='', ban_expires_in=None):
    user = User.objects.get(pk=user_id)
    user.banned = True
    user.ban_reason = ban_reason or 'Spamming'
    if ban_expires_in:
        user.ban_expires = timezone.now() + timezone.timedelta(seconds=ban_expires_in)
    else:
        user.ban_expires = None
    user.save(update_fields=['banned', 'ban_reason', 'ban_expires', 'updated_at'])
    Session.objects.filter(user_id=user_id).delete()
    return user


def unban_user(user_id):
    user = User.objects.get(pk=user_id)
    user.banned = False
    user.ban_reason = None
    user.ban_expires = None
    user.save(update_fields=['banned', 'ban_reason', 'ban_expires', 'updated_at'])
    return user


def set_user_role(user_id, role):
    user = User.objects.get(pk=user_id)
    user.role = role
    user.save(update_fields=['role', 'updated_at'])
    return user


def delete_user_record(user_id):
    from users.views.avatar_api import delete_avatar

    user = User.objects.get(pk=user_id)
    delete_avatar(user.image)
    user.delete()


def is_user_admin(user):
    return is_admin_role(getattr(user, 'role', None))
