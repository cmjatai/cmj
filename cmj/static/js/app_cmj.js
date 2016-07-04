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
                var input_position = input.context.getBoundingClientRect();
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
                                $("input[name='bairro']").val(retrivie_data.bairro_descricao);
                                $("input[name='cep']").val(retrivie_data.cep[0]);
                                $("select[name='distrito']").val(retrivie_data.distrito_id);
                                $("select[name='regiao_municipal']").val(retrivie_data.regiao_municipal_id);
                                $("select[name='municipio']").val(retrivie_data.municipio_id);
                                $("select[name='uf']").val(retrivie_data.uf);

                            });
                        });

                        its[0].data =  item_data.pk;

                        if (data.results.length == 1)
                            its.trigger('click', true)
                        else {
                            input.attr('data', '');
                        }


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


/*function SetCookie(cookieName,cookieValue,nDays) {
    var today = new Date();
    var expire = new Date();
    if (nDays==null || nDays==0) nDays=1;
    expire.setTime(today.getTime() + 3600000*24*nDays);
    document.cookie = cookieName+"="+escape(cookieValue)
    + ";expires="+expire.toGMTString();
}

function ReadCookie(cookieName) {
    var theCookie=" "+document.cookie;
    var ind=theCookie.indexOf(" "+cookieName+"=");
    if (ind==-1) ind=theCookie.indexOf(";"+cookieName+"=");
    if (ind==-1 || cookieName=="") return "";
    var ind1=theCookie.indexOf(";",ind+1);
    if (ind1==-1) ind1=theCookie.length;
    return unescape(theCookie.substring(ind+cookieName.length+2,ind1));
}

function initTinymce(elements) {
    removeTinymce();
    var config_tinymce = {
        force_br_newlines : false,
        force_p_newlines : false,
        forced_root_block : '',
        plugins: ["table save code"],
        menubar: "edit format table tools",
        toolbar: "undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",
        tools: "inserttable",
        border_css: "/static/styles/style_tinymce.css",
        content_css: "/static/styles/style_tinymce.css",
    }
    if (elements != null) {
        config_tinymce['elements'] = elements;
        config_tinymce['mode'] = "exact";
        }
    else
        config_tinymce['mode'] = "textareas";

    tinymce.init(config_tinymce);
}

function removeTinymce() {
    while (tinymce.editors.length > 0) {
        tinymce.remove(tinymce.editors[0]);
    }
}

function refreshDatePicker() {
    $.datepicker.setDefaults($.datepicker.regional['pt-BR']);
    $('.dateinput').datepicker();
}

function refreshMask() {
    $('.telefone').mask("(99) 9999-9999", {placeholder:"(__) ____ -____"});
    $('.cpf').mask("000.000.000-00", {placeholder:"___.___.___-__"});
    $('.cep').mask("00000-000", {placeholder:"_____-___"});
    $('.rg').mask("0.000.000", {placeholder:"_.___.___"});
    $('.titulo_eleitor').mask("0000.0000.0000.0000", {placeholder:"____.____.____.____"});
    $('.dateinput').mask('00/00/0000', {placeholder:"__/__/____"});
    $('.hora').mask("00:00", {placeholder:"hh:mm"});
    $('.hora_hms').mask("00:00:00", {placeholder:"hh:mm:ss"});
}


$(document).ready(function(){
});
*/
