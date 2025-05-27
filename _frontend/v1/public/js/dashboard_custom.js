function plot_chart(ctx, url, filter) {
  if (!url) {
    url = $(ctx).attr("data-url");
  }

  var ctx_id = $(ctx).attr("id");
  var base_url = url.split("?")[0];

  $.ajax({
    type: "GET",
    url: url,
    data: filter,
    success: function (data) {
      var prev_link = $(`a.dash-nav.previous[data-chart-target="#${ctx_id}"]`);
      var next_link = $(`a.dash-nav.next[data-chart-target="#${ctx_id}"]`);
      if (data.type == "html") {
        $(ctx).html(data.html);
      } else {
        var old = Chart.getChart(ctx);
        if (old != undefined) {
          old.destroy();
        }
        new Chart(ctx, data);
      }
      if (data.previous_page) {
        prev_link.attr("href", `${base_url}?${data.previous_page}`);
        prev_link.parent().removeClass("disabled");
      } else {
        prev_link.removeAttr("href");
        prev_link.parent().addClass("disabled");
      }
      if (data.next_page) {
        next_link.attr("href", `${base_url}?${data.next_page}`);
        next_link.parent().removeClass("disabled");
      } else {
        next_link.removeAttr("href");
        next_link.parent().addClass("disabled");
      }
      if (data.querystr) {
        let qs_params = new URLSearchParams(data.querystr);
        $(`a.export-link[data-chart-target="#${ctx_id}"]`).each(function (e) {
          var export_link = $(this);
          var [path, querystr] = export_link.attr("href").split("?");
          var qs = new URLSearchParams(querystr);
          for (const [k, v] of qs_params.entries()) {
            qs.set(k, v);
          }
          export_link.attr("href", `${path}?${qs.toString()}`);
        });
      }
    },
  });
}

$(function () {
  $("form[role='chart-filter'] :input").on("change", function (e) {
    var form = $(this.form);
    var target = $(form.attr("data-chart-target"));
    var url = form.attr("action");
    var filter = form.serialize();
    plot_chart(target, url, filter);
  });

  $("a.dash-nav[data-chart-target]").on("click", function (e) {
    e.preventDefault();
    var nav_btn = $(this);
    var target = $(nav_btn.attr("data-chart-target"));
    var url = nav_btn.attr("href");
    plot_chart(target, url);
  });

  $("canvas[data-url],div[data-url]").each(function () {
    plot_chart(this);
  });
});
