EOF
# fi

# superuser名字
USER="admin"
# superuser密码
PASS="adminzach"
# superuser邮箱
MAIL="pzk0417@gmail.com"
script="
from django.contrib.auth.models import User;
username = '$USER';
password = '$PASS';
email = '$MAIL';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password);
    print('Superuser created.');
else:
    print('Superuser creation skipped.');
"
printf "$script" | python manage.py shell