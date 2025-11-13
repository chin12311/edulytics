"""
Signals for the main app
Handles auto-creation of UserProfile when User is created
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Role
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a UserProfile when a User is created.
    
    This ensures that:
    1. Every User has a corresponding UserProfile (no orphaned users)
    2. Allows the registration form to populate role and all required fields
    3. Prevents database integrity errors from incomplete student profiles
    
    IMPORTANT: This signal should NOT raise exceptions! If it fails, we just log it
    and let the registration form handle the error. The transaction.atomic() in the
    view will rollback everything if form.save() fails.
    
    WHY ADMIN AS DEFAULT:
    - Students require studentnumber + course (CheckConstraint)
    - We can't pre-fill these without form input
    - ADMIN role has no field requirements, so it won't violate constraints
    - The registration form will immediately update the profile with correct role/fields
    - This is temporary - it lasts only milliseconds before the form updates it
    """
    if created:
        # Only create profile on actual User creation, not on updates
        try:
            # Check if profile already exists (safety check)
            if not hasattr(instance, 'userprofile'):
                profile = UserProfile(
                    user=instance,
                    role=Role.ADMIN,  # Temporary - won't trigger constraints
                    display_name=instance.get_full_name() or instance.username
                    # Don't set studentnumber/course - will be set by form
                )
                # Save without validation since this is temporary
                profile.save(skip_validation=True)
                logger.info(f"Auto-created UserProfile for user: {instance.username}")
        except Exception as e:
            # Log the error but don't raise it - let the view handle transaction rollback
            logger.error(f"Failed to auto-create UserProfile for {instance.username}: {str(e)}", exc_info=True)
