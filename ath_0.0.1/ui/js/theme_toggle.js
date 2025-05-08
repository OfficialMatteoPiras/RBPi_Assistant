// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('themeToggle');
    
    // Function to set theme
    function setTheme(themeName) {
        localStorage.setItem('theme', themeName);
        document.documentElement.setAttribute('data-theme', themeName);
        updateToggleIcon(themeName);
    }
    
    // Function to update the toggle button icon
    function updateToggleIcon(themeName) {
        themeToggleBtn.textContent = themeName === 'dark' ? '☀️' : '🌙';
    }
    
    // Function to toggle between themes
    function toggleTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }
    
    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (prefersDark) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
    
    // Add click event to toggle button
    themeToggleBtn.addEventListener('click', toggleTheme);
});
