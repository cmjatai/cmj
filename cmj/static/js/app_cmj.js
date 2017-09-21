function styleWithEndNameClass(endNameClass, attr, value=undefined) {
    for (var s = 0; s < document.styleSheets.length; s++) {
        var rules = document.styleSheets[s].rules || document.styleSheets[s].cssRules;
        for (var r = 0; r < rules.length;r++) {
            if (rules[r].selectorText !== undefined && rules[r].selectorText.endsWith(endNameClass)) {
                if (value === undefined)
                    return rules[r].style[attr];
                rules[r].style[attr] = value;
            }
        }
    }
}

function isElementInViewport (el) {

    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }

    var rect = el.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && /*or $(window).height() */
        rect.right <= (window.innerWidth || document.documentElement.clientWidth) /*or $(window).width() */
    );
}

function ImpressoEnderecamentoRenderer(opts) {
    $(function() {
        var ier = $('body').children(".ier");
        if (ier.length > 0)
            $(ier).remove();
        ier = $('<div class="ier"/>');
        eb = $('<div class="etiqueta"/>');

        var form = $('form');
        form.after(ier);

        var resize = function(event) {
            var largura_pagina = parseFloat(form[0].elements['largura_pagina'].value);
            var altura_pagina = parseFloat(form[0].elements['altura_pagina'].value);
            var rotate = form[0].elements['rotate'].value == 'True';

            var razao = altura_pagina / largura_pagina;
            var conversao = ier.width() / largura_pagina;
            ier.height(ier.width() * razao);

            var margem_esquerda = parseFloat(form[0].elements[rotate?'margem_superior':'margem_esquerda'].value) * conversao;
            var margem_superior = parseFloat(form[0].elements[rotate?'margem_esquerda':'margem_superior'].value) * conversao;

            var colunasfolha = parseInt(form[0].elements['colunasfolha'].value);
            var linhasfolha = parseInt(form[0].elements['linhasfolha'].value);

            var entre_colunas = parseFloat(form[0].elements[rotate?'entre_linhas':'entre_colunas'].value) * conversao;
            var entre_linhas = parseFloat(form[0].elements[rotate?'entre_colunas':'entre_linhas'].value) * conversao;

            var larguraetiqueta = parseFloat(form[0].elements[rotate?'alturaetiqueta':'larguraetiqueta'].value) * conversao;
            var alturaetiqueta = parseFloat(form[0].elements[rotate?'larguraetiqueta':'alturaetiqueta'].value) * conversao;

            var total_etiquetas = colunasfolha * linhasfolha;

            var etiquetas = $('.ier .etiqueta');
            while (etiquetas.length < total_etiquetas) {
                etiquetas.push(eb.clone())
                ier.append(etiquetas[etiquetas.length-1]);
            }
            while ($('.ier .etiqueta').length > total_etiquetas)
                $('.ier .etiqueta').last().remove();
            etiquetas = $('.ier .etiqueta');
            etiquetas.width(larguraetiqueta);
            etiquetas.height(alturaetiqueta);

            for (var i = 0; i < etiquetas.length; i++) {
                var left = margem_esquerda;
                var top = margem_superior;

                var quociente = i / colunasfolha | 0;
                var resto = i % colunasfolha;

                console.log(quociente + ' = '+ resto)

                if (resto > 0)
                    left += (resto) * entre_colunas + (resto) * larguraetiqueta;
                if (quociente > 0)
                    top += (quociente) * entre_linhas + (quociente) * alturaetiqueta;

                etiquetas[i].style.left = left + 'px';
                if (rotate)
                    etiquetas[i].style.bottom = top + 'px';
                else
                    etiquetas[i].style.top = top + 'px';
            }
        }
        $(window).resize(resize);
        form.change(resize);
        $(window).trigger('resize');
    });
}

function TrechoSearch(opts) {
    $(function() {
        var cts_clear = $('body').children(".cts"); // Container Trecho Search
        if (cts_clear.length > 0)
            $(cts_clear).remove();

        $("input[name='endereco']").each(function() {
            var input = $(this);
            var input_row_fluid = $(input.closest('.row-fluid'));
            var cts = $('<div class="cts"/>');
            var qOld = input.val();
            var qNew = input.val();
            var intervalKeyPress = null;
            input.after(cts);

            var cts_show = function(){
                var row_fluid_position = input_row_fluid[0].getBoundingClientRect();
                var input_position = input[0].getBoundingClientRect();
                cts.animate({
                    'top': input_position.bottom ,
                    'left':  input_position.left + 7,
                    'right':  row_fluid_position.right - row_fluid_position.width
                },400);
                //cts.css('top', input_position.bottom);
                //cts.css('left', input_position.left + 7);
                //cts.css('right', row_fluid_position.right - row_fluid_position.width);
            }
            var cts_hidden = function() {
                cts.css('visibility', 'hidden');
            }

            $(window).resize(cts_hidden);
            $(window).scroll(cts_hidden);

            var zoomListeners = [cts_hidden];
            var lastWidth = 0;
            var pollZoomFireEvent = function() {
              var widthNow = $(window).width();
              if (lastWidth == widthNow) return;
              lastWidth = widthNow;
              // Length changed, user must have zoomed, invoke listeners.
              for (i = zoomListeners.length - 1; i >= 0; --i) {
                zoomListeners[i]();
              }
            }
            setInterval(pollZoomFireEvent, 300);

            var flag_newkeypress = false;
            var flag_get_run_ajax = false;
            var keyUpEndereco = function() {
                if (qOld != qNew) {
                    qOld = qNew;
                    return;
                }
                if (!flag_newkeypress)
                    return;
                flag_newkeypress = false;

                if (flag_get_run_ajax)
                    return;
                flag_get_run_ajax = true;

                var formData = {
                    'q'      : qNew,
                    'format' : 'json',
                }
                $.get(opts.api_rest_list, formData).done( function(data) {
                    cts.html('');
                    cts_show();
                    cts.css('visibility', (data.results.length == 0 ? 'hidden': 'visible'));

                    $.each(data.results, function(index, item_data ) {
                        var its = $('<div class="its"/>'); // Item de Trecho Search
                        its.append(item_data.display);
                        cts.append(its);


                        its.on('click', function(event, set_data_endereco) {
                            var pk = this.data;
                            var formData = {
                                'format'            : 'json',
                            }
                            var url = opts.api_rest_retrieve;
                            url = url.replace('0', pk)
                            $.get(url, formData, function(retrivie_data) {
                                $("input[name='trecho']").val(pk);
                                if (set_data_endereco !== undefined && set_data_endereco)
                                    $("input[name='endereco']").attr('data', retrivie_data.tipo_descricao + ' ' + retrivie_data.logradouro_descricao);
                                else
                                    $("input[name='endereco']").val(retrivie_data.tipo_descricao + ' ' + retrivie_data.logradouro_descricao);
                                $("select[name='bairro']").val(retrivie_data.bairro_id);
                                $("input[name='cep']").val(retrivie_data.cep[0]);
                                $("select[name='distrito']").val(retrivie_data.distrito_id);
                                $("select[name='regiao_municipal']").val(retrivie_data.regiao_municipal_id);
                                $("select[name='municipio']").val(retrivie_data.municipio_id);
                                $("select[name='uf']").val(retrivie_data.uf);
                            });
                        });

                        its[0].data =  item_data.pk;
                        /*if (data.results.length == 1)
                            its.trigger('click', true)
                        else {
                            input.attr('data', '');
                        }*/


                    });
                }).always(function() {
                    flag_get_run_ajax = false;
                });
            };
            input.on('keyup', function() {
                //var d = new Date();
                //console.log(d.getSeconds()+'.'+d.getMilliseconds());
                if (intervalKeyPress == null)
                    intervalKeyPress = setInterval(keyUpEndereco, 700);
                flag_newkeypress = true;
                qNew = input.val();
                if (qNew == qOld || qNew.length < 3) {
                    cts.css('visibility', 'hidden');
                    return;
                }
            }).on('blur', function() {
                var input_data = $(this).attr('data');
                if (input_data !== undefined && input_data != '')
                    $(this).val(input_data);

                setTimeout(function() {
                    cts.css('visibility', 'hidden');
                },300);
            });
        });
    });
}

function Gallery() {
    var instance;
    var galerias;

    if (!(this instanceof Gallery)) {
        if (!instance) {
            instance = new Gallery();
        }
        return instance;
    }
    instance = this;
    Gallery = function() {
        return instance;
    };

    instance.intervalThumb = function() {
        var func = function () {
            instance.galerias.each(function(idx_galeria, _galeria) {
                var width = 0;
                var galeria = $(_galeria);


                galeria.find('.gallery-item').each(function(index, item) {
                    width = width + item.offsetWidth;
                });

                if (_galeria.thumbWidthOld === undefined)
                    _galeria.thumbWidthOld = width;
                else {
                    if (_galeria.thumbWidthOld === width)
                        return;
                }
                _galeria.thumbWidthOld = width;
                galeria.find('.thumb-scroll').css('width', (width+12) + 'px');
            });
          }

        func();
        setInterval(function () {
            func();
            // TODO: encerrar interval depois n interações sem mudanças
            // TODO: Avaliar necessidade de resize devido a responsividade (em dispositivos com mudanças de vertical/horizontal, por exemplo.)
        }, 2000);
    }
    instance.resize = function(e, ajustaShowImage=true) {
        instance.galerias.each(function(idx_galeria, _galeria) {
            var galeria = $(_galeria);
            var height = (window.innerWidth > window.innerHeight ? window.innerHeight * 0.9 : window.innerWidth)

            var strHeight;
            if (window.innerWidth > window.innerHeight)
                strHeight = 'height'

            else
                strHeight = 'min-height';

            var inner = galeria.find('.gallery-inner').css(strHeight, height + 'px');
            var galleryShow = galeria.find('.gallery-show').css(strHeight, height - galeria.find('.gallery-thumbnails')[0].offsetHeight);
            galleryShow.css('width', inner[0].offsetWidth + 'px');

            if (ajustaShowImage)
                instance.ajustaShowImage(galleryShow.find('img')[0]);

            //instance.recreateNextPrevious();

        });
    }
    instance.ajustaShowImage = function(img) {
        var div_image = img.parentElement;
        div_image.style.padding = ''
        div_image.style.paddingTop = '';

        img.style.width = 'auto';
        img.style.height = 'auto';

        if (div_image.offsetHeight > div_image.offsetWidth) {
            if (div_image.parentElement.offsetWidth != div_image.parentElement.parentElement.offsetWidth) {
                div_image.style.paddingTop = (div_image.offsetHeight - img.height) / 2 + 'px';
            }
            else {
                img.style.height = '50px';
            }
        } else {
            if (div_image.parentElement.offsetWidth != div_image.parentElement.parentElement.offsetWidth) {
                div_image.style.padding = div_image.offsetHeight * 0.04 + 'px';
                div_image.style.paddingTop = (div_image.offsetHeight - img.height) / 2 + 'px';
            }
            else {

            }
        }
    }
    instance.updateEventTouch = function(_show) {
        var show = _show[0];


        show.addEventListener('touchstart', function(e) {
            instance.touchStartX = e.touches[0].clientX;
            instance.touchStartTime = e.timeStamp;
        });
        show.addEventListener('touchend', function(e) {
            var _this = this;
            var x = instance.touchLastX;
            var taxa = (x - instance.touchStartX) / this.offsetWidth * 100;
            var it = x >= instance.touchStartX ? this.previousElementSibling : this.nextElementSibling;

            var base = e.timeStamp - instance.touchStartTime < 500 ? 7 : 30;

            if (it && it.classList.contains('gallery-show') && (taxa > base || taxa < -base)) {

                $(this).animate({
                    'left':  (x - instance.touchStartX) > 0 ? '100%': '-100%'
                },200);

                $(it).animate({
                    'left':  0
                },200, function() {
                    $(_this).off('touchstart').off('touchend').off('touchmove');
                    $(_this).removeClass('active');
                    $(it).addClass('active');
                    //instance.recreateNextPrevious($(next[0].data));
                    $(it.data).trigger('click');
                });
            }
            else {
                if (it && it.classList.contains('gallery-show')) {
                    $(it).animate({
                        'left':  (x - instance.touchStartX) > 0 ? '-100%': '100%'
                    },200);
                }

                $(this).animate({
                    'left':  0
                },200, function() {
                    //instance.recreateNextPrevious(_this.data);
                });
            }
        });
        show.addEventListener('touchmove', function(e) {
            var x = e.touches[0].clientX;
            instance.touchLastX = x;
            var it = x >= instance.touchStartX ? this.previousElementSibling : this.nextElementSibling;
            var taxa = (x - instance.touchStartX) / this.offsetWidth * 100;
            if ((taxa > 3 && taxa <= 100) || (taxa < -3 && taxa >= -100)) {
                this.style.left = taxa + '%';
                if (it && it.classList.contains('gallery-show'))
                    it.style.left = (x >= instance.touchStartX ? -(100 - taxa) : 100 + taxa) + '%';
            }
            else {
                this.style.left = 0;
            }
        });
    }
    instance.recreateNextPrevious = function(item_selecionado) {
        instance.galerias.each(function(idx_galeria, _galeria) {
            var galeria = $(_galeria);

            var view = galeria.find('.gallery-show.active');

            var shows = galeria.find('.gallery-show');
            shows.clearQueue();
            view.clearQueue();
            shows.stop();
            view.stop();

            if (item_selecionado === undefined) {
                shows.each(function(idx, _item) {
                    _item.style.height = view[0].style.height;
                    _item.style.width = view[0].style.width;
                });
                return;
            }

            var previous = [];
            var next = []
            var size = 4;
            var flag_pn = false;
            for (var i = 0; i < shows.length; i++) {
                if (shows[i] === view[0]) {
                    flag_pn = true;
                    continue;
                }

                (flag_pn ? next : previous).push(shows[i]);
            }

            if (item_selecionado.previousElementSibling)
                while (previous.length < size) {
                    vc = view[0].cloneNode(true);
                    vc.style.left = '100%';
                    vc.style.width = view[0].offsetWidth+'px';
                    vc.classList.remove('active');
                    previous.push(vc);
                    view[0].parentNode.insertBefore(vc, view[0]);
                }
            else
                for (var i = 0; i < previous.length; i++) {
                    previous[i].remove();
                }

            if (item_selecionado.nextElementSibling) {
                while (next.length < size) {
                    vc = view[0].cloneNode(true);
                    vc.style.left = '100%';
                    vc.style.width = view[0].offsetWidth+'px';
                    vc.classList.remove('active');
                    next.unshift(vc);
                    view[0].parentNode.insertBefore(vc, view[0].nextSibling);
                }
            }
            else
                for (var i = 0; i < next.length; i++) {
                    next[i].remove();
                }

            var left = -100;
            var p = item_selecionado.previousElementSibling;
            for (var i = previous.length-1; i > -1; i--) {
                if (!p || i > size - 1) {
                    previous[i].remove();
                    continue;
                }
                previous[i].style.left = left + '%';
                left -= 100;
                $(previous[i]).find('img')[0].src = $(p).find('img')[0].src;  //getAttribute('data-src');
                previous[i].data = p;

                if (p.children.length == 2) {
                    var texto = p.children[1];
                    var texto_clone = texto.cloneNode(true);
                    $(previous[i]).find('.show-texto').replaceWith(texto_clone);
                }

                p = p.previousElementSibling;
            }

            left = 100;
            var n = item_selecionado.nextElementSibling;
            for (var i = 0; i < next.length; i++) {
                if (!n || i > size - 1) {
                    next[i].remove();
                    continue;
                }
                next[i].style.left = left + '%';
                left += 100;
                $(next[i]).find('img')[0].src = $(n).find('img')[0].src;  //getAttribute('data-src');
                next[i].data = n;

                if (n.children.length == 2) {
                    var texto = n.children[1];
                    var texto_clone = texto.cloneNode(true);
                    $(next[i]).find('.show-texto').replaceWith(texto_clone);
                }

                n = n.nextElementSibling;
            }

            var preloads = next.concat(previous);
            var preloadImgs = function(i) {
                var progress = $(preloads[i]).find('.progress');
                if (i < preloads.length - 1)
                    setTimeout(function () {
                        var img = $(preloads[i]).find('img')[0];
                        progress.css('width', img.style.width);
                        progress.css('left', img.offsetLeft + 'px');
                        progress.css('top', img.offsetTop + img.offsetHeight - 2 + 'px');
                        progress.removeClass('hidden');
                    }, 100);

                if ($(preloads[i].data).find('img').length == 1)
                    $(preloads[i]).find('img').one("load", function() {
                        instance.ajustaShowImage(this);
                        progress.addClass('hidden');

                        if (i < preloads.length - 1)
                            preloadImgs(i + 1);

                    }).attr('src', $(preloads[i].data).find('img')[0].getAttribute('data-src'));
            }

            if (preloads.length > 0)
                preloadImgs(0);
        });
    }
    instance.addEventClick = function() {
        instance.galerias.each(function(idx_galeria, _galeria) {
            var galeria = $(_galeria);
            galeria.find('.gallery-item').click(function(event) {
                var _this = this;
                galeria.find('.gallery-item').removeClass('active');
                $(_this).addClass('active');
                var show_active = galeria.find('.gallery-show.active');

                if (show_active.length == 0)
                    show_active = $(galeria.find('.gallery-show')[0]).addClass('active').css('left', 0);

                instance.updateEventTouch(show_active);
                show_active[0].data = _this;

                if (_this.children.length == 2) {
                    var texto = _this.children[1];
                    var texto_clone = texto.cloneNode(true);
                    show_active.find('.show-texto').replaceWith(texto_clone);
                }
                $(_this.parentElement.parentElement).animate({
                    scrollLeft: _this.offsetLeft - show_active.width() / 2 + _this.offsetWidth / 2
                }, 300);

                var thumb = _this.children[0];

                var img = show_active.find('.show-image img')[0];
                var progress = show_active.find('.progress');

                var img_width = img.width;
                var img_height = img.height;

                if (!img.src.endsWith(thumb.getAttribute('data-src'))) {
                    setTimeout(function () {
                        img.src = thumb.src;
                        img.style.height = img_height + 'px';
                        img.style.width = (img_height * (thumb.width / thumb.height)) + 'px';
                        progress.css('width', img.style.width);
                        progress.css('left', img.offsetLeft + 'px');
                        progress.css('top', img.offsetTop + img.offsetHeight - 2 + 'px');
                        progress.removeClass('hidden');
                    }, 100);

                    setTimeout(function () {
                        $(img).one("load", function() {
                            progress.addClass('hidden');
                            instance.ajustaShowImage(img);
                            instance.recreateNextPrevious(_this);

                        }).attr('src', thumb.getAttribute('data-src'));
                    }, 200);
                }
                else {
                    progress.addClass('hidden');
                    instance.ajustaShowImage(img);
                    instance.recreateNextPrevious(_this);
                }
            });

            galeria.find('.gallery-item:first-child').trigger('click');

            galeria.find('.path-next a').click(function() {
                var view = galeria.find('.gallery-show.active');
                var next = view.next();

                if (!next.hasClass('gallery-show'))
                    return false;


                $(next[0].data.parentElement.parentElement).animate({
                    scrollLeft: next[0].data.offsetLeft - view.width() / 2 + next[0].data.offsetWidth / 2
                }, 300);

                view.animate({
                    'left':  view.width() * -1
                },300);

                next.animate({
                    'left':  0
                },400, function() {
                    view.removeClass('active');
                    next.addClass('active');
                    //instance.recreateNextPrevious($(next[0].data));
                    $(next[0].data).trigger('click');
                });
                return false;
            });

            galeria.find('.path-previous a').click(function() {
                var view = galeria.find('.gallery-show.active');
                var prev = view.prev();

                if (!prev.hasClass('gallery-show'))
                    return false;

                $(prev[0].data.parentElement.parentElement).animate({
                    scrollLeft: prev[0].data.offsetLeft - view.width() / 2 + prev[0].data.offsetWidth / 2
                }, 300);

                view.animate({
                    'left':  view.width()
                },300);

                prev.animate({
                    'left':  0
                },400, function() {
                    view.removeClass('active');
                    prev.addClass('active');
                    //instance.recreateNextPrevious($(prev[0].data));
                    $(prev[0].data).trigger('click');
                });
                return false;
            });
        });

    }

    instance.init = function() {
        instance.galerias = $('.container-gallery');
        instance.intervalThumb();

        instance.resize();
        window.onresize = instance.resize;

        instance.addEventClick();

    }
    instance.init();
}


function ContainerFirst() {
    var first = $('.container-first');
    if (first.height() > window.innerHeight * 2) {
        first.css('height', window.innerHeight * 0.6);
        var btn = first.find('.btn').click(function() {
            this.parentElement.remove();
            first.css('height', '');
            first.removeClass('container-first');
        });
        if (btn.length === 0) {
            first.css('height', '');
        }
    }
    else {
        first.removeClass('.container-first');
        first.css('height', '');
        first.find('.painel-corte').remove();
    }
}
