// Progressive enhancement only: show the setting group used by the selected analysis.
// No physics, no computation, no fetching - all values come from the Flask form POST.
(function () {
  var form = document.getElementById('sim-form');
  if (!form) return;

  var radios = form.querySelectorAll('input[name="analysis"]');
  var groups = {
    ac: document.getElementById('ac-settings'),
    transient: document.getElementById('tran-settings')
  };

  function update() {
    var checked = form.querySelector('input[name="analysis"]:checked');
    var selected = checked ? checked.value : 'dc';
    Object.keys(groups).forEach(function (key) {
      var group = groups[key];
      if (!group) return;
      var active = key === selected;
      group.hidden = !active;
      group.classList.toggle('setting-active', active);
    });
  }

  radios.forEach(function (radio) {
    radio.addEventListener('change', update);
  });
  update();
})();
