// Progressive enhancement only: show the setting group used by the selected analysis,
// give a real "running" acknowledgement, and bring post-run feedback into view.
// No physics, no computation, no fetching - all values come from the Flask form POST.
(function () {
  var form = document.getElementById('sim-form');
  if (!form) return;

  var radios = form.querySelectorAll('input[name="analysis"]');
  var button = document.getElementById('run-button');
  var pending = document.getElementById('run-pending');
  var status = document.getElementById('mobile-status');
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

  function restore() {
    if (button) {
      button.disabled = false;
      button.textContent = button.getAttribute('data-run-label') || 'Run ngspice';
    }
    if (pending) pending.textContent = '';
    try {
      if (sessionStorage.getItem('simulateSubmitted') === '1') {
        sessionStorage.removeItem('simulateSubmitted');
        if (status) {
          status.setAttribute('tabindex', '-1');
          status.focus({ preventScroll: true });
          if (window.matchMedia && window.matchMedia('(max-width: 760px)').matches) {
            status.scrollIntoView({ block: 'start' });
          }
        }
      }
    } catch (e) {
      // sessionStorage can be blocked; the server-rendered status is still visible.
    }
  }

  form.addEventListener('submit', function () {
    if (button) {
      button.disabled = true;
      button.textContent = 'Running ngspice…';
    }
    if (pending) pending.textContent = 'ngspice กำลังรัน analysis ที่เลือก…';
    try { sessionStorage.setItem('simulateSubmitted', '1'); } catch (e) {}
  });

  radios.forEach(function (radio) {
    radio.addEventListener('change', update);
  });
  update();
  window.addEventListener('pageshow', restore);
  restore();
})();
