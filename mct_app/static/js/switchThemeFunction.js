window.onload = function() {
    var selectedTheme = localStorage.getItem('selectedTheme');
    var darkMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    var element = document.body;
  
    if (selectedTheme) {
      element.dataset.bsTheme = selectedTheme;
      if (selectedTheme === 'dark') {
        document.getElementById('flexSwitchCheckChecked').checked = true;
      } else {
        document.getElementById('flexSwitchCheckChecked').checked = false;
      }
    } else {
      if (darkMediaQuery.matches) {
        element.dataset.bsTheme = 'dark';
        localStorage.setItem('selectedTheme', 'dark');
        document.getElementById('flexSwitchCheckChecked').checked = true;
      } else {
        element.dataset.bsTheme = 'light';
        localStorage.setItem('selectedTheme', 'light');
        document.getElementById('flexSwitchCheckChecked').checked = false;
      }
    }
  }
  

  function switchThemeFunction() {
    var element = document.body;
    var currentTheme = element.dataset.bsTheme == "light" ? "dark" : "light";
    element.dataset.bsTheme = currentTheme;
    localStorage.setItem('selectedTheme', currentTheme);
}