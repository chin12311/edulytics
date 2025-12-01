// Profile Settings JavaScript - Version 2.0
console.log('PROFILE SETTINGS JS VERSION 2.0 LOADED');

// Global variables to store section data
let sectionScoresData, sectionMapData, peerScoresData, irregularScoresData;
let selectedSectionId = null;
let selectedSectionCode = null;
let selectedSectionDisplay = null;
let currentlySelectedItem = null;
let currentRequestId = 0;

// Helper function to format numbers to 2 decimal places
function formatToTwoDecimals(number) {
    if (number === null || number === undefined || isNaN(number)) {
        return '0.00';
    }
    return parseFloat(number).toFixed(2);
}

// Initialize on page load
function initializeProfileSettings(sectionScores, sectionMap, peerScores, irregularScores) {
    sectionScoresData = sectionScores;
    sectionMapData = sectionMap;
    peerScoresData = peerScores;
    irregularScoresData = irregularScores;
    
    console.log('Section Scores Data:', sectionScoresData);
    console.log('Section Map Data:', sectionMapData);
    console.log('Peer Scores Data:', peerScoresData);
    console.log('Irregular Scores Data:', irregularScoresData);
    
    setupSectionSelection();
}

// Section selection functionality
function setupSectionSelection() {
    const sectionItems = document.querySelectorAll('.section-item, .overall-option, .peer-option, .irregular-option');
    console.log('Found section items:', sectionItems.length);
    
    if (sectionItems.length === 0) {
        console.log('No sections available');
        return;
    }
    
    sectionItems.forEach(item => {
        item.addEventListener('click', function(e) {
            console.log('CLICK EVENT TRIGGERED on:', this);
            e.preventDefault();
            e.stopPropagation();
            
            // Remove active class from previously selected item
            if (currentlySelectedItem) {
                currentlySelectedItem.classList.remove('active');
            }
            
            // Add active class to clicked item
            this.classList.add('active');
            currentlySelectedItem = this;
            
            // Get section info
            selectedSectionId = this.getAttribute('data-section');
            selectedSectionCode = this.getAttribute('data-section-code');
            selectedSectionDisplay = this.getAttribute('data-section-display') || 
                                    (selectedSectionId === 'overall' ? 'Overall Results' : 
                                     selectedSectionId === 'peer' ? 'Peer Evaluation Results' :
                                     selectedSectionId === 'irregular' ? 'Irregular Student Evaluations' : '');
            
            console.log('Selected:', selectedSectionId, selectedSectionCode, selectedSectionDisplay);
            
            // Update dropdown button text
            const dropdownBtn = document.getElementById('sectionDropdown');
            if (selectedSectionId === 'overall') {
                dropdownBtn.innerHTML = `📈 Overall Results <i class="fas fa-chevron-down"></i>`;
            } else if (selectedSectionId === 'peer') {
                dropdownBtn.innerHTML = `👥 Peer Evaluation Results <i class="fas fa-chevron-down"></i>`;
            } else if (selectedSectionId === 'irregular') {
                dropdownBtn.innerHTML = `🎓 Irregular Student Evaluations <i class="fas fa-chevron-down"></i>`;
            } else {
                dropdownBtn.innerHTML = `📊 ${selectedSectionDisplay} <i class="fas fa-chevron-down"></i>`;
            }
            
            // Close the dropdown
            const dropdown = bootstrap.Dropdown.getInstance(dropdownBtn);
            if (dropdown) {
                dropdown.hide();
            }
            
            // Hide section prompt and show tabs
            document.getElementById('section-prompt').classList.add('hidden-content');
            document.getElementById('tabs-navigation').classList.remove('hidden-content');
            document.getElementById('evaluation-tab').classList.remove('hidden-content');
            document.getElementById('recommendations-tab').classList.remove('hidden-content');
            
            // Load content for the selected section
            loadSectionData(selectedSectionId);
            
            // Switch to evaluation tab by default
            switchTab('evaluation');
        });
    });
    
    // Auto-select overall option first if available
    const overallOption = document.querySelector('.overall-option');
    if (overallOption) {
        overallOption.click();
    } else if (sectionItems.length > 0) {
        sectionItems[0].click();
    }
}

// Load section data
function loadSectionData(sectionId) {
    console.log('Loading data for section:', sectionId);
    
    let sectionData;
    
    if (sectionId === 'peer') {
        sectionData = peerScoresData;
    } else if (sectionId === 'irregular') {
        sectionData = irregularScoresData;
    } else if (sectionId === 'overall') {
        sectionData = calculateOverallResults();
    } else {
        const sectionCode = sectionMapData[sectionId];
        sectionData = sectionScoresData[sectionCode];
    }
    
    console.log('Section data:', sectionData);
    
    if (sectionData && sectionData.has_data) {
        alert('Data loaded successfully! Total: ' + sectionData.total_percentage + '%');
    } else {
        alert('No data available for this section');
    }
}

// Calculate overall results
function calculateOverallResults() {
    // Placeholder - implement actual calculation
    return {
        has_data: true,
        total_percentage: 85.5,
        category_scores: [30, 25, 15, 15.5],
        evaluation_count: 10
    };
}

// Tab switching
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked tab
    event.target.classList.add('active');
}

// Export for template use
window.initializeProfileSettings = initializeProfileSettings;
window.switchTab = switchTab;

console.log('Profile settings script loaded successfully');
