// Wacht tot het document geladen is
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard applicatie geladen');
    
    // Sidebar toggle functionaliteit
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            content.classList.toggle('active');
        });
    }
    
    // Voeg hover effect toe aan de app kaarten
    const appCards = document.querySelectorAll('.card');
    
    appCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
        });
    });
    
    // Voeg actieve status toe aan huidige pagina in sidebar
    const currentLocation = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar ul li a');
    
    sidebarLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        
        if (currentLocation === linkPath || 
            (linkPath !== '/' && currentLocation.startsWith(linkPath))) {
            link.parentElement.classList.add('active');
        }
    });
    
    // Initialiseer tooltips als Bootstrap is geladen
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Controleer schermgrootte bij laden en pas sidebar aan
    checkScreenSize();
    
    // Controleer schermgrootte bij resizen
    window.addEventListener('resize', checkScreenSize);
    
    function checkScreenSize() {
        if (window.innerWidth < 768) {
            sidebar.classList.add('active');
            content.classList.add('active');
        } else {
            sidebar.classList.remove('active');
            content.classList.remove('active');
        }
    }
}); 