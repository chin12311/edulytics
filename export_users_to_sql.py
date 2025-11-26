"""
Export user data as SQL INSERT statements for AWS
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Section, SectionAssignment

# Open SQL file for writing
with open('aws_import.sql', 'w', encoding='utf-8') as f:
    f.write("-- Data export for AWS MySQL\n")
    f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
    
    # Export auth_user
    print("Exporting users...")
    users = User.objects.all()
    for u in users:
        password = u.password.replace("'", "''")
        username = u.username.replace("'", "''")
        first_name = u.first_name.replace("'", "''") if u.first_name else ''
        last_name = u.last_name.replace("'", "''") if u.last_name else ''
        email = u.email.replace("'", "''") if u.email else ''
        last_login = f"'{u.last_login.strftime('%Y-%m-%d %H:%M:%S')}'" if u.last_login else 'NULL'
        date_joined = f"'{u.date_joined.strftime('%Y-%m-%d %H:%M:%S')}'"
        
        f.write(f"INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES ({u.id}, '{password}', {last_login}, {int(u.is_superuser)}, '{username}', '{first_name}', '{last_name}', '{email}', {int(u.is_staff)}, {int(u.is_active)}, {date_joined});\n")
    
    print(f"Exported {users.count()} users")
    
    # Export user profiles
    print("Exporting profiles...")
    profiles = UserProfile.objects.all()
    for p in profiles:
        display_name = p.display_name.replace("'", "''") if p.display_name else ''
        studentnumber = p.studentnumber.replace("'", "''") if p.studentnumber else ''
        course = p.course.replace("'", "''") if p.course else ''
        institute = p.institute.replace("'", "''") if p.institute else ''
        section_id = p.section_id if p.section_id else 'NULL'
        last_failure = f"'{p.last_evaluation_failure_date.strftime('%Y-%m-%d %H:%M:%S')}'" if p.last_evaluation_failure_date else 'NULL'
        
        f.write(f"INSERT INTO main_userprofile (id, user_id, display_name, role, studentnumber, course, section_id, institute, evaluation_failure_count, last_evaluation_failure_date, failure_alert_sent) VALUES ({p.id}, {p.user_id}, '{display_name}', '{p.role}', '{studentnumber}', '{course}', {section_id}, '{institute}', {p.evaluation_failure_count}, {last_failure}, {int(p.failure_alert_sent)});\n")
    
    print(f"Exported {profiles.count()} profiles")
    
    # Export sections
    print("Exporting sections...")
    sections = Section.objects.all()
    for s in sections:
        code = s.code.replace("'", "''")
        f.write(f"INSERT INTO main_section (id, code, year_level) VALUES ({s.id}, '{code}', {s.year_level});\n")
    
    print(f"Exported {sections.count()} sections")
    
    # Export section assignments
    print("Exporting section assignments...")
    assignments = SectionAssignment.objects.all()
    for a in assignments:
        role = a.role.replace("'", "''") if a.role else 'NULL'
        f.write(f"INSERT INTO main_sectionassignment (id, user_id, section_id, role) VALUES ({a.id}, {a.user_id}, {a.section_id}, '{role}');\n")
    
    print(f"Exported {assignments.count()} assignments")
    
    f.write("\nSET FOREIGN_KEY_CHECKS=1;\n")

print("\n✅ Export complete! File: aws_import.sql")
print("Upload and run this file on AWS.")
