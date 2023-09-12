from ocrmypdf import hookimpl


@hookimpl
def add_options(parser):
    print('aqui....', parser)
    pass
