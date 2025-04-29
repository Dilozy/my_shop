from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(
            self,
            phone_number: str,
            email: str,
            first_name: str,
            last_name: str,
            password: str = None,
            **extra_fields
    ):
        
        required_fields = {
            "номер телефона": phone_number,
            "пароль": password,
            "имя": first_name,
            "фамилию": last_name,
            "e-mail": email,
        }
        
        for field, value in required_fields.items():
            if not value:
                raise ValueError(f"Необходимо ввести {field}")
        
        user = self.model(phone_number=phone_number,
                          email=self.normalize_email(email),
                          first_name=first_name,
                          last_name=last_name,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(
            self,
            phone_number: str,
            email: str,
            first_name: str,
            last_name: str,
            password: str = None,
            **extra_fields
    ):
        
        user = self.create_user(phone_number,
                                email,
                                first_name,
                                last_name,
                                password=password,
                                **extra_fields)
        user.is_admin = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
