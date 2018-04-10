from shutil import rmtree
from sys import maxsize
from time import sleep
from xml.dom import minidom
import json
import os
import xml

from future.backports.misc import ceil
from unipath.path import Path as PathFile
import dxfgrabber

from svg.path.parser import parse_path


tags = {}


class Svg:

    def __init__(self, elemento=None):
        self.childs = []
        self.attrs = {}
        self.el = elemento

        self.minX = maxsize
        self.minY = maxsize
        self.maxX = maxsize * (-1)
        self.maxY = maxsize * (-1)

        if not elemento:
            return

        self.points = set()

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
            self.points |= el.points

    def extract_values_svg(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            self.attrs[name] = value

    def extract_values_line(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            self.attrs[name] = float(value) if name in (
                'x1', 'x2', 'y1', 'y2') else value
        self.points.add(complex(self.attrs['x1'], self.attrs['y1']))
        self.points.add(complex(self.attrs['x2'], self.attrs['y2']))

    def extract_values_g(self):
        pass

    def extract_values_ellipse(self):
        pass

    def extract_values_text(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            self.attrs[name] = float(value) if name in (
                'x', 'y', 'dx', 'dy') else value
        self.points.add(complex(self.attrs['x'], self.attrs['y']))

    def extract_values_path(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            # if name == 'd':
            #    print(value)
            try:
                self.attrs[name] = parse_path(value) if name == 'd' else value
            except:
                pass

        if 'd' not in self.attrs:
            return

        for item in self.attrs['d']:
            self.points.add(item.start)
            self.points.add(item.end)

    def extract_values_circle(self):
        attrs = self.el.attributes
        for name, value in attrs.items():
            self.attrs[name] = float(value) if name in (
                'r', 'cx', 'cy') else value
        self.points.add(complex(self.attrs['cx'], self.attrs['cy']))

    def union(self, fragments):

        for frag in fragments:
            if not self.el:
                self.el = frag.el
                for child in frag.childs:
                    self.childs.append(child)
                continue

            for child in frag.childs:
                self.childs.append(child)
                self.el.appendChild(child.el)

    def translate(self, center_point):
        for c in self.childs:
            translate_values = 'translate_{}'.format(c.el.tagName)
            assert hasattr(self, translate_values), 'Não existe {}'.format(
                translate_values)

            getattr(self, translate_values)(c, center_point)

        self.el.setAttribute('height', str(self.maxY - self.minY))
        self.el.setAttribute('width', str(self.maxX - self.minX))
        self.el.setAttribute('viewBox', '{} {} {} {}'.format(
            self.minX, self.minY, self.maxX, self.maxY))

    def translate_circle(self, c, center_point):
        p = next(iter(c.points))
        tp = p - center_point
        c.el.setAttribute("cx", str(tp.real))
        c.el.setAttribute("cy", str(tp.imag))

        self.minX = tp.real if tp.real < self.minX else self.minX
        self.minY = tp.imag if tp.imag < self.minY else self.minY
        self.maxX = tp.real if tp.real > self.maxX else self.maxX
        self.maxY = tp.imag if tp.imag > self.maxY else self.maxY

        style = c.el.getAttribute('style')
        style = style.replace('stroke-width:0;', 'stroke-width:1;')
        c.el.setAttribute('style', style)

    def translate_path(self, p, center_point):

        if 'd' not in p.attrs:
            return

        path = p.attrs['d']
        for s in path:

            s.start = s.start - center_point
            s.end = s.end - center_point

            if hasattr(s, 'control1'):
                s.control1 = s.control1 - center_point

            if hasattr(s, 'control2'):
                s.control2 = s.control2 - center_point

            self.minX = s.start.real if s.start.real < self.minX else self.minX
            self.minY = s.start.imag if s.start.imag < self.minY else self.minY
            self.maxX = s.start.real if s.start.real > self.maxX else self.maxX
            self.maxY = s.start.imag if s.start.imag > self.maxY else self.maxY

            self.minX = s.end.real if s.end.real < self.minX else self.minX
            self.minY = s.end.imag if s.end.imag < self.minY else self.minY
            self.maxX = s.end.real if s.end.real > self.maxX else self.maxX
            self.maxY = s.end.imag if s.end.imag > self.maxY else self.maxY

        p.el.setAttribute('d', path.d())

        style = p.el.getAttribute('style')
        style = style.replace('stroke-width:0;', 'stroke-width:1;')
        p.el.setAttribute('style', style)

    def translate_line(self, l, center_point):
        l.attrs['x1'] = l.attrs['x1'] - center_point.real
        l.attrs['x2'] = l.attrs['x2'] - center_point.real
        l.attrs['y1'] = l.attrs['y1'] - center_point.imag
        l.attrs['y2'] = l.attrs['y2'] - center_point.imag

        self.minX = l.attrs['x1'] if l.attrs['x1'] < self.minX else self.minX
        self.minY = l.attrs['y1'] if l.attrs['y1'] < self.minY else self.minY
        self.maxX = l.attrs['x1'] if l.attrs['x1'] > self.maxX else self.maxX
        self.maxY = l.attrs['y1'] if l.attrs['y1'] > self.maxY else self.maxY

        self.minX = l.attrs['x2'] if l.attrs['x2'] < self.minX else self.minX
        self.minY = l.attrs['y2'] if l.attrs['y2'] < self.minY else self.minY
        self.maxX = l.attrs['x2'] if l.attrs['x2'] > self.maxX else self.maxX
        self.maxY = l.attrs['y2'] if l.attrs['y2'] > self.maxY else self.maxY

        l.el.setAttribute('x1', str(l.attrs['x1']))
        l.el.setAttribute('x2', str(l.attrs['x2']))
        l.el.setAttribute('y1', str(l.attrs['y1']))
        l.el.setAttribute('y2', str(l.attrs['y2']))

        style = l.el.getAttribute('style')
        style = style.replace('stroke-width:0;', 'stroke-width:1;')
        l.el.setAttribute('style', style)

    def translate_g(self, g, center_point):
        for i in g.childs:
            translate_values = 'translate_{}'.format(i.el.tagName)
            assert hasattr(self, translate_values), 'Não existe {}'.format(
                translate_values)

            getattr(self, translate_values)(i, center_point)


class Quadrado(object):

    def __init__(self, center_point, length=1000):
        l = length / 2
        cp = center_point
        self.top_left = complex(cp.real - l, cp.imag - l)
        self.top_right = complex(cp.real - l, cp.imag + l)
        self.bottom_left = complex(cp.real + l, cp.imag - l)
        self.bottom_right = complex(cp.real + l, cp.imag + l)
        self.diagonal = abs(self.top_left - self.bottom_right)

    def tem_pontos_internos(self, svg):
        for point in svg.points:
            if abs(point - self.top_left) > self.diagonal or\
                    abs(point - self.top_right) > self.diagonal or\
                    abs(point - self.bottom_left) > self.diagonal or\
                    abs(point - self.bottom_right) > self.diagonal:
                return False
        return True

    def __iter__(self):
        return self

    def __contains__(self, point):
        if abs(point - self.top_left) > self.diagonal or\
                abs(point - self.top_right) > self.diagonal or\
                abs(point - self.bottom_left) > self.diagonal or\
                abs(point - self.bottom_right) > self.diagonal:
            return False
        return True


class SvgMatrix(object):

    def __init__(self, filename, fragmentar=False):
        self.filename = PathFile(filename)
        self.folderbase = self.filename.ancestor(1).child(
            'data__{}'.format(self.filename.name))

        if fragmentar:
            self.fragmentar()

    def create_fragment_file(self, center_point=0 + 0j, length=1000):
        fragments = set()
        quad = Quadrado(center_point, length)

        folder_index = self.folderbase.ancestor(1).child(
            "index__{}".format(self.filename.name))
        if not os.path.exists(folder_index):
            os.makedirs(folder_index)

        indexfile = folder_index.child('index.json')

        data = []
        with open(indexfile) as json_file:
            data = json.load(json_file)

        for point in data:
            p = point['x'] + point['y'] * 1j
            if p in quad:
                fragments.add(point['f'])

        if fragments:
            fragments_svg = []
            for f in fragments:
                folder_child = self.folderbase.child(
                    "{num:06d}".format(num=int(int(f) / 1000)))

                namefile = "{folder:s}/{namefile:s}.{num}".format(
                    folder=folder_child,
                    namefile=self.filename.name,
                    num=f)

                svgdom = minidom.parse(namefile)
                svg = Svg(svgdom.documentElement)
                fragments_svg.append(svg)

            fragment = Svg()
            fragment.union(fragments_svg)
            fragment.translate(center_point)

            namefile = self.folderbase.ancestor(1).child('teste.svg')

            doc = minidom.Document()
            doc.appendChild(fragment.el)
            doc.writexml(open(namefile, 'w'))

        """                    
        for dirpath, dirnames, filenames in os.walk(self.folderbase):

            for file in filenames:
                svgdom = minidom.parse('{}/{}'.format(dirpath, file))
                svg = Svg(svgdom.documentElement)

                if not center_point:
                    center_point = complex(float(svg.attrs['width']) / 2,
                                           float(svg.attrs['height']) / 2)
                    quad = Quadrado(center_point, length)

                if quad.tem_pontos_internos(svg):
                    fragments.append(svg)
                   print('capturado...', file)
                else:
                    print('............', file)
            if len(fragments) > 20:
                break
            sleep(15)"""

    def indexar(self):
        folder_index = self.folderbase.ancestor(1).child(
            "index__{}".format(self.filename.name))
        if not os.path.exists(folder_index):
            os.makedirs(folder_index)

        namefile = folder_index.child('index.json')

        """doc = minidom.Document()
        root = doc.createElement('index')
        doc.appendChild(root)"""

        count = 0
        points = set()

        for dirpath, dirnames, filenames in os.walk(self.folderbase):
            for file in filenames:
                if not count % 1000:
                    print(count)
                count += 1
                svgdom = minidom.parse('{}/{}'.format(dirpath, file))
                svg = Svg(svgdom.documentElement)

                number = file.rsplit('.', 1)[-1]

                for c in svg.childs:
                    for p in c.points:
                        points.add((p, number))

        points_dict = []
        for p, f in points:
            point = {
                'x':  p.real,
                'y': p.imag,
                'f': int(f)
            }
            points_dict.append(point)
            """
            pxml = doc.createElement('p')
            pxml.setAttribute('x',)
            pxml.setAttribute('y', str(p.imag))
            pxml.setAttribute('f', number)
            root.appendChild(pxml)"""

        with open(namefile, 'w') as f:
            json.dump(points_dict, f)

        # doc.writexml()

    def fragmentar(self):

        if os.path.exists(self.folderbase):
            rmtree(self.folderbase)
            os.makedirs(self.folderbase)

        svgdom = minidom.parse(self.filename)
        svgNode = svgdom.documentElement

        number_file = 0
        for nivel1 in svgNode.childNodes:
            if nivel1.nodeType in (nivel1.TEXT_NODE, nivel1.COMMENT_NODE):
                continue

            for cn in nivel1.childNodes:
                if cn.nodeType in (cn.TEXT_NODE, cn.COMMENT_NODE):
                    continue

                folder_child = self.folderbase.child(
                    "{num:06d}".format(
                        num=int(number_file / 1000))
                )
                if not os.path.exists(folder_child):
                    os.makedirs(folder_child)

                namefile = "{folder:s}/{namefile:s}.{num:06d}".format(
                    folder=folder_child,
                    namefile=self.filename.name,
                    num=number_file)

                doc = minidom.Document()
                root = doc.createElement('svg')
                doc.appendChild(root)

                for name, value in svgNode.attributes.items():
                    root.setAttribute(name, value)

                svg = doc.importNode(cn, True)
                root.appendChild(svg)
                doc.writexml(open(namefile, 'w'))
                number_file += 1

    @property
    def width(self):
        return self.svgdom.documentElement.getAttribute('width')

    @property
    def height(self):
        return self.svgdom.documentElement.getAttribute('height')


if __name__ == "__main__2":
    sm = SvgMatrix('/home/leandro/Documentos/mapa_jatai/'
                   'Zoneamento Mapa Jatai_teste3.svg',
                   fragmentar=False)

    # sm.indexar()
    sm.create_fragment_file(
        center_point=425659 + 8022341j,
        length=500)

    print(tags)


if __name__ == "__main__":
    dxf = dxfgrabber.readfile('/home/leandro/Documentos/mapa_jatai/'
                              'Zoneamento Mapa Jatai.dxf')
    print("DXF version: {}".format(dxf.dxfversion))
    header_var_count = len(dxf.header)  # dict of dxf header vars
    layer_count = len(dxf.layers)  # collection of layer definitions
    # dict like collection of block definitions
    block_definition_count = len(dxf.blocks)
    entity_count = len(dxf.entities)  # list like collection of entities
