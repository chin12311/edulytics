// ============================================================================
// SHARED AI RECOMMENDATIONS LOADER
// Extracted from coordinator_profile_settings.html and faculty_profile_settings.html
// This module handles all AI recommendation loading, display, and formatting logic
// ============================================================================

// Track current request ID for race condition prevention
let currentRequestId = 0;

/**
 * Load AI recommendations for a given section
 * @param {Object} sectionData - The evaluation data for the section
 * @param {string} sectionCode - The section code or 'Overall' or 'Peer Evaluation'
 */
function loadRecommendationsContent(sectionData, sectionCode) {
    const recommendationsContent = document.getElementById('recommendations-content');
    const currentRequest = ++currentRequestId; // Track this request
    
    console.log(`📡 Loading AI recommendations for ${sectionCode}, Request ID: ${currentRequest}`);
    
    const isOverall = sectionCode === 'Overall';
    const isPeer = sectionCode === 'Peer Evaluation';
    const sectionRef = isOverall ? 'all your sections' : isPeer ? 'peer evaluation' : 'section ' + sectionCode;
    
    // Different loading messages based on evaluation type
    const loadingMessage = isPeer 
        ? `🤖 Generating AI-powered professional development strategies for ${sectionCode}...`
        : `🤖 Generating AI-powered teaching strategies for ${sectionCode}...`;
    const loadingSubtext = isPeer
        ? 'Analyzing peer evaluation data to provide personalized professional development recommendations'
        : 'Analyzing evaluation data to provide personalized recommendations';
    
    // Show loading state with section context
    recommendationsContent.innerHTML = `
        <div class="text-center" style="padding: 40px;">
            <div class="spinner-border text-success" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">${loadingMessage}</p>
            <small class="text-muted">${loadingSubtext}</small>
        </div>
    `;
    
    // Prepare section data for API
    const apiSectionData = {
        has_data: sectionData.has_data,
        total_percentage: sectionData.total_percentage,
        evaluation_count: sectionData.evaluation_count || sectionData.total_evaluations,
        category_scores: sectionData.category_scores,
        total_responses: sectionData.evaluation_count || sectionData.total_evaluations,
        positive_comments: sectionData.positive_comments || [],
        negative_comments: sectionData.negative_comments || [],
        mixed_comments: sectionData.mixed_comments || []
    };
    
    console.log(`🚀 Sending AI request for ${sectionCode}:`, apiSectionData);
    
    // Fetch AI recommendations from shared API with cache prevention
    fetch('/api/ai-recommendations/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        },
        body: JSON.stringify({
            section_data: apiSectionData,
            section_code: sectionCode,
            is_overall: isOverall,
            evaluation_type: isPeer ? 'peer' : 'student', // ADD EVALUATION TYPE
            timestamp: Date.now() // Prevent caching
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(apiResponse => {
        // Check if this is still the current request (user didn't switch sections)
        if (currentRequest !== currentRequestId) {
            console.log('🔄 Request outdated, ignoring response');
            return;
        }
        
        console.log(`✅ AI Response for ${sectionCode}:`, apiResponse);
        
        // CORRECTED: Access the recommendations array from the response
        let recommendations = [];
        if (apiResponse.recommendations) {
            recommendations = apiResponse.recommendations;
            console.log(`🎯 Found ${recommendations.length} recommendations for ${sectionCode}`);
        } else if (Array.isArray(apiResponse)) {
            // Fallback: if response is directly the array
            recommendations = apiResponse;
        } else {
            throw new Error('Invalid response format from AI API');
        }
        
        displayRecommendations(recommendations, recommendationsContent, sectionCode);
    })
    .catch(error => {
        // Check if this is still the current request
        if (currentRequest !== currentRequestId) {
            console.log('🔄 Error in outdated request, ignoring');
            return;
        }
        
        console.error(`❌ Error loading recommendations for ${sectionCode}:`, error);
        recommendationsContent.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <strong>Unable to generate recommendations</strong>
                <p class="mb-0">Error: ${error.message}</p>
                <small class="text-muted">Please try again later or contact support.</small>
            </div>
        `;
    });
}

/**
 * Display formatted recommendations
 * @param {Array} recommendations - Array of recommendation objects
 * @param {HTMLElement} container - Container element to display recommendations
 * @param {string} sectionCode - Section code for context
 */
function displayRecommendations(recommendations, container, sectionCode) {
    console.log(`📊 Displaying ${recommendations.length} recommendations for ${sectionCode}`);
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>No recommendations available</strong>
                <p class="mb-0">Recommendations will be generated once evaluation data is available.</p>
            </div>
        `;
        return;
    }
    
    // Build HTML for recommendations
    let html = '<div class="recommendations-list">';
    
    recommendations.forEach((rec, index) => {
        const priority = rec.priority || 'normal';
        const priorityClass = priority === 'high' ? 'danger' : priority === 'low' ? 'info' : 'warning';
        
        html += `
            <div class="card mb-3 border-${priorityClass}">
                <div class="card-header bg-${priorityClass} text-white">
                    <strong>${rec.title || `Recommendation ${index + 1}`}</strong>
                    ${priority !== 'normal' ? `<span class="badge badge-light">${priority.toUpperCase()}</span>` : ''}
                </div>
                <div class="card-body">
                    <p class="card-text">${rec.description || rec.content || ''}</p>
                    ${rec.action_items ? `
                        <div class="action-items">
                            <strong>Action Items:</strong>
                            <ul class="mb-0">
                                ${rec.action_items.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${rec.estimated_impact ? `
                        <small class="text-muted">
                            <strong>Estimated Impact:</strong> ${rec.estimated_impact}
                        </small>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
