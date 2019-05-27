import csv
import os


if __name__ == '__main__':

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")
    django.setup()

if True:

    from cmj.sigad.models import Documento, Classe


if __name__ == '__main__':
    news = Documento.objects.qs_news()

    n = news.first()
    print(n.short_url())

    print(news.count())
