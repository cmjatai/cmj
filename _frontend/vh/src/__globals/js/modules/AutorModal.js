window.autorModal = function () {
  $(function () {
    const dialog = $('#modal_autor').dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 340,
      show: {
        effect: 'blind',
        duration: 500
      },
      hide: {
        effect: 'explode',
        duration: 500
      }
    })

    $('#button-id-limpar').click(function () {
      $('#nome_autor').text('')

      function clean_if_exists (fieldname) {
        if ($(fieldname).length > 0) {
          $(fieldname).val('').trigger('change')
        }
      }

      clean_if_exists('#id_autor')
      clean_if_exists('#id_autoria__autor')
      clean_if_exists('#id_autorianorma__autor')
    })

    $('#button-id-pesquisar').click(function () {
      $('#q').val('')
      $('#div-resultado')
        .children()
        .remove()
      $('#modal_autor').dialog('open')
      $('#selecionar').attr('hidden', 'hidden')
    })

    $('#pesquisar').click(function () {
      const json_data = {
        q: $('#q').val()
        // get_all: true
      }
      $.get('/api/base/autor/', json_data, function (data) {
        $('#div-resultado')
          .children()
          .remove()
        if (data.pagination.total_entries === 0) {
          $('#selecionar').attr('hidden', 'hidden')
          $('#div-resultado').html(
            "<span class='alert'><strong>Nenhum resultado</strong></span>"
          )
          return
        }

        const select = $(
          '<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>'
        )

        data.results.forEach(function (item) {
          select.append(
            $('<option>')
              .attr('value', item.id)
              .text(item.nome)
          )
        })

        $('#div-resultado')
          .append('<br/>')
          .append(select)
        $('#selecionar').removeAttr('hidden', 'hidden')

        if (data.pagination.total_pages > 1) {
          $('#div-resultado').prepend(
            '<span>Mostrando 10 primeiros autores relativos a sua busca.</span>'
          )
        }

        $('#selecionar').click(function () {
          const res = $('#resultados option:selected')
          const id = res.val()
          const nome = res.text()

          $('#nome_autor').text(nome)

          // MateriaLegislativa pesquisa Autor via a tabela Autoria
          if ($('#id_autoria__autor').length) {
            $('#id_autoria__autor').val(id).trigger('change')
          }
          // Protocolo pesquisa a própria tabela de Autor
          if ($('#id_autor').length) {
            $('#id_autor').val(id)
          }
          // MateriaLegislativa pesquisa Autor via a tabela AutoriaNorma
          if ($('#id_autorianorma__autor').length) {
            $('#id_autorianorma__autor').val(id)
          }

          dialog.dialog('close')
        })
      })
    })

    const id_autoria__autor__initial = $('#id_autoria__autor').val()

    if (![null, undefined, ''].includes(id_autoria__autor__initial)) {
      $.get(`/api/base/autor/${id_autoria__autor__initial}/`, function (data) {
        $('#nome_autor').text(data.nome)
      })
    }
  })

  /* function get_nome_autor(fieldname) {
    if ($(fieldname).length > 0) { // se campo existir
      if ($(fieldname).val() != "") { // e não for vazio
        var id = $(fieldname).val();
        $.get("/proposicao/get-nome-autor?id=" + id, function(data, status){
            $("#nome_autor").text(data.nome);
        });
      }
    }
  }

  get_nome_autor("#id_autor");
  get_nome_autor("#id_autoria__autor"); */
}
