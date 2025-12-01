#!/usr/bin/env python3
"""
Apply irregular evaluation dropdown changes to dean and coordinator profile templates.
This script reads faculty_profile_settings.html as the reference and applies similar changes.
"""

import re

def add_irregular_dropdown_option(content):
    """Add irregular evaluation option after peer evaluation option"""
    pattern = r'(<!-- Peer Evaluation Option -->.*?</a></li>\s*<li><hr class="dropdown-divider"></li>)\s*(<!-- Individual Sections -->)'
    
    irregular_option = '''
                                <!-- Irregular Student Evaluation Option -->
                                <li><a class="dropdown-item irregular-option" href="javascript:void(0);" data-section="irregular" style="background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-top: 2px solid #2196f3; font-weight: 600;">
                                    🎓 Irregular Student Evaluations 
                                    <span class="overall-badge" style="background: linear-gradient(135deg, #2196f3, #1976d2);">Irregular</span>
                                </a></li>
                                <li><hr class="dropdown-divider"></li>
                                '''
    
    replacement = r'\1' + irregular_option + r'\2'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def add_irregular_css(content):
    """Add CSS for irregular-option"""
    peer_css_pattern = r'(\.peer-option:hover \{[^}]+\})'
    
    irregular_css = '''

    .irregular-option {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-top: 2px solid #2196f3;
        font-weight: 600;
        color: #0d47a1 !important;
    }

    .irregular-option:hover {
        background: linear-gradient(135deg, #2196f3, #1976d2) !important;
        color: white !important;
    }'''
    
    return re.sub(peer_css_pattern, r'\1' + irregular_css, content)

def add_irregular_js_variable(content):
    """Add irregularScoresData JavaScript variable"""
    pattern = r'(let peerScoresData = \{\{ peer_scores_json\|safe \}\};)'
    replacement = r'\1\n    let irregularScoresData = {{ irregular_scores_json|safe }};'
    
    content = re.sub(pattern, replacement, content)
    
    # Add console.log
    pattern2 = r"(console\.log\('Peer Scores Data:', peerScoresData\);)"
    replacement2 = r"\1\n    console.log('Irregular Scores Data:', irregularScoresData);"
    return re.sub(pattern2, replacement2, content)

def update_dropdown_button_text(content):
    """Update dropdown button text handler for irregular"""
    pattern = r"(} else if \(selectedSectionId === 'peer'\) \{[^}]+\})"
    
    irregular_handler = '''
                    } else if (selectedSectionId === 'irregular') {
                        document.getElementById('sectionDropdown').innerHTML = 
                            `🎓 Irregular Student Evaluations <i class="fas fa-chevron-down"></i>`;'''
    
    return re.sub(pattern, r'\1' + irregular_handler, content)

def update_load_section_data(content):
    """Update loadSectionData to handle irregular"""
    # Update the check
    pattern1 = r"if \(Object\.keys\(sectionScoresData\)\.length === 0 && sectionId !== 'peer'\)"
    replacement1 = "if (Object.keys(sectionScoresData).length === 0 && sectionId !== 'peer' && sectionId !== 'irregular')"
    content = re.sub(pattern1, replacement1, content)
    
    # Add irregular case after peer
    pattern2 = r"(if \(sectionId === 'peer'\) \{[^}]+document\.getElementById\('overallStats'\)\.style\.display = 'none';[\s\n]+\})"
    
    irregular_case = '''
        } else if (sectionId === 'irregular') {
            // Load irregular student evaluation data
            sectionData = irregularScoresData;
            console.log("Irregular student evaluation data:", sectionData);
            
            // Hide overall stats for irregular evaluations
            document.getElementById('overallStats').style.display = 'none';'''
    
    return re.sub(pattern2, r'\1' + irregular_case, content)

def update_section_name_mapping(content):
    """Update section name mapping"""
    pattern = r"(const sectionName = sectionId === 'overall' \? 'Overall' : \s+sectionId === 'peer' \? 'Peer Evaluation' :)"
    replacement = r"const sectionName = sectionId === 'overall' ? 'Overall' : \n                               sectionId === 'peer' ? 'Peer Evaluation' :\n                               sectionId === 'irregular' ? 'Irregular Student Evaluations' :"
    return re.sub(pattern, replacement, content)

def update_evaluation_content(content):
    """Update loadEvaluationContent for irregular"""
    # Add isIrregular flag
    pattern1 = r"(const isOverall = sectionCode === 'Overall';\s+const isPeer = sectionCode === 'Peer Evaluation';)"
    replacement1 = r"\1\n        const isIrregular = sectionCode === 'Irregular Student Evaluations';"
    content = re.sub(pattern1, replacement1, content)
    
    # Update sectionInfo
    pattern2 = r"(const sectionInfo = isPeer \? 'Peer Evaluations from Staff' :[\s\n]+isOverall \? 'All Sections' :)"
    replacement2 = r"const sectionInfo = isPeer ? 'Peer Evaluations from Staff' :\n                           isIrregular ? 'Irregular Student Evaluations' :\n                           isOverall ? 'All Sections' :"
    content = re.sub(pattern2, replacement2, content)
    
    # Update display conditions
    content = re.sub(r'\$\{!isPeer \?', '${!isPeer && !isIrregular ?', content)
    
    return content

def update_chart_init(content):
    """Update chart initialization"""
    # Add isIrregular parameter
    pattern1 = r"initializeEvaluationChart\(sectionData, isOverall, isPeer\)"
    replacement1 = "initializeEvaluationChart(sectionData, isOverall, isPeer, isIrregular)"
    content = re.sub(pattern1, replacement1, content)
    
    # Update function signature
    pattern2 = r"function initializeEvaluationChart\(sectionData, isOverall = false, isPeer = false\)"
    replacement2 = "function initializeEvaluationChart(sectionData, isOverall = false, isPeer = false, isIrregular = false)"
    content = re.sub(pattern2, replacement2, content)
    
    # Update labels
    pattern3 = r"(const labels = isPeer[\s\n]+\? \['Peer: Subject Mastery'[^\]]+\])"
    irregular_labels = ''': isIrregular
            ? ['Irregular: Subject Mastery', 'Irregular: Classroom Mgmt', 'Irregular: Compliance', 'Irregular: Personality']'''
    content = re.sub(pattern3, r"const labels = isIrregular\n            ? ['Irregular: Subject Mastery', 'Irregular: Classroom Mgmt', 'Irregular: Compliance', 'Irregular: Personality']\n            \1", content)
    
    return content

def update_recommendations(content):
    """Update recommendations loading"""
    # Add isIrregular flag
    pattern1 = r"(const isOverall = sectionCode === 'Overall';\s+const isPeer = sectionCode === 'Peer Evaluation';)"
    replacement1 = r"\1\n        const isIrregular = sectionCode === 'Irregular Student Evaluations';"
    content = re.sub(pattern1, replacement1, content)
    
    # Update evaluation_type
    pattern2 = r"evaluation_type: isPeer \? 'peer' : 'student'"
    replacement2 = "evaluation_type: isIrregular ? 'irregular' : isPeer ? 'peer' : 'student'"
    content = re.sub(pattern2, replacement2, content)
    
    return content

def update_switch_tab(content):
    """Update switchTab function"""
    pattern1 = r"(if \(selectedSectionId === 'peer'\) \{[\s\n]+sectionData = peerScoresData;)"
    
    irregular_case = '''} else if (selectedSectionId === 'irregular') {
            sectionData = irregularScoresData;'''
    
    content = re.sub(pattern1, r'\1' + irregular_case, content)
    
    # Update section name mapping
    pattern2 = r"(const sectionName = selectedSectionId === 'peer' \? 'Peer Evaluation' :)"
    replacement2 = r"const sectionName = selectedSectionId === 'irregular' ? 'Irregular Student Evaluations' :\n                           selectedSectionId === 'peer' ? 'Peer Evaluation' :"
    return re.sub(pattern2, replacement2, content)

def process_file(filepath):
    """Apply all changes to a template file"""
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply all transformations
    content = add_irregular_dropdown_option(content)
    content = add_irregular_css(content)
    content = add_irregular_js_variable(content)
    content = update_dropdown_button_text(content)
    content = update_load_section_data(content)
    content = update_section_name_mapping(content)
    content = update_evaluation_content(content)
    content = update_chart_init(content)
    content = update_recommendations(content)
    content = update_switch_tab(content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Completed {filepath}")

if __name__ == '__main__':
    templates = [
        r'c:\Users\ADMIN\eval\evaluation\main\templates\main\dean_profile_settings.html',
        r'c:\Users\ADMIN\eval\evaluation\main\templates\main\coordinator_profile_settings.html'
    ]
    
    for template in templates:
        try:
            process_file(template)
        except Exception as e:
            print(f"Error processing {template}: {e}")
    
    print("\nAll templates updated!")
