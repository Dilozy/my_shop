from dotenv import load_dotenv

from my_shop.core.celery import app as celery_app


load_dotenv()
__all__ = ["celery_app"]