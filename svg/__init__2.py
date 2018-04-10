from xml.dom import minidom
from svg.path.parser import parse_path


tags = {}


class Svg:

    def __init__(self, elemento):
        self.childs = []
        self.attrs = {}
        self.el = elemento
        self.points = []

        tags.setdefault(elemento.tagName, 0)
        tags[elemento.tagName] += 1

        extract_values = 'extract_values_{}'.format(elemento.tagName)
        assert hasattr(self, extract_values), 'Não existe {}'.format(
            extract_values)

        getattr(self, extract_values)()

        for cn in elemento.childNodes:
            if cn.nodeType in (cn.TEXT_NODE, cn.COMMENT_NODE):
                continue
            el = Svg(cn)
            self.childs.append(el)

    def extract_values_svg(self):
        pass

    def extract_values_g(self):
        pass

    def extract_values_path(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            # if name == 'd':
            #    print(value)
            self.attrs[name] = parse_path(value) if name == 'd' else value

    def extract_values_circle(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            self.attrs[name] = float(value) if name in (
                'r', 'cx', 'cy') else value
        self.points = [(self.attrs['cx'], self.attrs['cy'])]


class SvgMatrix(object):
    svgdom = None
    svg = None
    elementos = []

    def __init__(self, filename=None):
        assert filename
        self.svgdom = minidom.parse(filename)
        self.svg = Svg(self.svgdom.documentElement)

    @property
    def width(self):
        return self.svgdom.documentElement.getAttribute('width')

    @property
    def height(self):
        return self.svgdom.documentElement.getAttribute('height')


if __name__ == "__main__":
    sm = SvgMatrix(filename='/home/leandro/Documentos/mapa_jatai/'
                   'Zoneamento Mapa Jatai.svg')

    print(sm.width)
    print(sm.height)
    print(len(sm.elementos))

    print(tags)
