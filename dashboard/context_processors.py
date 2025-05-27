from .registry import dashboard as dash


def dashboard(request):
    return {"dashboard": dash}
